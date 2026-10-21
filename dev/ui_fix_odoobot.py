env = env  # noqa: F821
assert env.cr.dbname == "boss_test"
env.ref("base.user_admin").odoobot_state = "disabled"
env.cr.commit()
print("ODOOBOT", env.ref("base.user_admin").odoobot_state)
