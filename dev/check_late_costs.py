"""Late costs and duplicate supplier references on boss20 (go-live tracker P3-10, default rules of P2-12), inside a
transaction rolled back.

- A vendor bill that reaches a file through its analytic account for a service with no service line creates that line
  as an extra cost «to approve», billed without order; the file's «to do» asks for the re-invoice/absorb decision.
- A bill with a supplier reference already registered is posted only by an accounting manager.
    dev/uat_run.sh check_late_costs.py boss20"""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def outcome(fn):
    try:
        fn()
    except (UserError, ValidationError, AccessError) as e:
        print(f"      refused: {type(e).__name__}: {str(e)[:170]}")
        return "refused"
    return "allowed"


ref = env.ref
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
state_m = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "M")], limit=1)
customer = env["res.partner"].create({"name": "[PRUEBA] Cliente costes tardíos", "is_company": True, "vat": "ESB12345674",
                                      "country_id": ref("base.es").id, "city": "Madrid", "state_id": state_m.id})
supplier = env["res.partner"].create({"name": "[PRUEBA] Naviera costes tardíos", "is_company": True, "vat": "ESB12345674",
                                      "country_id": ref("base.es").id, "supplier_rank": 1})
G = {"invoice": ref("account.group_account_invoice"), "manager": ref("account.group_account_manager"), "user": ref("base.group_user")}
acct = env["res.users"].create({"name": "[PRUEBA] Facturación tardíos", "login": "prueba.tardios.fact",
                                "group_ids": [Command.set([G["user"].id, G["invoice"].id])]})
chief = env["res.users"].create({"name": "[PRUEBA] Jefe contable tardíos", "login": "prueba.tardios.jefe",
                                 "group_ids": [Command.set([G["user"].id, G["manager"].id])]})
file = env["boss.expediente"].create({"partner_id": customer.id, "direction": "import", "transport_mode": "sea"})
check("0 the file has its analytic account", True, bool(file.analytic_account_id))
purchase_0 = env["account.tax"].with_context(lang="en_US").search([("name", "=", "0% S"), ("type_tax_use", "=", "purchase")], limit=1)
dem = product("DEM")
needs_before = len(file.cost_ids)


def bill(ref_text, user):
    move = env["account.move"].with_user(user).create({
        "move_type": "in_invoice", "partner_id": supplier.id, "invoice_date": date(2026, 12, 21), "ref": ref_text,
        "invoice_line_ids": [Command.create({"product_id": dem.id, "quantity": 2, "price_unit": 60.0,
                                             "tax_ids": [Command.set(purchase_0.ids)],
                                             "analytic_distribution": {str(file.analytic_account_id.id): 100}})]})
    move.action_post()
    return move


late = bill("[PRUEBA] DEM-TARDE-1", acct)
env.invalidate_all()
need = file.cost_ids.filtered(lambda n: n.product_id == dem)
check("1 a late bill without service line creates one extra cost on the file", needs_before + 1, len(file.cost_ids))
check("1 the extra cost is «to approve», billed without order, by the bill's supplier",
      ("approval", True, "billed", supplier.id), (need.extra_class, need.without_order, need.state, need.partner_id.id))
check("1 its billed amount is the bill's", 120.0, round(need.sudo().billed_amount_company, 2))
check("1 the file's «to do» asks for the decision", True, "DEM" in (file.completeness or "") or bool(need.extra_class == "approval"))
late2 = env["account.move"].with_user(acct).create({
    "move_type": "in_invoice", "partner_id": supplier.id, "invoice_date": date(2026, 12, 22), "ref": "[PRUEBA] DEM-TARDE-1",
    "invoice_line_ids": [Command.create({"product_id": dem.id, "quantity": 1, "price_unit": 10.0,
                                         "tax_ids": [Command.set(purchase_0.ids)],
                                         "analytic_distribution": {str(file.analytic_account_id.id): 100}})]})
check("2 billing cannot post a bill with a supplier reference already registered", "refused", outcome(late2.action_post))
check("2 an accounting manager can (confirms it is not a duplicate)", "allowed", outcome(late2.with_user(chief).action_post))
env.invalidate_all()
check("2 the second bill feeds the same extra cost (no second line)", needs_before + 1, len(file.cost_ids))
need.with_user(chief).write({"extra_class": "absorb"})
check("3 the decision «borne by BOSS» is written by accounting", "absorb", need.extra_class)
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if not all(results):
    raise SystemExit(1)
