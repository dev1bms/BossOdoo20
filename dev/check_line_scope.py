"""Read-only check of the price-line scope (ADR-002 amendment, 27/10/2026) on boss20: one draft tariff with several
sections (import pickup and export package of the same service, two provinces of a road price) is simulated as
approved; each price must apply only to its own section, the checklist must report overlapping prices and a line may
not widen its tariff. Illustrative amounts (not supplier prices). Everything is rolled back.
Prints «CHECK PASS|FAIL …» and «RESULT n passed, m failed».    dev/uat_run.sh check_line_scope.py boss20"""
from datetime import date

from odoo import Command
from odoo.exceptions import ValidationError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
P, results = env["product.product"], []  # noqa: F821
ref = env.ref  # noqa: F821


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected} got {got}")


han = P.search([("default_code", "=", "HAN")], limit=1)
tte = P.search([("default_code", "=", "TTE-CON")], limit=1)
mad = env["boss.port"].search([("code", "=", "MAD")], limit=1)  # noqa: F821
supplier = env["res.partner"].create({"name": "[PRUEBA] Proveedor alcance por línea"})  # noqa: F821
madrid = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "M")], limit=1)  # noqa: F821
valencia = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "V")], limit=1)  # noqa: F821
tariff = env["boss.tariff"].create({  # noqa: F821
    "name": "[PRUEBA] Un documento, varias secciones", "partner_id": supplier.id, "valid_from": date(2026, 1, 1),
    "transport_mode": "air", "load_type": "air", "port_ids": [Command.set(mad.ids)],
    "line_ids": [
        Command.create({"product_id": han.id, "uom_id": han.uom_id.id, "method": "per_unit", "basis": "awb_kg",
                        "unit_price": 1.0, "line_direction": "import"}),
        Command.create({"product_id": han.id, "uom_id": han.uom_id.id, "method": "per_unit", "basis": "awb_kg",
                        "unit_price": 2.0, "line_direction": "export"}),
        Command.create({"product_id": tte.id, "uom_id": tte.uom_id.id, "method": "per_unit", "basis": "line",
                        "unit_price": 10.0, "line_state_ids": [Command.set(madrid.ids)]}),
        Command.create({"product_id": tte.id, "uom_id": tte.uom_id.id, "method": "per_unit", "basis": "line",
                        "unit_price": 20.0, "line_state_ids": [Command.set(valencia.ids)]}),
    ]})
base = {"transport_mode": "air", "load_type": "air", "port_id": mad.id, "tariff_use": "real", "line_qty": 1,
        "supplier_id": supplier.id, "awb_kg": 100.0, "country_id": ref("base.cn").id}
day = date(2026, 11, 16)


def cost(product, **kw):
    res = env["boss.pricing"].price_cost(product, product.uom_id, dict(base, **kw), day, simulate=tariff)  # noqa: F821
    return round(res.amount, 2) if res.status == "ok" else res.status


check("HAN import uses the import section", 100.0, cost(han, direction="import"))
check("HAN export uses the export section", 200.0, cost(han, direction="export"))
check("TTE-CON Madrid province", 10.0, cost(tte, direction="import", state_id=madrid.id))
check("TTE-CON Valencia province", 20.0, cost(tte, direction="import", state_id=valencia.id))
check("TTE-CON other province", "no_tariff",
      cost(tte, direction="import", state_id=env["res.country.state"].search(  # noqa: F821
          [("country_id.code", "=", "ES"), ("code", "=", "Z")], limit=1).id))
check("checklist: no overlap between the sections", False, "would conflict" in (tariff.ws_checklist or ""))
check("price list shows the line scope", True, "Exportación" in tariff.with_context(lang="es_ES").line_ids[1].scope_display
      or "Export" in tariff.line_ids[1].scope_display)
tariff.line_ids = [Command.create({"product_id": han.id, "uom_id": han.uom_id.id, "method": "per_unit",
                                   "basis": "awb_kg", "unit_price": 3.0})]
tariff.invalidate_recordset(["ws_checklist"])
check("checklist reports an overlapping price", True, "would conflict" in (tariff.ws_checklist or ""))
try:
    with env.cr.savepoint():  # noqa: F821
        tariff.line_ids[0].line_port_ids = [Command.set(env["boss.port"].search([("code", "=", "BCN")]).ids)]  # noqa: F821
        tariff.line_ids[0]._check_line_scope()
    widened = "accepted"
except ValidationError:
    widened = "refused"
check("a price cannot widen its tariff (BCN outside MAD)", "refused", widened)
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
