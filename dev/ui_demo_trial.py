"""LOCAL copy only (boss_test): play the trial steps of the guide so the screenshots show the server setup.
Run after setup_company.py and server_trial.py. FICTITIOUS [DEMO] data; on the server a person does these steps."""
import base64
from datetime import date

from odoo import Command

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname == "boss_test", "local copy only"
ref = env.ref
admin = ref("base.user_admin")
admin.write({"lang": "es_ES", "tz": "Europe/Madrid", "group_ids": [Command.link(ref(x).id) for x in (
    "boss_pricing.group_tariff_approver", "sales_team.group_sale_manager")]})
admin.odoobot_state = "disabled"
env = env(user=admin)


def trial(name):
    imd = env["ir.model.data"].search([("module", "=", "boss_trial"), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id)


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


for name in ("tariff_sea", "tariff_road", "tariff_air"):
    if trial(name).state == "to_approve":
        trial(name).action_approve()
lead = trial("lead_sea")
sea = env["sale.order"].create({
    "partner_id": lead.partner_id.id, "opportunity_id": lead.id, "origin": lead.name, "boss_direction": "import",
    "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": trial("carrier").id,
    "boss_port_id": ref("boss_pricing.port_esvlc").id, "boss_country_id": ref("base.cn").id,
    "boss_planned_date": date(2026, 11, 4), "boss_storage_days": 12,
    "boss_container_ids": [
        Command.create({"size": "20", "container_type_id": ref("boss_pricing.container_type_dv").id, "quantity": 2}),
        Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id, "quantity": 1})]})
env["boss.add.services"].create({"order_id": sea.id, "product_ids": [Command.set(
    (product("THC") | product("DEM") | product("TTE-FCL") | product("FS") | product("CES")).ids)]}).action_add()
accepted = sea.copy({"origin": lead.name})
for ces in accepted.order_line.filtered(lambda l: l.product_id.default_code == "CES"):
    env["boss.supplier.price.wizard"].create({
        "sale_line_id": ces.id, "unit_price": 45.0, "document_page": "3",
        "document": base64.b64encode(b"%PDF-1.4 [DEMO]").decode(), "document_name": "demo-ces.pdf"}).action_save()
accepted.order_line.boss_cost_candidate_ids.tariff_id.filtered(lambda t: t.state == "to_approve").action_approve()
air_lead = trial("lead_air")
air = env["sale.order"].create({
    "partner_id": air_lead.partner_id.id, "opportunity_id": air_lead.id, "origin": air_lead.name,
    "boss_direction": "import", "boss_transport_mode": "air", "boss_load_type": "air",
    "boss_port_id": env["boss.port"].search([("code", "=", "MAD")], limit=1).id, "boss_country_id": ref("base.cn").id,
    "boss_planned_date": date(2026, 11, 4), "boss_awb_kg": 500, "boss_storage_days": 4})
env["boss.add.services"].create({"order_id": air.id, "product_ids": [Command.set(
    (product("ALM") | product("HAN")).ids)]}).action_add()
eu_lead = trial("lead_eu")
eu = env["sale.order"].create({
    "partner_id": eu_lead.partner_id.id, "opportunity_id": eu_lead.id, "origin": eu_lead.name,
    "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_carrier_id": trial("carrier").id, "boss_port_id": ref("boss_pricing.port_esvlc").id,
    "boss_country_id": ref("base.cn").id, "boss_planned_date": date(2026, 11, 4), "boss_storage_days": 10,
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id,
                                           "quantity": 1})]})
env["boss.add.services"].create({"order_id": eu.id, "product_ids": [Command.set(
    (product("THC") | product("DEM") | product("TTE-FCL") | product("FS")).ids)]}).action_add()
env.cr.commit()
print("IDS", {"eu": eu.id, "sea_draft": sea.id, "sea_priced": accepted.id, "air": air.id, "lead_sea": lead.id,
              "pricelist": trial("pricelist").id, "tariff_sea": trial("tariff_sea").id})
