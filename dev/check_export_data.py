"""Export data and customs-only files on boss20 (go-live tracker P4-08, Cristina F0-C36), inside a transaction rolled
back: cut-off dates with their alerts, booking and cargo-ready dates, the customs mode copied from the customer, and a
customs-only file that needs no booking, master document, arrival or discharge but does need the customs release.
    dev/uat_run.sh check_export_data.py boss20"""
from datetime import date, timedelta

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def outcome(fn):
    try:
        fn()
    except (UserError, ValidationError, AccessError) as e:
        print(f"      refused: {str(e)[:160]}")
        return "refused"
    return "allowed"


ref = env.ref
state_m = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "M")], limit=1)
customer = env["res.partner"].create({"name": "[PRUEBA] Exportador cut-offs", "is_company": True, "vat": "ESB12345674",
                                      "country_id": ref("base.es").id, "city": "Madrid", "state_id": state_m.id,
                                      "boss_customs_mode": "customer"})
check("0 the customer's customs mode is stored on the contact", "customer", customer.boss_customs_mode)
env.company.boss_cutoff_alert_days = 2
File = env["boss.expediente"]
ops = env["res.users"].create({"name": "[PRUEBA] Operativo cut-offs", "login": "prueba.cutoffs.ops",
                               "group_ids": [Command.set([ref("base.group_user").id, ref("sales_team.group_sale_salesman").id,
                                                          ref("purchase.group_purchase_user").id])]})
# --- export sea FCL file with its cut-offs ---
sailing = date(2026, 12, 18)
file = File.create({"partner_id": customer.id, "user_id": ops.id, "direction": "export", "transport_mode": "sea",
                    "load_type": "fcl", "scope_main": True, "scope_origin_customs": True, "etd": sailing,
                    "booking_ref": "[PRUEBA] BK-1", "vessel": "[PRUEBA] BUQUE", "booking_date": date(2026, 11, 20),
                    "cargo_ready_date": date(2026, 12, 10), "cutoff_docs": date(2026, 12, 11),
                    "cutoff_si": date(2026, 12, 14), "cutoff_vgm": date(2026, 12, 15), "cutoff": date(2026, 12, 16)})
check("1 the file keeps booking, cargo-ready and the four sea cut-offs",
      (date(2026, 11, 20), date(2026, 12, 10), date(2026, 12, 11), date(2026, 12, 14), date(2026, 12, 15), date(2026, 12, 16)),
      (file.booking_date, file.cargo_ready_date, file.cutoff_docs, file.cutoff_si, file.cutoff_vgm, file.cutoff))
check("1 a travelling file is not «customs only»", False, file.customs_only)
before = len(file.activity_ids)
n = File._boss_cron_cutoff_alerts(today=date(2026, 12, 9))  # Wednesday: 2 working days before the documents cut-off (Fri 11)
check("2 two working days before the documents cut-off: one activity to the operator", (1, before + 1, ops.id),
      (n, len(file.activity_ids), file.activity_ids.sorted("id")[-1].user_id.id))
check("2 the activity names the cut-off and its date", True, "Documents cut-off" in file.activity_ids.sorted("id")[-1].summary
      and "11/12/2026" in file.activity_ids.sorted("id")[-1].summary)
n2 = File._boss_cron_cutoff_alerts(today=date(2026, 12, 9))
check("2 the same day again gives nothing new", 0, n2)
n3 = File._boss_cron_cutoff_alerts(today=date(2026, 12, 11))
check("2 on the cut-off day: the «today» activity for the documents cut-off, and the first alert of SI (Mon 14 - 2 wd = Thu 10 < 11)",
      True, n3 >= 2)
file.write({"atd": date(2026, 12, 18)})
check("2 once departed, no more cut-off alerts", 0, File._boss_cron_cutoff_alerts(today=date(2026, 12, 16)))
# --- customs mode copied from the customer when a file opens from a quotation ---
order = env["sale.order"].create({"partner_id": customer.id})
check("3 the customs mode of the customer reaches the file values of its quotation", "customer",
      order._boss_file_values().get("customs_mode"))
# --- customs-only file (Odoo 17 traffic ITB): no travel, release required ---
only = File.create({"partner_id": customer.id, "direction": "import", "transport_mode": "sea", "load_type": "fcl",
                    "scope_destination_customs": True, "scope_main": False, "customs_mode": "boss"})
check("4 a file with only a customs scope is «customs only»", True, only.customs_only)
check("4 it needs nothing to be put in transit (no booking, master B/L, containers)", [], only._boss_transit_missing())
check("4 to be delivered it needs the customs release, not the arrival or the discharge", ["customs release (levante)"],
      only._boss_delivery_missing())
only.write({"customs_release_date": "2026-12-12 10:00:00"})
check("4 with the release it can be delivered", [], only._boss_delivery_missing())
own = File.create({"partner_id": customer.id, "direction": "import", "transport_mode": "sea", "load_type": "fcl",
                   "scope_destination_customs": True, "scope_delivery": True, "customs_mode": "customer"})
check("5 when the customer's own broker clears, the release is not required of BOSS (delivery date still is)",
      ["delivery date and time"], own._boss_delivery_missing())
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if not all(results):
    raise SystemExit(1)
