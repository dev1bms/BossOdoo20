"""Check of roadmap item 12 (boss20, rolled back): ratings before the operational close (F0-C66) and the shipment data
frozen once operations are closed. The full cycle (rate, close, frozen vessel, averages) is in check_file_e2e; this
covers the setting, the form, the reopening and what stays open. Prints «CHECK PASS|FAIL …» and «RESULT …».
    dev/uat_run.sh check_file_close.py boss20"""
from datetime import date

from lxml import etree

from odoo.exceptions import UserError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


Partner, File = env["res.partner"], env["boss.expediente"]
customer = Partner.create({"name": "[PRUEBA] Cierre Cliente", "is_company": True, "country_id": ref("base.es").id,
                           "vat": "ESB12345674"})
file = File.create({"partner_id": customer.id, "business": "boss", "direction": "import", "transport_mode": "sea",
                    "load_type": "lcl", "vessel": "[PRUEBA] VESSEL", "eta": date(2026, 12, 1)})
file.write({"state": "delivered"})

# 1. the setting: on by default (as Odoo 17); off, operations close without ratings
check("1 ratings required to close operations by default (Odoo 17 since 01/03/2025)", True,
      env.company.boss_ratings_to_close)
result = file.action_close_operations()
check("2 the close lists the customer to rate and asks for it, the file stays delivered",
      ("display_notification", "delivered", [customer]),
      (result["tag"], file.state, list(file.rating_ids.partner_id)))
env.company.boss_ratings_to_close = False
file.action_close_operations()
check("3 with the setting off, operations close without ratings", "closed", file.state)

# 2. frozen: form and server; what stays open
arch = etree.fromstring(File.get_view(view_type="form")["arch"])
vessel = arch.xpath("//field[@name='vessel']")[0].get("readonly") or ""
customs = arch.xpath("//field[@name='customs_ref']")[0].get("readonly") or ""
check("4 the form makes the shipment data read-only on a closed file", (True, True),
      ("closed" in vessel, "closed" in customs))
try:
    with env.cr.savepoint():
        file.write({"goods_description": "[PRUEBA] otra mercancía"})
    got = "accepted"
except UserError as exc:
    got = "refused"
    print(f"      «{' '.join(str(exc).split())[:160]}»")
check("5 the server refuses a change of the shipment data on a closed file", "refused", got)
file.write({"user_id": env.uid})
file.rating_ids.write({"rating": "7", "note": "[PRUEBA]"})
check("6 the responsible and the ratings stay editable after the close", ("7", env.uid),
      (file.rating_ids.rating, file.user_id.id))
action = file.action_reopen()
reopen = env[action["res_model"]].create({"expediente_ids": [(6, 0, file.ids)],
                                          "reason": "[PRUEBA] corregir la descripción"})
reopen.action_confirm()
file.write({"goods_description": "[PRUEBA] corregida tras reabrir"})
check("7 reopened with a reason in the history, the shipment data can be corrected",
      ("open", True, "[PRUEBA] corregida tras reabrir"),
      (file.state, "corregir la descripción" in (file.message_ids[:1].body or "")
       or any("corregir la descripción" in (m.body or "") for m in file.message_ids), file.goods_description))
check("8 the customer's average rating is on its contact", (7.0, 1), (customer.boss_rating_avg, customer.boss_rating_count))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
