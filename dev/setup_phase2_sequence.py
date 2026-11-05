"""File numbering that never repeats an Odoo 17 number (go-live tracker P2-01; P36 answered: yearly series, E270001
from 2027; boss20 is the production database, Belal 05/11/2026). Commits. Idempotent.

Odoo 17 numbers its files E%(yy)s%(nnnn)s per year (about 1,300-1,800 a year; on 05/11/2026 it is in E2613xx and
keeps numbering until the cut-over). boss20 uses the same shape, so its 2026 files start at E269001: far above any
number Odoo 17 can reach this year. From 2027 the yearly range starts at E270001 (Odoo 17 stops at the cut-over).
    dev/server_shell.sh setup_phase2_sequence.py"""
from datetime import date

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
seq = env.ref("boss_expediente.sequence_expediente")  # noqa: F821
Range = env["ir.sequence.date_range"]  # noqa: F821
print(f"OUT before: prefix {seq.prefix!r} padding {seq.padding} next {seq.number_next_actual} date ranges {seq.use_date_range}")
seq.write({"use_date_range": True, "prefix": "E%(range_y)s", "padding": 4})
for year, first in ((2026, 9001), (2027, 1)):
    rng = Range.search([("sequence_id", "=", seq.id), ("date_from", "=", date(year, 1, 1))], limit=1)
    if not rng:
        rng = Range.create({"sequence_id": seq.id, "date_from": date(year, 1, 1), "date_to": date(year, 12, 31),
                            "number_next_actual": first})
    elif rng.number_next_actual < first:
        rng.write({"number_next_actual": first})
    print(f"OUT range {year}: next number {rng.number_next_actual}")
env.cr.commit()  # noqa: F821
env.cr.execute("select max(name) from boss_expediente")
print(f"OUT highest boss20 file today: {env.cr.fetchone()[0]}; next 2026 file will be "  # noqa: F821
      f"E26{Range.search([('sequence_id', '=', seq.id), ('date_from', '=', date(2026, 1, 1))]).number_next_actual:04d}")
