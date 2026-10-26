"""Quotation templates (standard sale_management) with the BOSS services that always apply per case, on boss20 or
the local copy (odoo shell). Approved by Belal on 26/10/2026 (task TP02). Idempotent by template name.

Lists: air import FOB from the real Cofitel offer 05570 (03/02/2026); the other two are proposals until Cristina
confirms the always/sometimes services per case (task TP03). Optional services (ALM, inspections, SEG, CAU, QBR,
extras) are added on the quotation with «Add services». Also one [DEMO] draft quotation from the air template so the
pricing of the lines can be seen (nothing is sent or confirmed)."""
from datetime import date

from odoo import Command

assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, mail_create_nosubscribe=True))  # noqa: F821
P, Template = env["product.product"], env["sale.order.template"]
TEMPLATES = {
    "Importación aérea FOB · servicios estándar (lista de la oferta Cofitel 02/2026; Cristina confirma)":
        ["FAI", "HAN", "AWB", "CSA", "FAD", "ETX", "TTE-CON"],
    "Importación marítima FCL · servicios estándar (propuesta 26/10; Cristina confirma)":
        ["FMI", "THC", "BL", "GLO-CCC", "FAD", "CSM", "TTE-FCL"],
    "Exportación aérea · servicios estándar (propuesta 26/10; Cristina confirma)":
        ["TTE-CON", "HAN", "AWB", "DEX", "CSA", "FAE"],
}
NOTE = ("Plantilla de servicios que aplican SIEMPRE en este caso. Los servicios que aplican A VECES (almacenaje ALM, "
        "inspecciones, seguro, caución, quebranto, extras) se añaden en la oferta con «Añadir servicios». Lista "
        "pendiente de confirmación por Cristina (tarea BOSS20-TP03).")
made = {}
for name, codes in TEMPLATES.items():
    products = [P.search([("default_code", "=", c)], limit=1) for c in codes]
    assert all(products), [c for c, p in zip(codes, products) if not p]
    template = Template.search([("name", "=", name)], limit=1)
    if not template:
        template = Template.create({"name": name, "note": NOTE, "sale_order_template_line_ids": [
            Command.create({"product_id": p.id, "product_uom_qty": 1, "product_uom_id": p.uom_id.id,
                            "sequence": i * 10}) for i, p in enumerate(products, start=1)]})
    made[name] = template
    print("TEMPLATE", template.id, name[:40], [l.product_id.default_code for l in template.sale_order_template_line_ids])

# [DEMO] draft quotation from the air import template (DEMO customer, DEMO tariffs); never sent or confirmed
customer = env["res.partner"].search([("name", "=", "[DEMO] Cliente UE Ejemplo GmbH")], limit=1)
air = made[next(n for n in TEMPLATES if n.startswith("Importación aérea"))]
origin = "[DEMO] Plantilla importación aérea FOB (26/10)"
order = env["sale.order"].search([("origin", "=", origin)], limit=1)
if customer and not order:
    mad = env["boss.port"].search([("code", "=", "MAD")], limit=1)
    order = env["sale.order"].create({
        "partner_id": customer.id, "origin": origin, "sale_order_template_id": air.id, "boss_direction": "import",
        "boss_transport_mode": "air", "boss_load_type": "air", "boss_port_id": mad.id,
        "boss_country_id": env.ref("base.cn").id, "boss_planned_date": date(2026, 11, 4), "boss_awb_kg": 500.0})
    order._onchange_sale_order_template_id()
if order:
    print("QUOTE", order.name, order.state, "| lines", len(order.order_line))
    for l in order.order_line:
        print("   ", l.product_id.default_code, "| qty", l.product_uom_qty, l.product_uom_id.name, "| exec",
              l.boss_execution, "| cost", l.boss_cost_status, l.boss_cost_amount, "| supplier",
              l.boss_supplier_id.name or "-", "| sale", l.boss_sale_status)
env.cr.commit()
