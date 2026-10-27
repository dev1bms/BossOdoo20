"""Ports and airports abroad (ADR-006): Ángel (27/10/2026) asked for the port abroad on the quotation, as in Odoo 17.
Source: Odoo 17 `x_puertos` as imported into Odoo 19 (`boss.location`, seaports with UN/LOCODE, airports with IATA
code), exported read-only to a CSV kept outside Git:
    dev/server_shell.sh load_ports.py .research/ports_odoo19.csv
Columns: kind (seaport/airport), code, name, country (ISO), canary (t/f). A port that already exists (same code and
kind) is left as it is; nothing is deleted. Idempotent."""
import csv
import io
import os

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
NAME = "ports_odoo19.csv"
assert NAME in os.environ.get("BOSS_FILES", "").split("|"), "port list not given"
with open(f"/tmp/boss/{NAME}", encoding="utf-8") as handle:
    rows = list(csv.DictReader(io.StringIO(handle.read())))
countries = {c.code: c.id for c in env["res.country"].search([])}  # noqa: F821
Port = env["boss.port"].with_context(active_test=False)  # noqa: F821
existing = {(p.code, p.kind) for p in Port.search([])}
kinds = {"seaport": "sea", "airport": "air"}
values, skipped = [], {"exists": 0, "country": 0}
for row in rows:
    key = (row["code"].strip().upper(), kinds[row["kind"]])
    if key in existing:
        skipped["exists"] += 1
        continue
    country = countries.get(row["country"])
    if not country:
        skipped["country"] += 1
        continue
    existing.add(key)
    values.append({"code": key[0], "kind": key[1], "name": row["name"].strip(), "country_id": country,
                   "canary_islands": row["canary"] == "t"})
for start in range(0, len(values), 1000):
    Port.create(values[start:start + 1000])
env.cr.commit()  # noqa: F821
print("PORTS read", len(rows), "| created", len(values), "| skipped", skipped, "| total now", Port.search_count([]))
