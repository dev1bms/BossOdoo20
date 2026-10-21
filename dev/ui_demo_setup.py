"""Local, throw-away demo data for the UI walkthrough and the guide screenshots (odoo shell, isolated DB).

FICTITIOUS supplier, customer and prices only (the published guide is public). Never run on the server:
the taxes created here stand in for Ángel's VAT mapping, which is still to be decided.
Usage (inside the test container): odoo shell -d boss_test < dev/ui_demo_setup.py
"""
import base64
from datetime import date, timedelta

from odoo import Command

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname == "boss_test", "local test database only"
ref = env.ref
admin = ref("base.user_admin")
admin.write({"lang": "es_ES", "tz": "Europe/Madrid", "group_ids": [Command.link(ref(x).id) for x in (
    "boss_pricing.group_tariff_approver", "sales_team.group_sale_manager", "uom.group_uom")]})
eur = ref("base.EUR")
eur.active = True
company = env.company
company.write({"name": "BOSS Continental (prueba local)", "currency_id": eur.id, "country_id": ref("base.es").id})
Tax = env["account.tax"]
taxes = {k: Tax.create({"name": name, "amount": rate, "type_tax_use": "sale", "company_id": company.id})
         for k, name, rate in (("nr", "IVA 21% (prueba)", 21.0), ("ex", "Exento (prueba)", 0.0),
                               ("ns", "No sujeto (prueba)", 0.0))}
company.write({f"boss_tax_{k}_id": tax.id for k, tax in taxes.items()})

Partner = env["res.partner"]
customer = Partner.create({"name": "Cliente Ejemplo, S.L.", "is_company": True, "country_id": ref("base.es").id,
                           "state_id": ref("base.state_es_v").id, "city": "Valencia"})
doc = base64.b64encode(b"%PDF-1.4 documento de ejemplo").decode()
demo = {"tariffs": [{
    "key": "demo_naviera_ejemplo_import", "name": "Naviera Ejemplo - gastos locales importación 2026 (EJEMPLO)",
    "supplier": "Naviera Ejemplo, S.A.", "carrier": True, "currency": "EUR", "valid_from": "2026-01-01",
    "document_b64": doc, "document_path": "naviera-ejemplo-2026.pdf", "document_reference": "Tarifa de ejemplo 2026",
    "scope": {"direction": "import", "transport_mode": "sea", "load_type": "fcl"},
    "lines": [
        {"service": "THC", "uom": "container", "basis": "containers", "unit_price": 200, "page": "3"},
        {"service": "T3-PAD", "uom": "container", "container_size": "20", "basis": "containers", "unit_price": 30, "page": "3"},
        {"service": "T3-PAD", "uom": "container", "container_size": "40", "basis": "containers", "unit_price": 45, "page": "3"},
        {"service": "BL", "uom": "shipment", "basis": "line", "unit_price": 70, "page": "3"},
        {"service": "DEM", "uom": "container", "method": "time", "basis": "containers", "free_days": 7,
         "tier_mode": "relative", "brackets": [{"up_to": 5, "unit_price": 30}, {"up_to": 0, "unit_price": 80}],
         "page": "5"},
    ]}]}
tariff = env["boss.tariff"]._boss_import_tariffs(demo)
tariff.with_user(admin).action_approve()
team = ref("sales_team.team_sales_department", raise_if_not_found=False)
lead = env["crm.lead"].create({"name": "Importación 2x20' + 1x40'HC Shanghái - Valencia", "type": "opportunity",
                               "partner_id": customer.id, "user_id": admin.id, "team_id": team.id if team else False,
                               "expected_revenue": 1500, "date_deadline": date.today() + timedelta(days=7)})
env.cr.commit()
print("DEMO READY", tariff.ids, lead.id)
