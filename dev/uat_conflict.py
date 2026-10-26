"""boss20_uat / boss20: the BL conflict case of S4 (dev/uat_scenarios.py) with a second approved [DEMO] tariff of the
SAME scope as «[DEMO] MSC gastos locales importación Valencia 2026» (a more specific tariff wins; only equal scopes
conflict). Idempotent."""
from datetime import date

from odoo import Command
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname in ("boss20_uat", "boss20"), env.cr.dbname  # noqa: F821
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES", tracking_disable=True))  # noqa: F821
Tariff = env["boss.tariff"]
base = Tariff.search([("name", "=", "[DEMO] MSC gastos locales importación Valencia 2026")], limit=1)
bl = env["product.product"].search([("default_code", "=", "BL")], limit=1)
name = "[DEMO] MSC BL alternativo mismo alcance 2026 (conflicto)"
other = Tariff.search([("name", "=", name)], limit=1)
if not other:
    other = Tariff.create({
        "name": name, "partner_id": base.partner_id.id, "carrier_id": base.carrier_id.id,
        "currency_id": base.currency_id.id, "valid_from": base.valid_from, "valid_to": base.valid_to,
        "direction": base.direction, "transport_mode": base.transport_mode, "load_type": base.load_type,
        "port_ids": [Command.set(base.port_ids.ids)], "country_ids": [Command.set(base.country_ids.ids)],
        "customer_id": base.customer_id.id, "is_demo": True, "scope_confirmed": True,
        "document_reference": "[DEMO] segunda tarifa ficticia del BL, mismo alcance, para mostrar un conflicto",
        "document_name": "demo.txt", "document": BinaryBytes(b"DEMO", filename="demo.txt"),
        "line_ids": [Command.create({"product_id": bl.id, "uom_id": bl.uom_id.id, "method": "per_unit",
                                     "basis": "line", "unit_price": 70.0})]})
    other.action_submit()
    other.action_approve()
print("base scope:", base.scope_summary, "| other:", other.scope_summary, other.state)
s4 = env["sale.order"].search([("origin", "=like", "[UAT] escenarios 26/10/2026 S4%")], limit=1)
s4.action_boss_update_costs() if hasattr(s4, "action_boss_update_costs") else None
line = s4.order_line.filtered(lambda l: l.product_id.default_code == "BL")
line.invalidate_recordset()
print("S4", s4.name, "BL:", line.boss_cost_status, line.purchase_price, "| explanation:",
      " ".join((line.boss_cost_explanation or "")[:400].split()) if "boss_cost_explanation" in line._fields else "")
env.cr.commit()
