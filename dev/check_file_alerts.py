"""Check of roadmap item 14 (boss20, rolled back): container free-time alerts (F0-C55), month-close reminder (F0-A37)
and the operation date of the invoice (F0-A20). A [PRUEBA] sea import FCL with MSC in Valencia, its ATA known and the
empty container not returned, demurrage (DEM) to buy from MSC. Prints «CHECK PASS|FAIL …» and «RESULT …»; no amount.
    dev/uat_run.sh check_file_alerts.py boss20"""
from datetime import date, datetime, timedelta

from odoo import Command

from odoo.addons.boss_expediente.models.boss_expediente_alerts import minus_working_days

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


Partner, File = env["res.partner"], env["boss.expediente"]
port = lambda code: env["boss.port"].search([("code", "=", code), ("kind", "=", "sea")], limit=1)  # noqa: E731
msc = ref("o17_partner.res_partner_23762")
dem = env["product.product"].search([("default_code", "=", "DEM")], limit=1)
customer = Partner.create({"name": "[PRUEBA] Avisos Cliente", "is_company": True, "country_id": ref("base.es").id,
                           "vat": "ESB12345674"})
operator = env.user
file = File.create({
    "partner_id": customer.id, "business": "boss", "direction": "import", "transport_mode": "sea", "load_type": "fcl",
    "carrier_id": msc.id, "origin_country_id": ref("base.cn").id, "origin_port_id": port("CNSHA").id,
    "destination_country_id": ref("base.es").id, "destination_port_id": port("ESVLC").id, "user_id": operator.id,
    "eta": date(2026, 12, 1),
    "container_ids": [Command.create({"size": "40", "number": "PRUU7654321",
                                      "container_type_id": ref("boss_pricing.container_type_dv").id})]})
file.cost_ids = [Command.create({"kind": "extra", "product_id": dem.id, "uom_id": dem.uom_id.id, "partner_id": msc.id,
                                 "quantity": 1.0, "extra_class": "covered", "reason": "[PRUEBA] demora prevista"})]
file.action_in_transit()
file.ata = datetime(2026, 12, 1, 8, 0)
need = file.cost_ids.filtered(lambda n: n.product_id == dem)
container = file.container_ids
start = file.ata

# 1. last free day, from the MSC demurrage tariff
last_free = need._boss_last_free_day(container, start)
check("1 the last free day comes from the MSC tariff (after the arrival)", True, bool(last_free) and last_free > start.date())
print(f"      free days until {last_free} (arrival {start.date()})")
Alerts = File


def run(day):
    return Alerts._boss_cron_container_alerts(today=day)


first_day = minus_working_days(last_free, env.company.boss_free_alert_days)
check("2 nothing before the alert day", 0, run(first_day - timedelta(days=1)))
check("3 an activity for the operator 3 working days before the last free day", 1, run(first_day))
acts = file.activity_ids
check("... with the container and the last free day, assigned to the operator", (True, operator),
      ("PRUU7654321" in acts[-1:].summary and last_free.strftime("%d/%m/%Y") in acts[-1:].summary, acts[-1:].user_id))
check("4 not repeated the same day", 0, run(first_day))
check("5 another on the last free day", 1, run(last_free))
check("6 and one on the first day with a cost (to the salesperson, here the responsible)", 1,
      run(last_free + timedelta(days=1)))
check("7 nothing more afterwards", 0, run(last_free + timedelta(days=5)))
other = File.create({"partner_id": customer.id, "business": "boss", "direction": "import", "transport_mode": "sea",
                     "load_type": "fcl", "carrier_id": msc.id, "destination_port_id": port("ESVLC").id,
                     "user_id": operator.id, "container_ids": [Command.create({
                         "size": "40", "number": "PRUU7654322", "return_date": date(2026, 12, 3),
                         "container_type_id": ref("boss_pricing.container_type_dv").id})]})
other.cost_ids = [Command.create({"kind": "extra", "product_id": dem.id, "uom_id": dem.uom_id.id, "partner_id": msc.id,
                                  "quantity": 1.0, "extra_class": "covered", "reason": "[PRUEBA]"})]
other.write({"state": "arrived", "ata": datetime(2026, 12, 1, 8, 0)})
check("8 a container already returned gets no alert", 0, len(other._boss_container_alerts_due(last_free)))

# 2. month close (F0-A37)
file.write({"state": "delivered"})
angel = env["res.users"].browse(11)
env.company.boss_month_close_copy_user_id = angel
check("9 not on another day of the month", 0, File._boss_cron_month_close(today=date(2026, 12, 15)))
count = File._boss_cron_month_close(today=date(2026, 12, 31))
mine = file.activity_ids.filtered(lambda a: a.summary and a.summary.startswith("Month close 12/2026"))
check("10 on the last day: the delivered file not closed gets its activity for the responsible", (True, 1, operator),
      (count >= 1, len(mine), mine.user_id))
summary = env.company.partner_id.activity_ids.filtered(lambda a: a.summary and a.summary.startswith("Month close 12/2026"))
check("11 the person in copy gets one summary listing the file", (1, angel, True),
      (len(summary), summary.user_id, file.name in (summary.note or "")))
File._boss_cron_month_close(today=date(2026, 12, 31))
check("12 run twice, nothing is repeated", (1, 1), (len(file.activity_ids.filtered(
    lambda a: a.summary and a.summary.startswith("Month close 12/2026"))), len(env.company.partner_id.activity_ids.filtered(
        lambda a: a.summary and a.summary.startswith("Month close 12/2026")))))

# 3. operation date on the invoice (F0-A20)
income = env["account.account"].search([("account_type", "=", "income"), ("company_ids", "in", env.company.id)], limit=1)
invoice = env["account.move"].create({
    "move_type": "out_invoice", "partner_id": customer.id, "invoice_date": date(2026, 12, 20),
    "invoice_line_ids": [Command.create({"name": "[PRUEBA] servicio", "quantity": 1, "price_unit": 10.0,
                                         "account_id": income.id, "boss_expediente_id": file.id})]})
check("13 the invoice keeps its issue date and takes the operation date of the file (arrival of an import)",
      (date(2026, 12, 20), date(2026, 12, 1)), (invoice.invoice_date, invoice.delivery_date))
html = env["ir.actions.report"]._render_qweb_html("account.account_invoices", invoice.ids)[0].decode()
label = "Fecha de la operación" if (invoice.partner_id.lang or env.company.partner_id.lang or "").startswith("es")     else "Operation date"
check("14 the invoice prints the operation date in the customer's language", (True, label),
      (label in html, label))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
