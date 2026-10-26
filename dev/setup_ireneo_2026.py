"""IRENEO 2026: new version of the 2025 transport tariffs with the written confirmation of IRENEO (letter of
14/07/2026, attached to the e-mail «Actualización del Recargo por Combustible conforme a RDL 9/2026», read on the
server on 26/10/2026): «las tarifas aplicables a los servicios de transporte se incrementarán en un 10 %» from 15/07.
The letter covers transport only: TTE-CON, TTE-FCL and road X-R get 2025 × 1.10; SEG (percentage) stays; the
handling tariff (HAN, air X-R) is NOT versioned (Cristina confirms, docs/revision-tarifas.md). The new tariffs are
submitted, never approved here (Cristina approves). Idempotent (name). odoo shell on boss20 / boss20_uat."""
import base64
import glob
import os
from datetime import date

assert env.cr.dbname in ("boss20", "boss_test", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
Tariff = env["boss.tariff"]
TRANSPORT = ("TTE-CON", "TTE-FCL", "X-R")
FACTOR = 1.10
REFERENCE = "Carta IRENEO 14/07/2026 (RDL 9/2026): transporte +10 % desde 15/07/2026, sobre TARIFAS 2025"


def money(value):
    return round(value * FACTOR, 2) if value else value


for old in Tariff.search([("partner_id.name", "ilike", "IRENEO"), ("valid_to", "=", date(2025, 12, 31)),
                          ("line_ids.product_id.default_code", "in", TRANSPORT)]):
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
        new.write({"document": base64.b64encode(open(letters[0], "rb").read()),
                   "document_name": os.path.basename(letters[0])})
    changed = []
    for line in new.line_ids:
        if line.product_id.default_code not in TRANSPORT or line.tariff_id.transport_mode == "air":
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
