"""IRENEO 2026: new version of the 2025 transport tariffs with the written confirmation of IRENEO (letter of
14/07/2026, attached to the e-mail «Actualización del Recargo por Combustible conforme a RDL 9/2026», read on the
server on 26/10/2026): «las tarifas aplicables a los servicios de transporte se incrementarán en un 10 %» from 15/07.
The letter covers transport only: TTE-CON, TTE-FCL and road X-R get 2025 × 1.10; SEG (percentage) stays; the
handling tariff (HAN, air X-R) is NOT versioned (Cristina confirms, docs/revision-tarifas.md). The new tariffs are
submitted, never approved here (Cristina approves). Idempotent (name). odoo shell on boss20 / boss20_uat."""
import glob
import os
from datetime import date

from odoo.tools.binary import BinaryBytes

assert env.cr.dbname in ("boss20", "boss_test", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
Tariff = env["boss.tariff"]
TRANSPORT = ("TTE-CON", "TTE-FCL", "X-R")
FACTOR = 1.10
REFERENCE = "Carta IRENEO 14/07/2026 (RDL 9/2026): transporte +10 % desde 15/07/2026, sobre TARIFAS 2025"


def money(value):
    return round(value * FACTOR, 2) if value else value


# Only the road-transport tariffs (they carry TTE-CON / TTE-FCL); the handling tariffs (HAN, air X-R) are not covered.
for old in Tariff.search([("partner_id.name", "ilike", "IRENEO"), ("valid_to", "=", date(2025, 12, 31)),
                          ("line_ids.product_id.default_code", "in", ("TTE-CON", "TTE-FCL"))]):
    name = old.name.replace("2025", "2026") + " (+10 % transporte, carta 14/07/2026)"
    if Tariff.search_count([("name", "=", name)]):
        print("exists", name)
        continue
    new = old.copy({"name": name, "valid_from": date(2026, 7, 15), "valid_to": False,
                    "document_reference": REFERENCE, "scope_confirmed": old.scope_confirmed,
                    "note": "Versión 2026 creada el 26/10/2026 desde la tarifa 2025: líneas de transporte × 1,10 "
                            "según la carta de IRENEO del 14/07/2026 (adjunta al correo del mismo día). SEG sin "
                            "cambio. La carta no cubre el handling: HAN y X-R aéreo siguen en la tarifa 2025 hasta "
                            "que Cristina confirme."})
    letters = glob.glob("/tmp/boss/*.pdf")  # dev/server_shell.sh setup_ireneo_2026.py .research/ireneo-carta-2026-07-14.pdf
    if letters:
        with open(letters[0], "rb") as handle:
            new.write({"document": BinaryBytes(handle.read(), filename=os.path.basename(letters[0])),
                       "document_name": os.path.basename(letters[0])})
    new.scope_confirmed = True  # same scope as the 2025 tariff (reviewed on 26/10/2026 with the letter)
    changed = []
    for line in new.line_ids:
        if line.product_id.default_code not in TRANSPORT:
            continue
        line.write({"unit_price": money(line.unit_price), "min_amount": money(line.min_amount),
                    "max_amount": money(line.max_amount)})
        for bracket in line.bracket_ids:
            bracket.write({"fixed_amount": money(bracket.fixed_amount), "unit_price": money(bracket.unit_price)})
        changed.append(line.product_id.default_code)
    if new.document:
        new.action_submit()  # waiting for Cristina's approval; never approved here
    else:
        print("no letter mounted: left as draft without document")
    print("created", new.name, new.state, "valid from", new.valid_from, "lines x1.10:", changed)
env.cr.commit()
