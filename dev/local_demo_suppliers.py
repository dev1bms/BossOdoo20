"""Local copy only (boss_test): fictitious suppliers named like the real ones, without their tariffs, so that
dev/demo_meeting.py and the guide screenshots use illustrative [DEMO] amounts only."""
assert env.cr.dbname in ("boss_test", "boss_uat"), env.cr.dbname
for name in ("MSC [DEMO]", "WFS [DEMO]", "IRENEO [DEMO]"):
    if not env["res.partner"].search([("name", "=", name)]):
        env["res.partner"].create({"name": name, "is_company": True})
env.cr.commit()
print("suppliers ok")
