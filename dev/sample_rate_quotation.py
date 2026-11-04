"""A [PRUEBA] rate quotation on boss20 to look at the rate table in the PDF and the portal (phase A, 04/11/2026): the
IMB FOB template, its per-container services for 20' DV and 40' HC, invented prices typed on the lines. Kept (not
rolled back) so that it can be opened in the browser; a second run reuses it.
    dev/server_shell.sh sample_rate_quotation.py"""
from odoo import Command
from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
Order = env["sale.order"]  # noqa: F821
name = "[PRUEBA] Oferta de tarifas SEA FCL"
order = Order.search([("client_order_ref", "=", name)], limit=1)
if not order:
    customer = env["res.partner"].search([("name", "=", "[PRUEBA] Cliente tarifas (muestra)")], limit=1) or \
        env["res.partner"].create({"name": "[PRUEBA] Cliente tarifas (muestra)", "is_company": True, "lang": "es_ES",  # noqa: F821
                                   "country_id": env.ref("base.es").id})  # noqa: F821
    with Form(Order) as form:
        form.partner_id = customer
        form.sale_order_template_id = env["sale.order.template"].search([("name", "=like", "IMB FOB · %")], limit=1)  # noqa: F821
        form.client_order_ref = name
    order = form.save()
    dv, hc = env.ref("boss_pricing.container_type_dv"), env.ref("boss_pricing.container_type_hc")  # noqa: F821
    order.boss_rate_quotation = True
    per_container = order.order_line.filtered(lambda l: order._boss_per_container(l.product_id, l.product_uom_id))
    per_container.write({"boss_container_size": "20", "boss_container_type_id": dv.id})
    order.write({"order_line": [Command.create({"product_id": l.product_id.id, "product_uom_id": l.product_uom_id.id,
                                                "boss_container_size": "40", "boss_container_type_id": hc.id,
                                                "sequence": l.sequence}) for l in per_container]})
    # invented prices (never boss20 tariffs): 100 per service, +50 % for a 40' HC
    for line in order.order_line.filtered(lambda l: not l.display_type):
        line.price_unit = 150.0 if line.boss_container_size == "40" else 100.0
print("ORDER", order.id, order.name, "lines", len(order.order_line), "columns",
      [c["label"] for c in order._boss_rate_matrix()["columns"]])
env.cr.commit()  # noqa: F821
