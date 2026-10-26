"""Load reference supplier tariffs into Odoo (odoo shell). The data file is private (real prices) and is
passed as /tmp/samples.json; this script holds no price. Tariffs are created once (idempotent), sent for
approval with their document, and never approved here.
"""
import json

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname in ("boss20", "boss_test", "boss20_uat"), env.cr.dbname
data = json.load(open("/tmp/samples.json", encoding="utf-8"))
created = env["boss.tariff"]._boss_import_tariffs(data)
env.cr.commit()
print("SAMPLES created:", len(created), "states:", sorted(set(created.mapped("state"))),
      "with document:", len(created.filtered("document")))
print("SAMPLES total in database:", env["boss.tariff"].search_count([("name", "like", "[MUESTRA]")]))
