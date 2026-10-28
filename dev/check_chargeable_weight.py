"""Check of the chargeable weight rules confirmed by Ángel (Teams, 27/10/2026; ADR-006 amendment) on boss20: volume
weight = m³ × factor of the mode (air 167, road 333, sea 1000), chargeable = the higher of gross and volume weight;
suppliers charge BOSS on it (engine, buying) and BOSS charges its customers on it (line quantity, selling) when the
charge basis is weight-based; other bases (container, shipment) keep theirs; unknown measures are never 0. Every record
is made here and rolled back.    dev/uat_run.sh check_chargeable_weight.py boss20"""
from datetime import date

from odoo import Command
from odoo.tools.binary import BinaryBytes

from odoo.addons.boss_pricing_sale.models.boss_shipment_route import MODE_VOLUMETRIC_FACTORS, chargeable_kg

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


ref = env.ref
P, U = env["product.product"], env["uom.uom"]
product = lambda code: P.search([("default_code", "=", code)], limit=1)  # noqa: E731
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
check("factors of the three modes", {"air": 167, "road": 333, "sea": 1000}, MODE_VOLUMETRIC_FACTORS)

# 1. the shared function: real > volumetric, volumetric > real, equal, missing measures, unknown mode
check("air: real heavier (500 kg, 2 m3 -> 334)", (334.0, 500.0), chargeable_kg("air", 500, 2))
check("air: volume heavier (100 kg, 2 m3 -> 334)", (334.0, 334.0), chargeable_kg("air", 100, 2))
check("air: equal (167 kg, 1 m3)", (167.0, 167.0), chargeable_kg("air", 167, 1))
check("road: real heavier (1000 kg, 2 m3 -> 666)", (666.0, 1000.0), chargeable_kg("road", 1000, 2))
check("road: volume heavier (500 kg, 2 m3 -> 666)", (666.0, 666.0), chargeable_kg("road", 500, 2))
check("road: equal (333 kg, 1 m3)", (333.0, 333.0), chargeable_kg("road", 333, 1))
check("sea: real heavier (3000 kg, 2 m3 -> 2000)", (2000.0, 3000.0), chargeable_kg("sea", 3000, 2))
check("sea: volume heavier (1500 kg, 2 m3 -> 2000)", (2000.0, 2000.0), chargeable_kg("sea", 1500, 2))
check("sea: equal (1000 kg, 1 m3)", (1000.0, 1000.0), chargeable_kg("sea", 1000, 1))
check("volume unknown: nothing assumed", (0.0, 0.0), chargeable_kg("air", 500, 0))
check("gross unknown: nothing assumed", (0.0, 0.0), chargeable_kg("road", 0, 2))
check("mode unknown: nothing assumed", (0.0, 0.0), chargeable_kg(False, 500, 2))

# 2. a road quotation: the line quantity (selling) and the supplier cost (buying) on the chargeable weight
customer = env["res.partner"].create({"name": "[PRUEBA] Peso tasable S.L.", "is_company": True,
                                      "country_id": ref("base.es").id, "vat": "ESB12345674"})
supplier = env["res.partner"].create({"name": "[PRUEBA] Transportista tasable", "is_company": True,
                                      "country_id": ref("base.es").id})
road_uom = U.with_context(lang="es_ES").search([("name", "=", "kg tasable terrestre")], limit=1)
check("road charge basis exists", True, bool(road_uom))
road_uom.boss_quantity_source = "chargeable_road_kg"  # the data change of dev/setup_chargeable_uom.py
tte = product("TTE-CON")
zaragoza = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "Z")], limit=1)
# supplier price per chargeable kg WITHOUT a factor in the document: the mode factor applies (road 333)
tariff = env["boss.tariff"].create({
    "name": "[PRUEBA] transporte por kg tasable", "partner_id": supplier.id, "valid_from": date(2026, 1, 1),
    "scope_confirmed": True,  # no mode in the scope: a haulier serves road, air and sea shipments (IRENEO)
    "document": BinaryBytes(b"[PRUEBA] tarifa por kg tasable", filename="tarifa.txt"), "document_name": "tarifa.txt",
    "line_ids": [Command.create({"product_id": tte.id, "uom_id": road_uom.id, "method": "per_unit",
                                 "basis": "chargeable_kg", "unit_price": 0.10})]})
order = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "export", "boss_transport_mode": "road", "boss_load_type": "road",
    "boss_origin_country_id": ref("base.es").id, "boss_destination_country_id": ref("base.fr").id,
    "boss_inland_state_id": zaragoza.id, "boss_etd": date(2026, 11, 16),
    "boss_gross_kg": 500.0, "boss_volume_m3": 2.0,
    "order_line": [Command.create({"product_id": tte.id, "product_uom_id": road_uom.id, "price_unit": 0.20,
                                   "boss_supplier_id": supplier.id})]})
line = order.order_line
line.price_unit = 0.20  # the sale price typed by the salesperson (per chargeable kg)
check("road quotation: volume weight 2 x 333, chargeable 666 (volume heavier)", (666.0, 666.0),
      (order.boss_volume_weight_kg, order.boss_chargeable_kg))
