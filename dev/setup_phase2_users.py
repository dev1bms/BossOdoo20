"""Named users by role on boss20 (go-live tracker P2-02, P2-03, P2-04; documented defaults F0-C01, P20, P35, P19 applied
on 05/11/2026 by Belal's rule «apply what is documented»). Commits. Idempotent.

- The internal users of Odoo 17 (read 05/11/2026, read-only) get a user with the same login and the role template of
  their Odoo 17 sales group: «own documents» -> salesperson / operator; «all documents» -> manager of documents.
  No password is set (no mail server): Belal sets them in Settings › Users. The shared mailbox «Sales Boss» is not
  created (named users only).
- Cristina: sales manager, purchase manager and the only tariff approver (P19); Ángel: accounting manager, reads every
  file; Pablo: backup administrator (default until Santos names one, P2-03); Belal: administrator.
- Only Belal (both accounts) and the backup administrator keep administration (P2-02); the tariff-approver group stays
  with Cristina and Belal only (P2-04).
    dev/server_shell.sh setup_phase2_users.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, no_reset_password=True))  # noqa: F821
ref = env.ref
Users = env["res.users"].with_context(active_test=False)
ADMIN, USER = ref("base.group_system"), ref("base.group_user")
T = {
    "operator": ["base.group_user", "sales_team.group_sale_salesman", "boss_pricing.group_tariff_user",
                 "purchase.group_purchase_user"],
    "manager_docs": ["base.group_user", "sales_team.group_sale_salesman_all_leads", "boss_pricing.group_tariff_user",
                     "purchase.group_purchase_user"],
    "cristina": ["base.group_user", "sales_team.group_sale_manager", "purchase.group_purchase_manager",
                 "boss_pricing.group_tariff_user", "boss_pricing.group_tariff_approver"],
    "angel": ["base.group_user", "account.group_account_manager", "sales_team.group_sale_salesman_all_leads",
              "purchase.group_purchase_user", "boss_pricing.group_tariff_user"],
}
# Odoo 17 internal users (res.users, groups 21 «own documents» / 22 «all documents»), without the shared mailbox.
NEW = [
    ("Amalia Perez", "aperez@bosscontinental.com", "manager_docs"),
    ("Solanguie Niño", "snino@bosscontinental.com", "manager_docs"),
    ("Elisabeth Bastida", "ebastida@bosscontinental.com", "operator"),
    ("Flor Quispe", "fquispe@bosscontinental.com", "operator"),
    ("Giancarlo Castañeda", "operaciones1@bosscontinental.com", "operator"),
    ("Jose Manuel Lopez", "jmlopez@bosscontinental.com", "operator"),
    ("Laura Rodriguez", "lrodriguez@bosscontinental.com", "operator"),
    ("Ricardo Bastos", "rbastos@bosscontinental.com", "operator"),
    ("Tommy Reyes", "treyes@bosscontinental.com", "operator"),
    ("Wendy Chen", "wchen@bosscontinental.com", "operator"),
]
EXISTING = {"csantisteban@bosscontinental.com": "cristina", "adesantisteban@bosscontinental.com": "angel"}
KEEP_ADMIN = {"devbms", "balswerki@bidatia.com", "pespinosa@bosscontinental.com"}
APPROVERS = {"devbms", "csantisteban@bosscontinental.com"}
gids = lambda names: [ref(g).id for g in names]  # noqa: E731

for name, login, template in NEW:
    user = Users.search([("login", "=", login)], limit=1)
    if not user:
        user = Users.create({"name": name, "login": login, "email": login, "lang": "es_ES",
                             "group_ids": [(6, 0, gids(T[template]))]})
        print(f"OUT created {login} as {template}")
    else:
        user.write({"active": True, "group_ids": [(4, g) for g in gids(T[template])]})
        print(f"OUT kept {login}, groups of {template} ensured")
for login, template in EXISTING.items():
    user = Users.search([("login", "=", login)], limit=1)
    assert user, login
    user.write({"group_ids": [(4, g) for g in gids(T[template])]})
    print(f"OUT {login}: groups of {template} ensured")

approver = ref("boss_pricing.group_tariff_approver")
for user in Users.search([("share", "=", False), ("active", "=", True), ("id", "!=", 1)]):
    changes = {}
    if ADMIN in user.group_ids and user.login not in KEEP_ADMIN:
        changes["admin removed"] = (3, ADMIN.id)
    if approver in user.group_ids and user.login not in APPROVERS:
        changes["approver removed"] = (3, approver.id)
    if changes:
        user.write({"group_ids": list(changes.values())})
        print(f"OUT {user.login}: {', '.join(changes)}")
env.cr.commit()  # noqa: F821
env.invalidate_all()
internal = Users.search([("share", "=", False), ("active", "=", True), ("id", "!=", 1)])
print(f"OUT internal users now: {len(internal)}")
print("OUT administrators: " + ", ".join(sorted(internal.filtered(lambda u: ADMIN in u.all_group_ids).mapped("login"))))
print("OUT tariff approvers: " + ", ".join(sorted(internal.filtered(lambda u: approver in u.all_group_ids).mapped("login"))))
