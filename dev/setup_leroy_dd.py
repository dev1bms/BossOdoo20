"""Demurrage (DEM) and port occupancy (OCU) for import of ONE, Maersk, OOCL and MSC (Hoja1 E10), from the only document
that has them: the carriers' conditions of the Leroy Merlin tender «DIAS LIBRES Y TARIFAS HAPAG JUNIO 2025.xlsx»
(OPERACIONES › LEROY MERLIN › Resto › TARIFAS NAVIERAS; header «2025/2026»), sheet «DEMORAS Y OCUPACIONES»: per carrier,
container type and Spanish port, free days and EUR per day. ZIM is not in it (nor anywhere else searched).
    dev/server_shell.sh setup_leroy_dd.py "<…>/DIAS LIBRES Y TARIFAS HAPAG JUNIO 2025.xlsx"
The file is identified by its SHA-256 and read at run time (prices stay out of Git). One tariff per carrier and port,
only for the customer Leroy Merlin (they are its tender conditions), valid from 01/06/2025 with no end (the file states
none), WAITING FOR APPROVAL (Cristina approves). Missing partners are created with their Odoo 17 id in «ref».
Idempotent by tariff name."""
import hashlib
import io
import os
from datetime import date

import openpyxl

from odoo import Command
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname in ("boss20", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
DOC = ("DIAS LIBRES Y TARIFAS HAPAG JUNIO 2025.xlsx", "98ee301b0c3151db9c84d56324a40b6801579d4b200058900836bb9a82519db2")
assert DOC[0] in os.environ.get("BOSS_FILES", "").split("|"), "document not given"
with open(f"/tmp/boss/{DOC[0]}", "rb") as handle:
    raw = handle.read()
assert hashlib.sha256(raw).hexdigest() == DOC[1], "not the Leroy tender file of June 2025"
ws = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)["DEMORAS Y OCUPACIONES"]
rows = [r for r in ws.iter_rows(min_row=4, values_only=True) if r[0]]
Partner, Tariff = env["res.partner"], env["boss.tariff"]
ref = env.ref
PORTS = {"VALENCIA": ref("boss_pricing.port_esvlc"), "BARCELONA": ref("boss_pricing.port_esbcn"),
         "ALGECIRAS": ref("boss_pricing.port_esalg")}
TYPES = {"DV": ref("boss_pricing.container_type_dv"), "D": ref("boss_pricing.container_type_dv"),
         "HC": ref("boss_pricing.container_type_hc")}
CARRIERS = {"ONE": ("OCEAN NETWORK EXPRESS PTE LTD", 36546), "MAERSK": ("MAERSK LINE", 23001),
            "OOCL": ("OOCL - ORIENT OVERSEAS CONTAINER LINE (SPAIN) SL", 23358), "MSC": None}


def equipment(text):
    text = str(text).replace(" ", "").upper()
    size, kind = text[:2], text[2:]
    return size, TYPES.get(kind)


def partner(name, o17_id, role, **vals):
    found = Partner.search([("ref", "=", f"O17:{o17_id}")], limit=1) or Partner.search([("name", "=", name)], limit=1)
    if not found:
        found = Partner.create(dict(vals, name=name, is_company=True, ref=f"O17:{o17_id}",
                                    boss_role_ids=[Command.link(role.id)]))
        print("partner created", name, found.ref)
    return found


customer = partner("LEROY MERLIN ESPAÑA, S.L.U.", 23014, ref("boss_expediente.role_customer"),
                   country_id=ref("base.es").id) if env.ref("boss_expediente.role_customer", raise_if_not_found=False) \
    else Partner.search([("ref", "=", "O17:23014")], limit=1) or Partner.create(
        {"name": "LEROY MERLIN ESPAÑA, S.L.U.", "is_company": True, "ref": "O17:23014", "country_id": ref("base.es").id})
products = {code: env["product.product"].search([("default_code", "=", code)], limit=1) for code in ("DEM", "OCU")}
created = 0
for code in CARRIERS:
    if CARRIERS[code]:
        carrier = partner(*CARRIERS[code], ref("boss_expediente.role_carrier"), boss_is_supplier=True)
    else:
        carrier = Partner.search([("name", "=", "MSC [MUESTRA]")], limit=1)
    for port_name, port in PORTS.items():
        lines = []
        for row in rows:
            for offset, prod_code in ((0, "DEM"), (6, "OCU")):
                name_, equip, free, per_day, dest = row[offset:offset + 5]
                if str(name_).strip().upper() != code or str(dest).strip().upper() != port_name:
                    continue
                size, ctype = equipment(equip)
                prod = products[prod_code]
                lines.append(Command.create({
                    "product_id": prod.id, "uom_id": prod.uom_id.id, "method": "time", "basis": "containers",
                    "container_size": size, "container_type_ids": [Command.set(ctype.ids)] if ctype else [],
                    "free_days": int(free), "free_mode": "deduct", "period_unit": "calendar",
                    "document_page": f"DEMORAS Y OCUPACIONES ({prod_code} {equip})",
                    "bracket_ids": [Command.create({"up_to": 0, "unit_price": float(per_day)})]}))
        if not lines:
            continue
        name = f"[MUESTRA] {code} demoras y ocupaciones importación {port_name.title()} (licitación Leroy Merlin 2025/2026)"
        if Tariff.search_count([("name", "=", name)]):
            print("already", name)
            continue
        tariff = Tariff.create({
            "name": name, "partner_id": carrier.id, "carrier_id": carrier.id, "customer_id": customer.id,
            "currency_id": env.company.currency_id.id, "valid_from": date(2025, 6, 1), "direction": "import",
            "transport_mode": "sea", "load_type": "fcl", "port_ids": [Command.set(port.ids)], "scope_confirmed": True,
            "document": BinaryBytes(raw, filename=DOC[0]), "document_name": DOC[0],
            "document_reference": f"Licitación Leroy Merlin, condiciones de navieras 2025/2026 (sha256 {DOC[1][:12]})",
            "note": "Condiciones de la licitación de Leroy Merlin: solo para ese cliente. Periodo de demoras y ocupaciones: "
                    "el de defecto del servicio (el fichero no lo dice). Fin de vigencia no indicado.",
            "line_ids": lines})
        tariff.action_submit()
        created += 1
        print("created", name, f"{len(lines)} prices", tariff.state)
print("TARIFFS CREATED", created, "| ZIM: not in the document")
env.cr.commit()
