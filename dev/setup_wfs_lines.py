"""WFS 2026 prices still missing in the [MUESTRA] WFS tariffs (Hoja1 B10/D10), read from the supplier document at run
time (prices stay out of Git):
    dev/server_shell.sh setup_wfs_lines.py "<Documents>/costs/TARIFAS-DE-CARGA-WFS-ESPANA-Validez desde-01.06.2026.pdf"
- item 12 «THC (Terminal Handling Charges)», general cargo, EXPORT: per chargeable kg with a minimum per AWB -> HAN of
  «[MUESTRA] WFS exportación PNS MAD/BCN desde 01/06/2026» (import is already loaded);
- item 49 «Recargo de Mantenimiento del Servicio», per AWB, «solo aplicable a la mercancía de importación» -> ETX of
  «[MUESTRA] WFS importación MAD/BCN desde 01/06/2026» (ETX = this surcharge: Odoo 17 bills, Cristina 08/10).
The document is identified by its SHA-256. Lines are added to the tariffs waiting for approval without changing their
state (a note in the chatter tells the approver). Approved tariffs are never touched. Idempotent."""
import hashlib
import io
import os
import re

from pypdf import PdfReader

from odoo import Command

assert env.cr.dbname in ("boss20", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
DOC = ("TARIFAS-DE-CARGA-WFS-ESPANA-Validez desde-01.06.2026.pdf",
       "ed6772fcee8616df3e4df65d70167777b04368424f1047941c03b198a1751639")
assert DOC[0] in os.environ.get("BOSS_FILES", "").split("|"), "document not given"
with open(f"/tmp/boss/{DOC[0]}", "rb") as handle:
    data = handle.read()
assert hashlib.sha256(data).hexdigest() == DOC[1], "not the WFS document of 01/06/2026"
pages = [" ".join((p.extract_text() or "").split()) for p in PdfReader(io.BytesIO(data)).pages]
p6, p10 = pages[5], pages[9]
m12 = re.search(r"12\. ?THC \(Terminal Handling Charges\) ?Carga General ?Import ?([\d.]+) ?€ ?([\d.]+) ?€ por AWB ?"
                r"Export ?([\d.]+) ?€ ?([\d.]+) ?€ por AWB", p6, re.I)
m49 = re.search(r"49\. ?Recargo de Mantenimiento del Servicio ?([\d.]+) ?€ ?Tarifa solo aplicable a la mercanc[ií]a de "
                r"importaci[oó]n", p10, re.I)
assert m12 and m49, ("item 12" if not m12 else "item 49") + " not found in the document"
export_kg, export_min, item49 = float(m12.group(3)), float(m12.group(4)), float(m49.group(1))
print(f"DOCUMENT ok: sha256 {DOC[1][:12]} | item 12 export read (per kg + minimum per AWB) | item 49 read (per AWB, import "
      f"only)")
Tariff = env["boss.tariff"]
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
plan = [
    ("[MUESTRA] WFS exportación PNS MAD/BCN desde 01/06/2026", "HAN",
     {"method": "per_unit", "basis": "awb_kg", "unit_price": export_kg, "min_amount": export_min,
      "document_page": "6 (punto 12, export)", "note": "Carga general; mínimo por AWB"}),
    ("[MUESTRA] WFS importación MAD/BCN desde 01/06/2026", "ETX",
     {"method": "per_unit", "basis": "line", "unit_price": item49, "document_page": "10 (punto 49)",
      "note": "Recargo de mantenimiento del servicio: solo importación, por AWB"}),
]
for name, code, values in plan:
    tariff = Tariff.search([("name", "=", name)], limit=1)
    assert tariff, name
    prod = product(code)
    existing = tariff.line_ids.filtered(lambda l, p=prod: l.product_id == p)
    if existing:
        same = abs(existing.unit_price - values["unit_price"]) < 1e-6 and abs(
            existing.min_amount - values.get("min_amount", 0.0)) < 1e-6
        print("already", name, code, "same as the document" if same else "DIFFERENT from the document")
        continue
    if tariff.state == "approved":
        print("approved, not changed:", name)
        continue
    env["boss.tariff.line"].create(dict(values, tariff_id=tariff.id, product_id=prod.id, uom_id=prod.uom_id.id))
    tariff.message_post(body=f"{code} añadido desde el documento WFS 2026, página {values['document_page']} "
                             f"(dev/setup_wfs_lines.py, 26/10/2026). Estado y aprobación sin cambios.")
    print("added", code, "to", name, "| unit", prod.uom_id.name, "| state", tariff.state)
env.cr.commit()
