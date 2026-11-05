"""Personal administrator account for Belal on boss20 (tracker P1-15, 05/11/2026). Commits. No password is set here:
Belal sets it from Settings › Users (Change password) while logged in as admin. Idempotent."""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
Users = env["res.users"].with_context(active_test=False)  # noqa: F821
login = "balswerki@bidatia.com"
user = Users.search([("login", "=", login)], limit=1)
if not user:
    user = Users.create({"name": "Belal Alswerki", "login": login, "email": login,
                         "group_ids": [(4, env.ref("base.group_system").id), (4, env.ref("base.group_user").id)]})  # noqa: F821
    print(f"OUT created user {user.id} {login} (administrator, no password yet)")
else:
    user.write({"active": True, "group_ids": [(4, env.ref("base.group_system").id)]})  # noqa: F821
    print(f"OUT user {user.id} {login} already existed: active and administrator")
env.cr.commit()  # noqa: F821
