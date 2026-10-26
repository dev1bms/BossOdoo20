"""boss20_uat only: the UI scenarios of Belal's mandate (26/10/2026) created as persistent [DEMO] records, with the
expected result computed here from the [DEMO] tariffs before reading what the system did. Idempotent (origin tag).
    BOSS_DB=boss20_uat dev/server_shell.sh uat_scenarios.py
S1 sea FCL mixed 2x20' DV + 1x40' HC, template [DEMO] IMB FOB + GLO-FUELEU per TEU (4 TEU)
S2 LCL with an eventual inspection (SOI): no [DEMO] LCL tariff -> missing price, never zero
S3 air export with the [DEMO] EAB template: no export tariff -> missing price
S4 missing / expired / conflicting tariffs on one quotation (TTE-CON on IRENEO 2025 expired; BL with two approved
   [DEMO] tariffs -> conflict)
S5 air import accepted, then the file weight changes 500 -> 620 kg: cost recomputed, sale kept
S6 sea import with 12 days of storage: DEM per container and day after the free days (MSC [DEMO] 7 free days)"""
from datetime import date

from odoo import Command
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname in ("boss20_uat", "boss20"), env.cr.dbname  # noqa: F821  (boss20: drafts + one accepted [DEMO] air order, no accounting)
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES", tracking_disable=True))  # noqa: F821
TAG = "[UAT] escenarios 26/10/2026"
SO, P, Tariff = env["sale.order"], env["product.product"], env["boss.tariff"]
IMD = env["ir.model.data"]


