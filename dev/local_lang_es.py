"""Local copy only (boss_test): the admin works in Spanish, like the BOSS team, for the guide screenshots."""
assert env.cr.dbname == "boss_test", env.cr.dbname  # noqa: F821
env.ref("base.user_admin").lang = "es_ES"  # noqa: F821
env.cr.commit()  # noqa: F821
print("admin es_ES")
