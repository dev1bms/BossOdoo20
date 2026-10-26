"""Local copy only (boss_test): try the standard sale -> invoice and purchase -> vendor bill steps on the [DEMO] data
inside ONE transaction that is rolled back at the end. Nothing stays; never run on boss20."""
from odoo import Command
from odoo.exceptions import UserError, ValidationError
assert env.cr.dbname == "boss_test", env.cr.dbname  # noqa: F821
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES"))  # noqa: F821
ref = env.ref
SO, P = env["sale.order"], env["product.product"]
def prod(code):
    return P.search([("default_code", "=", code)], limit=1)

def step(name, fn):
    try:
        with env.cr.savepoint():
            out = fn()
        print("OK  ", name, "|", out)
        return out
    except (UserError, ValidationError) as exc:
        print("STOP", name, "|", " ".join(str(exc).split())[:260])
        return None

# 1. Customer invoice from the accepted [DEMO] quotation
order = SO.search([("state", "=", "sale"), ("boss_pricing_frozen", "=", True)], limit=1)
def invoice_from_order():
    move = order._create_invoices()
    lines = [(l.product_id.default_code, l.quantity, l.price_unit, l.tax_ids.mapped("name"), l.account_id.code,
              l.sale_line_ids.ids) for l in move.invoice_line_ids]
    return (move.state, move.partner_id.name, move.journal_id.code, move.fiscal_position_id.name,
            move.amount_untaxed, move.amount_tax, lines, "order invoice_status:", order.invoice_status)
step("1 customer invoice (draft) from " + order.name, invoice_from_order)

# 2. A BOSS own service (no supplier) alone and with a purchased service
lead_partner = order.partner_id
def own_service_order():
    so = SO.create({"partner_id": lead_partner.id, "boss_direction": "import", "boss_transport_mode": "sea",
                    "boss_load_type": "fcl", "boss_planned_date": order.boss_planned_date,
                    "boss_port_id": ref("boss_pricing.port_esvlc").id, "boss_country_id": ref("base.cn").id,
                    "order_line": [Command.create({"product_id": prod("CSM").id})]})
    l = so.order_line
    first = (l.product_id.default_code, l.boss_pricing_mode, l.boss_cost_status, l.boss_cost_explanation,
             l.purchase_price, l.price_unit, l.boss_sale_status, l.boss_vat_class, l.boss_vat_status)
    blocked = None
    try:
        so.action_confirm()
    except UserError as exc:
        blocked = str(exc).splitlines()[0][:160]
    l.price_unit = 120.0  # BOSS fee typed by the salesperson
    try:
        so.action_confirm()
        confirmed = so.state
    except UserError as exc:
        confirmed = "blocked: " + " ".join(str(exc).split())[:300]
    return {"line": first, "confirm without price": blocked or "confirmed", "confirm with 120": confirmed,
            "margin": l.margin, "margin %": l.margin_percent, "purchase lines": l.purchase_line_count}
step("2 own service CSM", own_service_order)

# 3. Standard automatic RFQ (sale_purchase 'subcontract') on a purchased service
def auto_rfq():
    thc = prod("THC")
    thc.product_tmpl_id.service_tracking = "subcontract"
    so = order.copy()
    so.action_confirm()
    return so.purchase_order_count
step("3 THC as 'subcontract' -> RFQ on confirmation (no supplierinfo)", auto_rfq)

# 4. Manual purchase order -> vendor bill, and what links back to the sale
def manual_po():
    line = order.order_line.filtered(lambda l: l.product_id.default_code == "THC")[:1]
    po = env["purchase.order"].create({
        "partner_id": line.boss_supplier_id.id or line.boss_tariff_line_id.partner_id.id, "origin": order.name,
        "order_line": [Command.create({"product_id": line.product_id.id, "product_qty": line.product_uom_qty,
                                       "uom_id": line.product_uom_id.id, "price_unit": line.purchase_price})]})
    po.button_confirm()
    pol = po.order_line
    pol.qty_received = pol.product_qty  # services: received manually (receipt policy)
    action = po.action_create_invoice()
    bill = env["account.move"].browse(action.get("res_id")) if action.get("res_id") else po.invoice_ids
    bl = bill.invoice_line_ids[:1]
    return {"po": (po.name, po.state, po.partner_id.name, pol.product_qty, pol.uom_id.name, pol.price_unit,
                   po.currency_id.name, pol.tax_ids.mapped("name"), "sale_line_id", pol.sale_line_id.id),
            "bill": (bill.state, bill.move_type, bl.quantity, bl.price_unit, bl.account_id.code,
                     bl.tax_ids.mapped("name"), "purchase_line_id", bl.purchase_line_id.id == pol.id,
                     "analytic", bl.analytic_distribution),
            "sale line after": (line.boss_cost_amount, line.purchase_price, line.price_unit, line.purchase_line_count)}
step("4 manual PO -> vendor bill (draft)", manual_po)
print("SERVICE_TRACKING", sorted(set(env["product.template"].search([("boss_pricing_mode", "!=", False)]).mapped("service_tracking"))))
env.cr.rollback()
print("ROLLED BACK")
