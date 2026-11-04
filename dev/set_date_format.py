"""English user interface with the Spanish date (meeting with Ángel, 04/11/2026): BOSS works in Spain, so dates read
day/month/year in English too, as in Spanish; the week already starts on Monday. Idempotent.
    dev/server_shell.sh set_date_format.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
lang = env["res.lang"]._lang_get("en_US")  # noqa: F821
before = (lang.date_format, lang.week_start)
lang.write({"date_format": "%d/%m/%Y", "week_start": "1"})
print("en_US date format", before, "->", (lang.date_format, lang.week_start))
env.cr.commit()  # noqa: F821
