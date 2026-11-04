"""Check of the settings, phase 1 (boss20, rolled back): the values that left the code are read from the company and
change the behaviour when changed in Settings; the three BOSS tabs exist. Fictitious figures only.
    dev/uat_run.sh check_settings.py boss20"""
from datetime import date, timedelta

from odoo import Command
from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []
company = env.company


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


# 0. the tabs
arch = env["res.config.settings"].get_view(view_type="form")["arch"]
check("0 Settings has the three BOSS tabs and the Sales tab no longer holds BOSS settings",
      (True, True, True, False), ('name="boss_pricing_sale"' in arch, 'name="boss_expediente"' in arch,
                                  'name="boss_documents"' in arch, "boss_vat_mapping" in arch.split('name="boss_pricing_sale"')[0]))
check("1 the defaults equal the former code values", (30, 7, 10.0, 10.0, 167, 333, 1000, 7, "chargeable", 3, True),
      (company.boss_tariff_expiring_days, company.boss_spot_rate_validity_days, company.boss_margin_default_rate,
       company.boss_margin_tolerance, company.boss_volumetric_air, company.boss_volumetric_road,
       company.boss_volumetric_sea, company.boss_close_days_after_delivery, company.boss_default_allocation_basis,
       company.boss_hbl_originals, company.boss_invoice_operation_date))

# 2. volumetric factor: a quotation's chargeable weight follows the setting
customer = env["res.partner"].create({"name": "[PRUEBA] Ajustes Cliente", "is_company": True})
order = env["sale.order"].create({"partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "air",
                                  "boss_load_type": "air", "boss_gross_kg": 100.0, "boss_volume_m3": 1.0})
check("2 air chargeable weight with the default factor 167", 167.0, order.boss_chargeable_kg)
company.boss_volumetric_air = 200
order.invalidate_recordset(["boss_chargeable_kg", "boss_volume_weight_kg"])
check("3 ... follows the setting (200)", 200.0, order.boss_chargeable_kg)
company.boss_volumetric_air = 167

# 4. margin default and tolerance
Policy = env["boss.margin.policy"]
fad = env["product.product"].search([("default_code", "=", "FAD")], limit=1)
ctx = Policy._boss_context(order, [], 0.0)
money = lambda a: f"{a:.2f}"  # noqa: E731
rows = Policy._boss_check({fad: (105.0, 100.0)}, ctx, money)
check("4 a service without a rule: 10 % minimum, within the tolerance", (10.0, False), (rows[0][3], bool(rows[0][4])))
company.boss_margin_default_rate, company.boss_margin_tolerance = 20.0, 2.0
rows = Policy._boss_check({fad: (105.0, 100.0)}, ctx, money)
check("5 ... 20 % and 2 of tolerance from Settings: warned", (20.0, True), (rows[0][3], bool(rows[0][4])))
company.boss_margin_default_rate, company.boss_margin_tolerance = 10.0, 10.0

# 6. tariff expiring days
supplier = env["res.partner"].create({"name": "[PRUEBA] Ajustes Proveedor", "is_company": True, "supplier_rank": 1})
tariff = env["boss.tariff"].create({
    "name": "[PRUEBA] Ajustes tarifa", "partner_id": supplier.id, "valid_from": date.today(),
    "valid_to": date.today() + timedelta(days=20),
    "line_ids": [Command.create({"product_id": fad.id, "uom_id": fad.uom_id.id, "unit_price": 1.0})]})
tariff._workflow_write({"state": "approved"})  # the check's own [PRUEBA] tariff, approved without the buttons
line = tariff.line_ids[:1]
check("6 a price valid 20 more days is «expiring» with the default 30", "expiring", line.validity_state)
company.boss_tariff_expiring_days = 10
line.invalidate_recordset(["validity_state"])
check("7 ... and «current» when the setting is 10 days", "current", line.validity_state)
company.boss_tariff_expiring_days = 30

# 8. close days and allocation default
file = env["boss.expediente"].create({"partner_id": customer.id, "business": "boss", "direction": "import",
                                      "transport_mode": "sea", "load_type": "fcl"})
check("8 a new master proposes the split of Settings", "chargeable", file.allocation_basis)
company.boss_default_allocation_basis = "equal"
other = env["boss.expediente"].create({"partner_id": customer.id, "business": "boss", "direction": "import",
                                       "transport_mode": "sea", "load_type": "fcl"})
check("9 ... «equal parts» once the setting changes", "equal", other.allocation_basis)
company.boss_default_allocation_basis = "chargeable"
house = env["boss.expediente"].create({"partner_id": customer.id, "business": "boss", "direction": "import",
                                       "transport_mode": "sea", "load_type": "lcl", "master_id": file.id})  # a master's next step reaches the close
file.write({"state": "delivered", "delivered_date": date.today() - timedelta(days=5)})
company.boss_ratings_to_close = False
file.invalidate_recordset(["next_step_detail"])
check("10 delivered 5 days ago: no warning with 7 days to close", False, "asks to close" in (file.next_step_detail or ""))
company.boss_close_days_after_delivery = 3
file.invalidate_recordset(["next_step_detail"])
check("11 ... warns with 3 days in Settings", True, "within 3 days" in (file.next_step_detail or ""))
company.boss_close_days_after_delivery, company.boss_ratings_to_close = 7, True

# 12. house documents and invoice
company.boss_hbl_originals, company.boss_doc_issue_place = 2, "[PRUEBA] VALENCIA"
html = env["ir.actions.report"]._render_qweb_html("boss_documents.action_report_house_bl", house.ids)[0].decode()
check("12 the house B/L prints the originals and the place of issue of Settings", (True, True),
      ("2 / TWO" in html, "[PRUEBA] VALENCIA" in html))
company.boss_hbl_originals, company.boss_doc_issue_place = 3, False
company.boss_invoice_operation_date = False
income = env["account.account"].search([("account_type", "=", "income"), ("company_ids", "in", company.id)], limit=1)
file.ata = date.today()
invoice = env["account.move"].create({
    "move_type": "out_invoice", "partner_id": customer.id, "invoice_date": date.today(),
    "invoice_line_ids": [Command.create({"name": "[PRUEBA]", "quantity": 1, "price_unit": 10.0, "account_id": income.id,
                                         "boss_expediente_id": file.id})]})
check("13 operation date switched off: the invoice has none", False, bool(invoice.delivery_date))
company.boss_invoice_operation_date = True

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
