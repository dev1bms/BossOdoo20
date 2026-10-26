"""Local copy only (boss_test): does a standard quotation template (sale_management) fill a BOSS quotation with the
standard services of an air import FOB (Cofitel case) so that BOSS prices them? Rolled back at the end."""
from odoo import Command

assert env.cr.dbname == "boss_test", env.cr.dbname  # noqa: F821
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES", tracking_disable=True))  # noqa: F821
P = env["product.product"]
codes = ["FAI", "HAN", "AWB", "CSA", "FAD", "ETX", "TTE-CON"]
products = {c: P.search([("default_code", "=", c)], limit=1) for c in codes}
print("PRODUCTS", {c: (bool(p), p.boss_pricing_mode if p else None, p.uom_id.name if p else None) for c, p in products.items()})
Template = env["sale.order.template"]
print("TEMPLATE MODEL", Template._name, "| line fields", [f for f in env["sale.order.template.line"]._fields
                                                           if f.startswith("boss_") or f in ("product_id", "product_uom_qty", "product_uom_id")])
tpl = Template.create({"name": "[DEMO] Importación aérea FOB (Cofitel)", "sale_order_template_line_ids": [
    Command.create({"product_id": p.id, "product_uom_qty": 1, "product_uom_id": p.uom_id.id}) for p in products.values() if p]})
customer = env["res.partner"].create({"name": "CLIENTE PLANTILLA (FICTICIO)", "country_id": env.ref("base.de").id, "vat": "DE100000008", "boss_is_customer": True})
mad = env["boss.port"].search([("code", "=", "MAD")], limit=1)
order = env["sale.order"].create({
    "partner_id": customer.id, "sale_order_template_id": tpl.id, "boss_direction": "import", "boss_transport_mode": "air",
    "boss_load_type": "air", "boss_port_id": mad.id, "boss_country_id": env.ref("base.cn").id,
    "boss_planned_date": __import__("datetime").date(2026, 11, 10), "boss_awb_kg": 500.0})
order._onchange_sale_order_template_id()  # what the form does when the template is chosen
print("ORDER", order.name, "template", order.sale_order_template_id.name, "| lines", len(order.order_line))
for l in order.order_line:
    print("  ", l.product_id.default_code, "| uom", l.product_uom_id.name, "| exec", l.boss_execution,
          "| cost", l.boss_cost_status, l.boss_cost_amount, "| supplier", l.boss_supplier_id.name or "-",
          "| sale", l.boss_sale_status, l.price_unit, "| vat", l.boss_vat_status)
# supplier chosen on a line -> cost appears (Cristina: lines empty, then choose the supplier)
han = order.order_line.filtered(lambda l: l.product_id.default_code == "HAN")
wfs = env["res.partner"].search([("name", "=like", "WFS %")], limit=1) or env["res.partner"].create({"name": "HANDLER (FICTICIO)", "boss_is_supplier": True})
han.boss_supplier_id = wfs
print("HAN with WFS:", han.boss_cost_status, han.boss_cost_amount)
env.cr.rollback()
print("ROLLED BACK")
