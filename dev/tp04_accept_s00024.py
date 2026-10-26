"""TP04 on boss20 (approved by Belal 26/10/2026: boss20 is the testing server): accept the [DEMO] quotation «Caso Cofitel
— Importación aérea» (S00024), check the file gets every service once, then recompute with actual data.
[DEMO] customer and [DEMO]/illustrative amounts only; nothing is posted, sent or confirmed to a supplier."""
from odoo.exceptions import UserError

assert env.cr.dbname in ("boss20", "boss_uat"), env.cr.dbname  # noqa: F821
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES", tracking_disable=True))  # noqa: F821
order = env["sale.order"].search([("origin", "=", "[DEMO] Caso Cofitel — Importación aérea")], limit=1)
assert order and order.partner_id.boss_demo, "DEMO quotation with a DEMO customer only"
print("ORDER", order.name, order.state, order.partner_id.name)


def show(label):
    print(label)
    for l in order.order_line:
        print("   ", l.product_id.default_code, "| qty", l.product_uom_qty, l.product_uom_id.name, "| cost",
              l.boss_cost_status, l.boss_cost_amount, l.boss_cost_kind, "| sale", l.boss_sale_status, l.price_unit,
              "| vat", l.boss_vat_status, l.tax_ids.mapped("name"))


if order.state == "draft":
    show("BEFORE")
    try:  # what Cristina would see pressing «Confirm» as it is
        with env.cr.savepoint():
            order.action_confirm()
        print("CONFIRM AS IS: accepted")
    except UserError as exc:
        print("CONFIRM AS IS: blocked «%s»" % " ".join(str(exc).split())[:400])
    # shipment data and [DEMO] illustrative amounts, as a salesperson would complete them
    order.write({"boss_gross_kg": 500.0, "boss_volume_m3": 2.0})
    lines = {l.product_id.default_code: l for l in order.order_line}
    lines["FAI"].write({"boss_manual_cost": 2.5, "boss_manual_cost_note": "[DEMO] Oferta de flete ilustrativa"})
    for code, price in (("FAI", 3.0), ("CSA", 40.0), ("FAD", 90.0), ("ETX", 40.0), ("TTE-CON", 0.25)):
        if lines[code].boss_sale_status == "missing":
            lines[code].price_unit = price
    for code in ("FAD", "ETX", "TTE-CON"):
        if lines[code].boss_cost_kind == "unknown":
            lines[code].boss_unknown_cost_reason = "[DEMO] Tarifa del proveedor pendiente (D01/TP03); prueba TP04"
    show("COMPLETED")
    order.action_confirm()
    print("CONFIRMED", order.name, order.state)

file = order.boss_expediente_id
print("FILE", file.name, "| analytic", file.analytic_account_id.name)
sold = {l.product_id.default_code for l in order.order_line}
parts = file.allocation_ids.mapped("product_id.default_code")
needs = file.cost_ids.mapped("product_id.default_code")
print("SOLD", sorted(sold))
print("PARTS", sorted(parts), "| missing", sorted(sold - set(parts)), "| duplicated",
      sorted({c for c in parts if parts.count(c) > 1}))
print("NEEDS", [(n.product_id.default_code, n.state, n.expected_unit_cost, n.quantity) for n in file.cost_ids])
print("NEEDS duplicated", sorted({c for c in needs if needs.count(c) > 1}))
print("FIGURES sale", file.amount_sale, "| cost at acceptance", file.amount_cost_accepted, "| forecast",
      file.amount_cost_forecast, "| margin at acceptance", file.amount_margin_accepted)
if not file.revision_ids:
    han = file.cost_ids.filtered(lambda n: n.product_id.default_code == "HAN")
    before = (han.quantity, han.expected_unit_cost)
    file.awb_kg = 620.0
    file.with_context(boss_reason="[DEMO] AWB definitiva 620 kg (prueba TP04)").action_recompute_costs()
    han.invalidate_recordset()
    print("RECOMPUTE HAN", before, "->", (han.quantity, han.expected_unit_cost), "| revisions", len(file.revision_ids),
          "| sale unchanged", file.amount_sale)
env.cr.commit()