def xid(name):
    imd = IMD.search([("module", "=", "boss_trial"), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id).exists() if imd else None


def product(code):
    return P.search([("default_code", "=", code)], limit=1)


def ctype(code):
    return env["boss.container.type"].search([("code", "=", code)], limit=1)


def lines(order):
    return [(l.product_id.default_code, l.boss_container_size or "", round(l.product_uom_qty, 2), l.product_uom_id.name,
             l.boss_cost_status, round(l.purchase_price or 0.0, 2), round(l.price_unit, 2)) for l in order.order_line
            if not l.display_type]


def add(order, codes, **vals):
    env["boss.add.services"].create({"order_id": order.id, "product_ids": [Command.set([product(c).id for c in codes])],
                                     **vals}).action_add()


def template(order, name_start):
    tpl = env["sale.order.template"].search([("name", "=like", name_start + "%")], limit=1)
    assert tpl, name_start
    order.sale_order_template_id = tpl
    order._onchange_sale_order_template_id()


def report(label, order, expected):
    print(f"\n== {label}: {order.name} ({order.state})")
    print("   expected:", expected)
    print("   actual:  ", lines(order))
    print("   cost total (purchase_price x qty):", round(sum(l.purchase_price * l.product_uom_qty for l in order.order_line), 2))


if SO.search_count([("origin", "=like", TAG + "%")]):
    print("ALREADY RUN:", [(o.name, o.origin, o.state) for o in SO.search([("origin", "=like", TAG + "%")], order="id")])
    raise SystemExit(0)

customer_eu, msc = xid("customer_eu"), xid("demo_msc").partner_id
wfs = xid("demo_wfs").partner_id
vlc, mad = env.ref("boss_pricing.port_esvlc"), env.ref("boss_pricing.port_esmad_air")
cn = env.ref("base.cn")
dv, hc = ctype("DV"), ctype("HC")
print("DATA", customer_eu.name, "|", msc.name, "|", wfs.name, "| DV", bool(dv), "HC", bool(hc))

# A [DEMO] tariff for the TEU charge (fictitious, approved here because every [DEMO] tariff is)
teu = product("GLO-FUELEU")
fueleu = Tariff.search([("name", "=", "[DEMO] MSC FuelEU por TEU 2026")], limit=1)
if not fueleu and teu:
    fueleu = Tariff.create({
        "name": "[DEMO] MSC FuelEU por TEU 2026", "partner_id": msc.id, "currency_id": env.company.currency_id.id,
        "valid_from": date(2026, 1, 1), "valid_to": date(2026, 12, 31), "direction": "import", "transport_mode": "sea",
        "load_type": "fcl", "carrier_id": msc.id, "is_demo": True, "scope_confirmed": True,
        "document_reference": "[DEMO] tarifa ficticia para la prueba del TEU", "document_name": "demo.txt",
        "document": BinaryBytes(b"DEMO", filename="demo.txt"), "country_ids": [Command.set(cn.ids)],
        "line_ids": [Command.create({"product_id": teu.id, "uom_id": teu.uom_id.id, "method": "per_unit",
                                     "basis": "teu", "unit_price": 25.0})]})
    fueleu.action_submit()
    fueleu.action_approve()
print("TEU tariff", fueleu.name if fueleu else "GLO-FUELEU product missing", fueleu.state if fueleu else "")

# S1 sea FCL mixed 2x20' DV + 1x40' HC
s1 = SO.create({
    "partner_id": customer_eu.id, "origin": f"{TAG} S1 FCL mixto 2x20'+1x40'HC", "boss_direction": "import",
    "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": msc.id, "boss_port_id": vlc.id,
    "boss_country_id": cn.id, "boss_planned_date": date(2026, 11, 10), "boss_storage_days": 0,
    "boss_container_ids": [Command.create({"size": "20", "container_type_id": dv.id, "quantity": 2}),
                           Command.create({"size": "40", "container_type_id": hc.id, "quantity": 1})]})
template(s1, "[DEMO] IMB FOB")
add(s1, ["GLO-FUELEU"])
report("S1 FCL mixto", s1, "THC 20' qty 2 x 180 = 360 (ok) · THC 40' HC qty 1 x 300 (ok) · BL 1 x 60 (ok) · "
       "GLO-FUELEU 4 TEU x 25 = 100 (ok) · DEM 0 days (ok, 0) · FMI/FAD/TTE-FCL: no approved [DEMO] tariff "
       "(no_tariff or pending_approval, never 0 as free) · CSM by BOSS (ok, 0)")

# S2 LCL + eventual inspection
s2 = SO.create({
    "partner_id": customer_eu.id, "origin": f"{TAG} S2 LCL + inspección SOIVRE", "boss_direction": "import",
    "boss_transport_mode": "sea", "boss_load_type": "lcl", "boss_carrier_id": msc.id, "boss_port_id": vlc.id,
    "boss_country_id": cn.id, "boss_planned_date": date(2026, 11, 10), "boss_gross_kg": 1800.0,
    "boss_volume_m3": 4.5})
add(s2, ["THC-LCL", "DOC", "FAD", "SOI"])
report("S2 LCL + SOI", s2, "THC-LCL (max of 1.8 t / 4.5 m3): no [DEMO] LCL tariff -> no_tariff · DOC/FAD/SOI -> "
       "no_tariff; every line shows the «add supplier price» action, no 0 cost")

# S3 air export with the EAB template
s3 = SO.create({
    "partner_id": customer_eu.id, "origin": f"{TAG} S3 exportación aérea EAB", "boss_direction": "export",
    "boss_transport_mode": "air", "boss_load_type": "air", "boss_carrier_id": wfs.id, "boss_port_id": mad.id,
    "boss_country_id": env.ref("base.us").id, "boss_planned_date": date(2026, 11, 12), "boss_awb_kg": 350.0})
template(s3, "[DEMO] EAB")
report("S3 export aéreo", s3, "TTE-CON, HAN, AWB, DEX, FAE: no export [DEMO] tariff -> no_tariff · CSA by BOSS (ok, 0)")

# S4 missing / expired / conflicting
bl = product("BL")
other = Tariff.search([("name", "=", "[DEMO] MSC BL alternativo 2026 (conflicto)")], limit=1)
if not other:
    other = Tariff.create({
        "name": "[DEMO] MSC BL alternativo 2026 (conflicto)", "partner_id": msc.id, "carrier_id": msc.id,
        "currency_id": env.company.currency_id.id, "valid_from": date(2026, 1, 1), "valid_to": date(2026, 12, 31),
        "direction": "import", "transport_mode": "sea", "load_type": "fcl", "is_demo": True, "scope_confirmed": True,
        "document_reference": "[DEMO] segunda tarifa ficticia del BL para provocar un conflicto",
        "document_name": "demo.txt", "document": BinaryBytes(b"DEMO", filename="demo.txt"),
        "line_ids": [Command.create({"product_id": bl.id, "uom_id": bl.uom_id.id, "method": "per_unit",
                                     "basis": "line", "unit_price": 70.0})]})
    other.action_submit()
    other.action_approve()
s4 = SO.create({
    "partner_id": customer_eu.id, "origin": f"{TAG} S4 tarifas: falta, caducada, conflicto", "boss_direction": "import",
    "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": msc.id, "boss_port_id": vlc.id,
    "boss_country_id": cn.id, "boss_planned_date": date(2026, 11, 10),
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": dv.id, "quantity": 1})]})
add(s4, ["BL", "CES"])
ireneo = Tariff.search([("name", "=like", "[MUESTRA] IRENEO distribución nacional zona 3 2025%")], limit=1)
add(s4, ["TTE-CON"], supplier_id=ireneo.partner_id.id if ireneo else False)
report("S4 falta / caducada / conflicto", s4,
       "BL: two approved [DEMO] tariffs (60 and 70) -> conflict, no cost chosen · CES: no tariff -> no_tariff · "
       "TTE-CON IRENEO: 2025 tariff expired and waiting for approval -> pending_approval/no_tariff (never applied)")

# S5 air import accepted, then the weight changes on the file
s5 = SO.create({
    "partner_id": customer_eu.id, "origin": f"{TAG} S5 aéreo: cambio de peso tras aceptar", "boss_direction": "import",
    "boss_transport_mode": "air", "boss_load_type": "air", "boss_carrier_id": wfs.id, "boss_port_id": mad.id,
    "boss_country_id": cn.id, "boss_planned_date": date(2026, 11, 12), "boss_awb_kg": 500.0, "boss_storage_days": 0})
add(s5, ["HAN", "AWB"])
for line in s5.order_line:
    line.price_unit = {"HAN": 0.12, "AWB": 45.0}[line.product_id.default_code]
report("S5 before acceptance", s5, "HAN 500 kg x 0.05 = 25 (min 20) sale 0.12 x 500 = 60 · AWB 30 cost, 45 sale")
s5.action_confirm()
f5 = s5.boss_expediente_id
han_need = f5.cost_ids.filtered(lambda n: n.product_id.default_code == "HAN")
before = (han_need.quantity, han_need.expected_amount)
f5.awb_kg = 620.0
f5.action_recompute_costs()
han_need.invalidate_recordset()
print(f"\n== S5 file {f5.name}: HAN need before {before} -> after 620 kg {(han_need.quantity, han_need.expected_amount)}"
      f" | expected (500.0, 25.0) -> (620.0, 31.0) | sale line kept at",
      s5.order_line.filtered(lambda l: l.product_id.default_code == 'HAN').price_unit, "(expected 0.12)",
      "| revisions:", [(r.old_amount, r.new_amount) for r in f5.revision_ids])

# S6 storage: DEM per container and day after the free days
s6 = SO.create({
    "partner_id": customer_eu.id, "origin": f"{TAG} S6 demoras 12 días", "boss_direction": "import",
    "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": msc.id, "boss_port_id": vlc.id,
    "boss_country_id": cn.id, "boss_planned_date": date(2026, 11, 10), "boss_storage_days": 12,
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": dv.id, "quantity": 2})]})
add(s6, ["DEM", "THC"])
dem_line = env["boss.tariff.line"].search([("tariff_id.name", "=", "[DEMO] MSC gastos locales importación Valencia 2026"),
                                           ("product_id.default_code", "=", "DEM")], limit=1)
print("\n   DEM [DEMO] rule:", dem_line.free_days, "free days, free_mode", dem_line.free_mode, "period", dem_line.period_unit,
      "tiers", [(b.up_to, b.unit_price, b.fixed_amount) for b in dem_line.bracket_ids], "unit_price", dem_line.unit_price)
report("S6 DEM 12 días x 2 cntr", s6, "DEM: 12 days - 7 free = 5 chargeable days x 2 containers x tier price "
       "(see rule above) · THC 40' DV 2 x 240 = 480")
env.cr.commit()
print("\nCOMMITTED on boss20_uat:", [(o.name, o.origin) for o in (s1 | s2 | s3 | s4 | s5 | s6)])
