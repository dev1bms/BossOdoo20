"""Hoja1 C7 «MSC import Far East tiene un GLO que aplica por TEU que hay que asociar a países de Far East»: the MSC FuelEU
per TEU (local charges 01/09/2026, «FuelEU para importaciones desde el Lejano Oriente») for the countries of the list
proposed on 07/10/2026 (estado 07-10 Estado!E14/L14: China, Hong Kong, Taiwán, Japón, Corea del Sur, Vietnam, Tailandia,
Malasia, Singapur, Indonesia, Filipinas, Camboya), applied by Belal's mandate of 26/10 (Cristina may ratify, P24).
China is already in «[MUESTRA] MSC gastos locales importación (origen China)»; this script adds a tariff with the same
FuelEU price (copied from that line, document identified by SHA-256) for the other eleven countries, so that no origin is
priced twice. WAITING FOR APPROVAL. Idempotent.
    dev/server_shell.sh setup_fueleu_far_east.py "<Documents>/costs/DRY - Gastos Locales 2026 - DRY desde 01.09.pdf\""""
import hashlib
import os

from odoo import Command
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname in ("boss20", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
DOC = ("DRY - Gastos Locales 2026 - DRY desde 01.09.pdf", "9b7e96c4fff9037d2e7c522166ee42d19f11e5255a0537a8f01582d817de8772")
assert DOC[0] in os.environ.get("BOSS_FILES", "").split("|"), "document not given"
with open(f"/tmp/boss/{DOC[0]}", "rb") as handle:
    raw = handle.read()
assert hashlib.sha256(raw).hexdigest() == DOC[1], "not the MSC local charges of 01/09/2026"
OTHERS = ["hk", "tw", "jp", "kr", "vn", "th", "my", "sg", "id", "ph", "kh"]
Tariff = env["boss.tariff"]
base = Tariff.search([("name", "=", "[MUESTRA] MSC gastos locales importación (origen China) 09-12/2026")], limit=1)
line = base.line_ids.filtered(lambda l: l.product_id.default_code == "GLO-FUELEU")
assert base and len(line) == 1, "FuelEU line of the MSC sample tariff not found"
name = "[MUESTRA] MSC FuelEU Lejano Oriente (sin China) 09-12/2026"
if Tariff.search_count([("name", "=", name)]):
    print("already", name)
else:
    tariff = Tariff.create({
        "name": name, "partner_id": base.partner_id.id, "carrier_id": base.carrier_id.id,
        "currency_id": base.currency_id.id, "valid_from": base.valid_from, "valid_to": base.valid_to,
        "direction": "import", "transport_mode": "sea", "load_type": "fcl", "port_ids": [Command.set(base.port_ids.ids)],
        "country_ids": [Command.set([env.ref(f"base.{c}").id for c in OTHERS])], "scope_confirmed": True,
        "document": BinaryBytes(raw, filename=DOC[0]), "document_name": DOC[0],
        "document_reference": base.document_reference + " — FuelEU Lejano Oriente; lista de países: propuesta 07/10/2026",
        "note": "Lista «Lejano Oriente» propuesta el 07/10/2026 y aplicada por mandato de Belal (26/10); China está en la "
                "tarifa de gastos locales (origen China).",
        "line_ids": [Command.create({
            "product_id": line.product_id.id, "uom_id": line.uom_id.id, "method": line.method, "basis": line.basis,
            "unit_price": line.unit_price, "document_page": line.document_page, "note": line.note})]})
    tariff.action_submit()
    print("created", name, tariff.state, "countries", ", ".join(tariff.country_ids.mapped("code")))
env.cr.commit()