check("selling: line quantity = chargeable weight", 666.0, line.product_uom_qty)
check("selling: amount = 666 kg x 0.20", 133.2, round(line.price_subtotal, 2))
check("buying: no cost while the price waits for approval", "pending_approval", line.boss_cost_status)
tariff.action_submit()
tariff.with_user(env["res.users"].search([("login", "=", "devbms")], limit=1)).action_approve()
line._boss_recompute_cost()
check("buying: cost = 666 kg x 0.10 with the mode factor", ("ok", 66.6), (line.boss_cost_status, round(line.boss_cost_amount, 2)))
check("buying: the explanation names the factor of the mode", True, "333" in (line.boss_cost_explanation or "") and "666" in (line.boss_cost_explanation or ""))
order.boss_gross_kg = 900.0  # real heavier now
check("quantity update: gross 900 > volume 666 -> chargeable 900", (900.0, 900.0), (order.boss_chargeable_kg, line.product_uom_qty))
check("quantity update: cost follows (900 x 0.10)", 90.0, round(line.boss_cost_amount, 2))
order.boss_volume_m3 = 0.0  # a measure unknown
check("volume unknown: chargeable not assumed", 0.0, order.boss_chargeable_kg)
check("volume unknown: supplier cost asks for the measures, no zero", ("missing_input", 0.0),
      (line.boss_cost_status, round(line.boss_cost_amount, 2)))
check("volume unknown: the line quantity stays as it was (not 0)", 900.0, line.product_uom_qty)
order.boss_volume_m3 = 2.0
# a document that states its own factor keeps it (IRENEO 333 on an air quotation, ADR-002): engine params win
tariff.line_ids.volumetric_factor = 500.0
line._boss_recompute_cost()
check("document factor stated (500): used instead of the mode factor -> 2 x 500 = 1000 kg x 0.10", 100.0, round(line.boss_cost_amount, 2))

# 3. air and sea quotations: chargeable weight computed; FCL untouched (per container, no weights)
air = env["sale.order"].create({"partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "air",
                                "boss_load_type": "air", "boss_gross_kg": 100.0, "boss_volume_m3": 2.0})
check("air quotation: 2 x 167 = 334 > 100", (334.0, 334.0), (air.boss_volume_weight_kg, air.boss_chargeable_kg))
check("air: AWB weight for air handlers = chargeable until the AWB is known", 334.0, air._boss_awb_weight())
sea = env["sale.order"].create({"partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea",
                                "boss_load_type": "lcl", "boss_gross_kg": 1500.0, "boss_volume_m3": 2.0})
check("sea LCL quotation: 2 x 1000 = 2000 > 1500", (2000.0, 2000.0), (sea.boss_volume_weight_kg, sea.boss_chargeable_kg))
check("sea: W/M basis agrees (2 m3 vs 1.5 t -> 2)", 2.0, sea._boss_quantity("wm"))
fcl = env["sale.order"].create({"partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea",
                                "boss_load_type": "fcl",
                                "boss_container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_dv").id, "quantity": 2})],
                                "order_line": [Command.create({"product_id": product("THC").id, "product_uom_id": product("THC").uom_id.id})]})
check("FCL without weights: per-container quantity 2, no chargeable weight needed", (2.0, 0.0),
      (fcl.order_line.product_uom_qty, fcl.boss_chargeable_kg))
check("per-shipment basis unchanged", 1.0, fcl._boss_quantity("shipment"))

# 4. the file keeps the same rule, with its own measures completed later
file = env["boss.expediente"].create({"partner_id": customer.id, "direction": "export", "transport_mode": "road",
                                      "load_type": "road"})
check("file without measures: nothing assumed", 0.0, file.chargeable_kg)
file.write({"gross_kg": 500.0, "volume_m3": 2.0})
check("file measures completed later: 666", (666.0, 666.0), (file.volume_weight_kg, file.chargeable_kg))
check("file quantity for a chargeable basis", 666.0, file._boss_quantity("chargeable_kg"))
# 6. the road leg of a SEA import is charged with the road factor (333), both selling and buying
sea_road = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "lcl",
    "boss_origin_country_id": ref("base.cn").id, "boss_destination_country_id": ref("base.es").id,
    "boss_inland_state_id": zaragoza.id, "boss_eta": date(2026, 11, 16), "boss_gross_kg": 500.0, "boss_volume_m3": 2.0,
    "order_line": [Command.create({"product_id": tte.id, "product_uom_id": road_uom.id, "boss_supplier_id": supplier.id})]})
sr = sea_road.order_line
check("sea import, road delivery: shipment chargeable uses sea (2000) but the road line uses road (666)",
      (2000.0, 666.0), (sea_road.boss_chargeable_kg, sr.product_uom_qty))
tariff.line_ids.volumetric_factor = 0.0
sr._boss_recompute_cost()
check("sea import, road delivery: supplier price per chargeable kg without factor uses the road factor (666 x 0.10)",
      ("ok", 66.6), (sr.boss_cost_status, round(sr.boss_cost_amount, 2)))

# 5. history: accepted quotations keep their stored values
accepted = env["sale.order"].search([("state", "=", "sale"), ("boss_pricing_frozen", "=", True), ("boss_transport_mode", "=", "air")], limit=1)
if accepted:
    before = [(l.product_id.default_code, l.product_uom_qty, round(l.boss_cost_amount, 2), l.price_unit) for l in accepted.order_line.filtered("product_id")]
    accepted.order_line.invalidate_recordset()
    accepted.order_line._boss_recompute_cost()
    after = [(l.product_id.default_code, l.product_uom_qty, round(l.boss_cost_amount, 2), l.price_unit) for l in accepted.order_line.filtered("product_id")]
    check(f"{accepted.name}: frozen quantities, costs and prices unchanged", before, after)
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if len(results) - sum(results):  # a failed check fails the run (dev/uat_run.sh records the exit status)
    raise SystemExit(1)
