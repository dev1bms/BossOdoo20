"""Phase 1 guards (tracker P1-20 and P1-21, audit of 05/11/2026), checked on boss20 inside a transaction rolled back.

P1-20 «Upload Bill» on a purchase order of a file: the BOSS override accepts the attachment the standard button passes
(a TypeError on boss20 the 04/11 before the fix).
P1-21 the status of a quotation changes only with its buttons: a direct write of «state» is refused for an
administrator and for a salesperson, while Send / Confirm / Set to quotation / Cancel still work.
    dev/uat_run.sh check_phase1_guards.py boss20"""
from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def refused(fn):
    try:
        fn()
    except (UserError, ValidationError, AccessError) as e:
        return type(e).__name__
    return "allowed"


ref = env.ref
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
state = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "M")], limit=1)
customer = env["res.partner"].create({"name": "[PRUEBA] Cliente guardas fase 1", "is_company": True,
                                      "country_id": ref("base.es").id, "vat": "ESB12345674", "city": "Madrid",
                                      "state_id": state.id})
supplier = env["res.partner"].create({"name": "[PRUEBA] Proveedor guardas fase 1", "is_company": True,
                                      "country_id": ref("base.es").id, "vat": "ESB12345674", "supplier_rank": 1})
sales_group = ref("sales_team.group_sale_salesman")
seller = env["res.users"].create({"name": "[PRUEBA] Comercial guardas", "login": "prueba.guardas.fase1",
                                  "group_ids": [Command.set([sales_group.id, ref("base.group_user").id])]})

# --- P1-21: the quotation state ---
order = env["sale.order"].create({"partner_id": customer.id, "order_line": [Command.create({
    "product_id": product("AWB").id, "product_uom_id": product("AWB").uom_id.id, "price_unit": 100.0})]})
check("P1-21 admin: direct write of state='sale' is refused", "UserError", refused(lambda: order.write({"state": "sale"})))
check("P1-21 admin: the order stays a draft", "draft", order.state)
as_seller = order.with_user(seller)
check("P1-21 salesperson: direct write of state='sale' is refused", "UserError",
      refused(lambda: as_seller.write({"state": "sale"})))
check("P1-21 salesperson: direct write of state='sent' is refused", "UserError",
      refused(lambda: as_seller.write({"state": "sent"})))
order.action_quotation_sent()
check("P1-21 button Send (mark as sent) still works", "sent", order.state)
order.action_draft()
check("P1-21 button Set to quotation still works", "draft", order.state)
order.action_cancel()
check("P1-21 button Cancel still works", "cancel", order.state)
order.action_draft()
other = order.write({"note": "<p>[PRUEBA] note</p>"})
check("P1-21 writes without state are untouched", True, other)

# --- P1-20: «Upload Bill» on a purchase order of a file ---
accepted = env["sale.order"].search([("state", "=", "sale"), ("boss_expediente_id", "!=", False)], order="id desc",
                                    limit=1) if "boss_expediente_id" in env["sale.order"]._fields else env["sale.order"]
po = env["purchase.order"].create({
    "partner_id": supplier.id, "order_line": [Command.create({
        "product_id": product("AWB").id, "product_qty": 1, "price_unit": 50.0, "name": "[PRUEBA] AWB"})]})
po.button_confirm()
po.order_line.qty_received = 1
attachment = env["ir.attachment"].create({"name": "[PRUEBA] factura.txt", "raw": b"prueba", "res_model": "purchase.order",
                                          "res_id": po.id})
got = po.action_create_invoice(attachment_ids=[attachment.id])
check("P1-20 action_create_invoice(attachment_ids=…) on a plain order works", True, bool(po.invoice_ids))
check("P1-20 the uploaded attachment reaches the bill's chatter", True,
      bool(po.invoice_ids.message_ids.attachment_ids.filtered(lambda a: a.id == attachment.id)))
file_po = env["purchase.order"].search([("boss_expediente_id", "!=", False), ("state", "in", ("purchase", "done"))],
                                       order="id desc", limit=1)
if file_po:
    try:
        file_po.action_create_invoice(attachment_ids=False)
        res = "ok"
    except TypeError as e:
        res = f"TypeError: {e}"
    except UserError:
        res = "ok"  # «nothing performed yet» is the BOSS message, not a signature error
    check("P1-20 action_create_invoice(attachment_ids=False) on a file's order: no TypeError", "ok", res)
else:
    print("CHECK SKIP P1-20 no confirmed purchase order of a file on boss20")

print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if not all(results):
    raise SystemExit(1)
