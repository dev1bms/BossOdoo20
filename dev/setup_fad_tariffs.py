"""FAD (import customs clearance) of the two brokers Cristina named in «Plan detallado previsiones.xlsx» (Explicaciones
A111:A118, A34:A37, her e-mail of 28/09/2026): one price by number of containers of the shipment, per declaration.
    dev/server_shell.sh setup_fad_tariffs.py .research/fad-cristina-2026-09-28.json
The figures come from that private file (outside Git, transcribed from the Excel); the file itself is attached as the
document of each tariff. Brokers created as suppliers with their Odoo 17 id in «ref» when missing. Tariffs left WAITING
FOR APPROVAL (Cristina approves). The «59 € per partida» case is to be checked with Laura (A120): not loaded.
Idempotent."""
import json
import os
from datetime import date

from odoo import Command
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname in ("boss20", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
NAME = "fad-cristina-2026-09-28.json"
assert NAME in os.environ.get("BOSS_FILES", "").split("|"), "data file not given"
with open(f"/tmp/boss/{NAME}", "rb") as handle:
    raw = handle.read()
data = json.loads(raw)
Partner, Tariff = env["res.partner"], env["boss.tariff"]
fad = env["product.product"].search([("default_code", "=", "FAD")], limit=1)
broker_role = env.ref("boss_expediente.role_customs_broker")
for supplier_name, spec in data["suppliers"].items():
    partner = Partner.search([("ref", "=", f"O17:{spec['o17_id']}")], limit=1) or Partner.search(
        [("name", "=", supplier_name)], limit=1)
    if not partner:
        partner = Partner.create({"name": supplier_name, "is_company": True, "ref": f"O17:{spec['o17_id']}",
                                  "boss_is_supplier": True, "boss_role_ids": [Command.link(broker_role.id)],
                                  "country_id": env.ref("base.es").id})
        print("supplier created", partner.name, partner.ref)
    name = f"[MUESTRA] {supplier_name} FAD importación FCL (Cristina 28/09/2026)"
    tariff = Tariff.search([("name", "=", name)], limit=1)
    if tariff:
        print("already", name, tariff.state)
        continue
    tariff = Tariff.create({
        "name": name, "partner_id": partner.id, "currency_id": env.company.currency_id.id,
        "valid_from": date(2026, 1, 1), "direction": "import", "transport_mode": "sea", "load_type": "fcl",
        "scope_confirmed": True, "document": BinaryBytes(raw, filename=NAME), "document_name": NAME,
        "document_reference": data["source"], "note": data["quote"] + " " + data["pending"],
        "line_ids": [Command.create({
            "product_id": fad.id, "uom_id": fad.uom_id.id, "method": "brackets", "basis": "containers",
            "document_page": "Explicaciones A111:A118",
            "bracket_ids": [Command.create({"up_to": up_to, "fixed_amount": amount})
                            for up_to, amount in spec["brackets"]]})]})
    tariff.action_submit()
    print("created", name, tariff.state, f"{len(spec['brackets'])} steps by number of containers")
env.cr.commit()
