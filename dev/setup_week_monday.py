"""The week starts on Monday in every BOSS language (Ángel, meeting 27/10/2026: date pickers started on Sunday in
English). Setting of res.lang, idempotent.    dev/server_shell.sh setup_week_monday.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
langs = env["res.lang"].search([("active", "=", True)])  # noqa: F821
langs.filtered(lambda l: l.week_start != "1").write({"week_start": "1"})
env.cr.commit()  # noqa: F821
print("WEEK START", [(lang.code, lang.week_start) for lang in langs])
