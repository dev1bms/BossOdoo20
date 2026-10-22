"""Read-only permission check on boss20 / the local copy (odoo shell): what each internal user may do with
supplier prices. Every write attempt is rolled back."""
from odoo.exceptions import AccessError, UserError
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname  # noqa: F821
groups = {g: env.ref(g) for g in ("sales_team.group_sale_salesman", "boss_pricing.group_tariff_user",
                                  "boss_pricing.group_tariff_approver")}
users = env["res.users"].search([("share", "=", False)])
real_customer = env["res.partner"].search([("boss_demo", "=", False), ("sale_order_ids", "!=", False)], limit=1)
for user in users:
    roles = [g.split(".")[1] for g, rec in groups.items() if user in rec.all_user_ids]
    res = {}
    def attempt(name, fn):
        sp = env.cr.savepoint()
        try:
            fn(); res[name] = "yes"
        except (AccessError, UserError) as exc:
            res[name] = "no"
        finally:
            sp.rollback()
    u = env(user=user)
    attempt("read prices", lambda: u["boss.tariff.line"].search([], limit=1).mapped("unit_price"))
    attempt("mark demo customer", lambda: real_customer.with_user(user).write({"boss_demo": True}))
    draft = u["boss.tariff"].sudo().search([("state", "=", "to_approve")], limit=1)
    attempt("approve", lambda: draft.with_user(user).action_approve() if draft else None)
    print(user.login, roles, res)
env.cr.rollback()
