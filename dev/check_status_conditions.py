"""Check of the settings, phase 3 (boss20, rolled back): each status condition of a file has a level in Settings ›
BOSS · Files (required, warning only, not checked), today's behaviour by default. Fictitious records only.
    dev/uat_run.sh check_status_conditions.py boss20"""
from datetime import datetime

from odoo.exceptions import UserError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []
company = env.company


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def outcome(fn):
    try:
        with env.cr.savepoint():
            fn()
        return "accepted"
    except UserError as exc:
        print(f"      «{' '.join(str(exc).split())[:150]}»")
        return "refused"


customer = env["res.partner"].create({"name": "[PRUEBA] Condiciones Cliente", "is_company": True})


def new_file():
    return env["boss.expediente"].create({"partner_id": customer.id, "business": "boss", "direction": "import",
                                          "transport_mode": "sea", "load_type": "lcl", "scope_delivery": True})


check("1 defaults = today: leaving warns, delivering and closing are required",
      ("warn", "warn", "warn", "warn", "block", "block", "block", "block", "block", "block", "block", "block"),
      tuple(company[f] for f in ("boss_cond_transit_atd", "boss_cond_transit_booking", "boss_cond_transit_master",
                                 "boss_cond_transit_containers", "boss_cond_delivered_ata",
                                 "boss_cond_delivered_discharge", "boss_cond_delivered_release",
                                 "boss_cond_delivered_pickup", "boss_cond_delivered_delivery", "boss_cond_delivered_hbl",
                                 "boss_cond_close_invoiced", "boss_cond_close_margin")))
f1 = new_file()
check("2 by default a file leaves without ATD, with the warning in its history", ("accepted", True),
      (outcome(f1.action_in_transit), "without" in (f1.message_ids[:1].body or "")))
company.boss_cond_transit_atd = "block"
f2 = new_file()
check("3 ATD set to «required»: the file cannot leave without it", "refused", outcome(f2.action_in_transit))
company.boss_cond_transit_atd = "warn"
f3 = new_file()
f3.write({"state": "arrived", "ata": datetime(2026, 12, 1, 8, 0)})
check("4 by default «Delivered» needs the discharge, the delivery date and the B/L released", "refused",
      outcome(f3.action_delivered))
company.boss_cond_delivered_discharge = company.boss_cond_delivered_delivery = "off"
company.boss_cond_delivered_hbl = "warn"
check("5 discharge and delivery date not checked, B/L a warning: delivered, with the warning in the history",
      ("accepted", True), (outcome(f3.action_delivered), "house B/L" in (f3.message_ids[:1].body or "")))
check("6 the next step no longer lists what is not checked", False, "vessel discharge" in (
    ", ".join(f3._boss_delivery_missing())))
company.boss_cond_delivered_discharge = company.boss_cond_delivered_delivery = company.boss_cond_delivered_hbl = "block"

f4 = new_file()
f4.write({"state": "delivered"})
company.boss_ratings_to_close = False
File = type(f4)
original = File._boss_margin_warnings
File._boss_margin_warnings = lambda self: ["[PRUEBA] Flete: margen bajo"]  # this transaction only, restored below
try:
    check("7 a low margin without a reason stops the close by default", "refused", outcome(f4.action_close_operations))
    company.boss_cond_close_margin = "warn"
    check("8 set to «warning only»: the file closes, the warning stays in its history", ("accepted", True),
          (outcome(f4.action_close_operations), "margen bajo" in (f4.message_ids[:1].body or "")))
    f5 = new_file()
    f5.write({"state": "delivered"})
    company.boss_cond_close_margin = "off"
    check("9 set to «not checked»: the file closes, nothing written", ("accepted", False),
          (outcome(f5.action_close_operations), "margen bajo" in (f5.message_ids[:1].body or "")))
finally:
    File._boss_margin_warnings = original

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
