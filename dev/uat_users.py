"""boss20_uat: one internal user per BOSS role so the cycle is tried without the administrator (Belal's mandate
26/10/2026: tests with role permissions, not admin). No password is set here: Belal sets them from Settings > Users
(«Change password»). Idempotent."""
assert env.cr.dbname == "boss20_uat", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, no_reset_password=True))  # noqa: F821
USERS = {
    "uat_ventas": ("[UAT] Ventas (comercial)", ["sales_team.group_sale_salesman", "boss_pricing.group_tariff_user",
                                                "purchase.group_purchase_user"]),
    "uat_operaciones": ("[UAT] Operaciones (jefe de ventas y compras)",
                        ["sales_team.group_sale_manager", "purchase.group_purchase_manager",
                         "boss_pricing.group_tariff_approver"]),
    "uat_contabilidad": ("[UAT] Contabilidad", ["account.group_account_invoice", "account.group_account_user"]),
}
Users = env["res.users"]
for login, (name, groups) in USERS.items():
    user = Users.search([("login", "=", login)], limit=1)
    group_ids = [env.ref(g).id for g in groups]
    if not user:
        user = Users.create({"login": login, "name": name, "email": f"{login}@example.com",
                             "group_ids": [(6, 0, group_ids)], "lang": "es_ES"})
    else:
        user.write({"group_ids": [(4, g) for g in group_ids]})
    print(login, user.name, sorted(user.group_ids.mapped("full_name"))[:8])
env.cr.commit()
