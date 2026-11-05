"""Phase 1 permission guards with role users (tracker P1-22, P1-23, P1-24; audit of 05/11/2026), on boss20 inside a
transaction rolled back. Prints what each role can and cannot do; CHECK lines carry the expected behaviour.

P1-22 a salesperson with «own documents» opens, closes and cancels their own file.
P1-23 a file is deleted only while it is an empty draft (no order, costs or invoices), by nobody otherwise.
P1-24 cost-control fields (extra cost type, paid in advance, closed, variance reviewed, without order) are written only
      by purchasing, accounting or a sales manager; frozen and accepted prices never by a direct write.
    dev/uat_run.sh check_role_guards.py boss20"""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []
ERRORS = (UserError, ValidationError, AccessError)


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def outcome(fn):
    try:
        fn()
    except ERRORS as e:
        print(f"      refused: {type(e).__name__}: {str(e)[:160]}")
        return type(e).__name__
    except Exception as e:  # noqa: BLE001
        print(f"      ERROR: {type(e).__name__}: {str(e)[:160]}")
        return "ERROR " + type(e).__name__
    return "allowed"


ref = env.ref
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
state_m = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "M")], limit=1)
G = {"user": ref("base.group_user"), "sales": ref("sales_team.group_sale_salesman"),
     "sales_all": ref("sales_team.group_sale_salesman_all_leads"), "sales_mgr": ref("sales_team.group_sale_manager"),
     "purchase": ref("purchase.group_purchase_user"), "invoice": ref("account.group_account_invoice")}


def user(name, *groups):
    return env["res.users"].create({"name": f"[PRUEBA] {name}", "login": f"prueba.{name.lower().replace(' ', '.')}.p1",
                                    "group_ids": [Command.set([G["user"].id] + [G[g].id for g in groups])]})


seller = user("Comercial propio", "sales")
seller2 = user("Comercial ajeno", "sales")
mgr = user("Jefe ventas", "sales_mgr")
buyer = user("Compras", "purchase")
customer = env["res.partner"].create({"name": "[PRUEBA] Cliente guardas roles", "is_company": True, "vat": "ESB12345674",
                                      "country_id": ref("base.es").id, "city": "Madrid", "state_id": state_m.id})

# a file of the salesperson: created through a quotation they own, confirmed as admin (confirmation is covered by
# check_quote_flow); then every role action runs as the role user
order = env["sale.order"].create({"partner_id": customer.id, "user_id": seller.id, "order_line": [Command.create({
    "product_id": product("AWB").id, "product_uom_id": product("AWB").uom_id.id, "price_unit": 100.0})]})
file = env["boss.expediente"].search([("sale_order_ids", "in", order.ids)], limit=1) if "sale_order_ids" in env["boss.expediente"]._fields else env["boss.expediente"]
if not file:
    # the simplest file the model allows, owned by the salesperson
    vals = {"partner_id": customer.id, "user_id": seller.id} if "user_id" in env["boss.expediente"]._fields else {"partner_id": customer.id}
    file = env["boss.expediente"].create(vals)
print(f"      file {file.name} state {file.state} owner {file.user_id.name if 'user_id' in file._fields else '?'}")

# --- P1-22 salesperson on their own file ---
mine = file.with_user(seller)
check("P1-22 salesperson reads their own file (form data)", "allowed", outcome(lambda: mine.read(["name", "state", "partner_id", "rating_missing", "amount_to_invoice"])))
check("P1-22 salesperson reads the summary rows", "allowed", outcome(lambda: mine._boss_summary_rows()))
other = file.with_user(seller2)
check("P1-22 another salesperson with «own documents» cannot read it", "AccessError", outcome(lambda: other.read(["name"])))
check("P1-22 salesperson can cancel their own open file", "allowed", outcome(lambda: mine.action_cancel()))
check("P1-22 file is cancelled", "cancel", file.state)
mgr_file = file.with_user(mgr)
mgr_file._boss_reopen("[PRUEBA] reopen for the guard check") if file.state == "cancel" else None
check("P1-22 sales manager reopened it", "open", file.state)

# --- P1-23 deletion ---
check("P1-23 sales manager cannot delete a file with an order", "UserError", outcome(lambda: file.with_user(mgr).unlink()))
check("P1-23 admin cannot delete a file with an order either", "UserError", outcome(lambda: file.unlink()))
empty_vals = {"partner_id": customer.id}
empty = env["boss.expediente"].create(empty_vals)
check("P1-23 an empty draft can be deleted", "allowed", outcome(lambda: empty.unlink()))

# --- P1-24 cost-control fields and frozen prices ---
cost = env["boss.expediente.cost"].create({"expediente_id": file.id, "kind": "extra", "product_id": product("AWB").id,
                                           "uom_id": product("AWB").uom_id.id, "quantity": 1.0,
                                           "currency_id": env.company.currency_id.id, "name": "[PRUEBA] coste guardas"})
if cost:
    check("P1-24 salesperson cannot mark a cost «closed»", "AccessError", outcome(lambda: cost.with_user(seller).write({"closed": True})))
    check("P1-24 salesperson cannot mark «variance reviewed»", "AccessError", outcome(lambda: cost.with_user(seller).write({"variance_reviewed": True})))
    check("P1-24 purchasing can mark «variance reviewed»", "allowed", outcome(lambda: cost.with_user(buyer).write({"variance_reviewed": True})))
else:
    print("CHECK SKIP P1-24 the file has no cost line")
line = order.order_line[:1]
check("P1-24 admin: direct write of boss_price_frozen is refused", "UserError", outcome(lambda: line.write({"boss_price_frozen": True})))
res = outcome(lambda: line.with_user(seller).write({"boss_price_frozen": True}))
check("P1-24 salesperson: direct write of boss_price_frozen is refused", True, res in ("UserError", "AccessError"))

print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if not all(results):
    raise SystemExit(1)
