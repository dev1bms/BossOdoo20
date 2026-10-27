"""ALM (airport storage) of IRENEO: its bonded warehouse G-5 (ADT) at Madrid-Barajas, «TARIFAS MAD 2025.pdf» p.15
«ALMACENAJES» (free calendar days, price per 100 kg or fraction and day, minimum, 1 m³ = 167 kg). 2026 = 2025 prices
(Ángel, 14/10/2026, as the other IRENEO handling tariffs; the letter of 14/07/2026 only raises transport). Requested by
Belal on 27/10/2026.
    dev/server_shell.sh setup_ireneo_alm.py "<NEW ODOO>/IRENEO/TARIFAS MAD 2025.pdf"
The PDF is identified by its SHA-256 and the amounts are read from it at run time (prices stay out of Git).
How the free days work is not written in the document (deducted, or every day charged once exceeded): loaded as
«deducted» and left WAITING FOR APPROVAL until IRENEO or Cristina confirm it. Period: from the pickup at the handler
(cargo moved to G-5) to the delivery out of the warehouse, in calendar days (entry and exit days counted, p.4 rule of the
same document). The Friday rule of p.17 (cargo moved on Friday or the eve of a holiday: general tariff with 2 free
calendar days) is a different case and is not modelled. Idempotent by name."""
import hashlib
import io
import os
import re
from datetime import date

from odoo import Command
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
DOC = ("TARIFAS MAD 2025.pdf", "71459edc1fe6108f8b1885fcc363f7ad45213d3dba147f67bccf65665ce02e42")
NAME = "[MUESTRA] IRENEO almacén G-5 (ADT) importación MAD 2026 (precios 2025)"
assert DOC[0] in os.environ.get("BOSS_FILES", "").split("|"), "document not given"
with open(f"/tmp/boss/{DOC[0]}", "rb") as handle:
    raw = handle.read()
assert hashlib.sha256(raw).hexdigest() == DOC[1], "not IRENEO «TARIFAS MAD 2025»"
try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader
page = PdfReader(io.BytesIO(raw)).pages[14].extract_text()  # p.15
assert "ALMACENAJES" in page and "G-5" in page, "p.15 is not the G-5 storage page"
number = lambda text: float(text.replace(".", "").replace(",", "."))  # noqa: E731
free_days = int(re.search(r"FRANQUICIA\s+(\d+)\s+D.AS\s+NATURALES", page).group(1))
price = number(re.search(r"([\d.,]+)\s*\S\s*/\s*100\s*KG\s+o\s+FRACCI.N\s*/\s*D.A", page).group(1))
minimum = number(re.search(r"M.NIMO\s+([\d.,]+)\s*\S\s*\n\s*MOZOS", page).group(1))
factor = int(re.search(r"1\s*m3\s*=\s*(\d+)\s*kgs", page).group(1))
print("READ from p.15: free days", free_days, "| per 100 kg/day read | minimum read | volumetric factor", factor)

Tariff = env["boss.tariff"]
if Tariff.search_count([("name", "=", NAME)]):
    print("already", NAME)
else:
    alm = env["product.product"].search([("default_code", "=", "ALM")], limit=1)
    ireneo = env["res.partner"].search([("ref", "=", "O17:23062")], limit=1)
    mad = env["boss.port"].search([("code", "=", "MAD")], limit=1)
    assert alm and ireneo and mad
    tariff = Tariff.create({
        "name": NAME, "partner_id": ireneo.id, "currency_id": env.ref("base.EUR").id, "valid_from": date(2026, 1, 1),
        "direction": "import", "transport_mode": "air", "load_type": "air", "port_ids": [Command.set(mad.ids)],
        "scope_confirmed": True, "document": BinaryBytes(raw, filename=DOC[0]), "document_name": DOC[0],
        "document_reference": "IRENEO Tarifas MAD 2025, p.15 «Almacenajes» G-5 (ADT); mismos precios en 2026 "
                              f"(Ángel, 14/10/2026); sha256 {DOC[1][:12]}",
        "note": "Almacén aduanero G-5 de IRENEO en Barajas (mercancía trasladada desde el handler). PENDIENTE DE "
                "CONFIRMAR con IRENEO o Cristina: si los días libres se descuentan (cargado así) o, superados, se cobra "
                "desde el día 1. Días naturales: cuentan el día de entrada y el de salida (p.4). La regla de los viernes "
                "o vísperas de festivo (p.17, 2 días naturales libres con la tarifa general) no está modelada. Las otras "
                "partidas del G-5 (recepción, manipulación, reexpedición) son otros servicios.",
        "line_ids": [Command.create({
            "product_id": alm.id, "uom_id": alm.uom_id.id, "method": "time", "basis": "chargeable_kg",
            "volumetric_factor": factor, "unit_size": 100.0, "round_up": True, "free_days": free_days,
            "free_mode": "deduct", "period_unit": "calendar", "tier_mode": "positional",
            "period_start_event": "pickup", "period_end_event": "delivery", "min_amount": minimum,
            "document_page": "p.15 (Almacenajes G-5)",
            "note": "Lectura de los días libres por confirmar (descontados / desde el día 1)",
            "bracket_ids": [Command.create({"up_to": 0, "unit_price": price})]})],
    })
    tariff.action_submit()
    print("created", tariff.id, NAME, tariff.state, "|", tariff.scope_summary)
env.cr.commit()
