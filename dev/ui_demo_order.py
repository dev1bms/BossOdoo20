"""Local demo quotation for the guide screenshots (odoo shell on boss_test only, after ui_demo_setup.py). FICTITIOUS data.

Same steps as the UI walkthrough (opportunity -> quotation -> shipment data -> add services -> add the missing supplier
price -> approve -> sale prices -> confirm), done through the ORM so the screenshots can be recreated.
"""
import base64
from datetime import date, timedelta

from odoo import Command

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname == "boss_test", "local test database only"
ref = env.ref
admin = ref("base.user_admin")
env = env(user=admin)
lead = env["crm.lead"].search([("name", "ilike", "Shanghái")], limit=1)
carrier = env["res.partner"].search([("name", "=", "Naviera Ejemplo, S.A.")], limit=1)
order = env["sale.order"].create({
    "partner_id": lead.partner_id.id, "opportunity_id": lead.id, "origin": lead.name,
    "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": carrier.id,
    "boss_port_id": ref("boss_pricing.port_esvlc").id, "boss_country_id": ref("base.cn").id,
    "boss_planned_date": date.today() + timedelta(days=12), "boss_storage_days": 10,
    "boss_container_ids": [Command.create({"size": "20", "container_type_id": ref("boss_pricing.container_type_dv").id, "quantity": 2}),
                           Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id, "quantity": 1})],
})
services = env["product.product"].search([("default_code", "in", ["THC", "T3-PAD", "BL", "DEM", "CES"])])
env["boss.add.services"].create({"order_id": order.id, "product_ids": [Command.set(services.ids)]}).action_add()
ces = order.order_line.filtered(lambda l: l.product_id.default_code == "CES")[:1]
wizard = env["boss.supplier.price.wizard"].create({
    "sale_line_id": ces.id, "unit_price": 40, "document_page": "4",  # supplier, scope and currency come from the quotation
    "document": base64.b64encode(b"%PDF-1.4 documento de ejemplo").decode(), "document_name": "naviera-ejemplo-ces.pdf",
})
wizard.action_save()
env["boss.tariff"].search([("state", "=", "to_approve")]).action_approve()
order.action_boss_update_costs()
sale = {"THC": 240, "T3-PAD": 0, "BL": 90, "DEM": 0, "CES": 50}
for line in order.order_line:
    code = line.product_id.default_code
    price = sale[code] or round((line.purchase_price or 0) * 1.2, 2)
    line.price_unit = price
order.action_confirm()
env.cr.commit()
print("ORDER", order.id, order.state, order.amount_untaxed, order.amount_tax, [
    (l.product_id.default_code, l.boss_container_size, l.product_uom_qty, l.boss_cost_status, l.purchase_price, l.price_unit)
    for l in order.order_line])
