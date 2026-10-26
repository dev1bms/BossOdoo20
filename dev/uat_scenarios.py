"""boss20_uat: the quotation and file scenarios of Belal's mandate (26/10/2026) with EXPLICIT checks: each expected value
is computed here from the [DEMO] tariffs and compared with what the system did («CHECK PASS|FAIL»). Every run creates
its own records (tag «[UAT] escenarios <run>») and keeps them for the UI.
    dev/uat_run.sh uat_scenarios.py          (evidence with the tested commit in docs/evidencias/)
S1 sea FCL mixed 2x20' DV + 1x40' HC with the [DEMO] IMB FOB template and GLO-FUELEU per TEU
S2 LCL 1.8 t / 4.5 m3 with an eventual inspection (SOI): no [DEMO] LCL tariff -> missing price, never 0
S3 air export with the [DEMO] EAB template: no export tariff -> missing price
S4 missing / expired / conflicting tariffs (two approved BL prices of the same scope in December)
S5 air import accepted, then the file weight changes 500 -> 620 kg: cost recomputed, sale kept
S6 sea import with 12 days of demurrage: free days and tiers per container
S7 air import: handler of the airline at the airport, proposed and changed with the airline"""
from datetime import date, datetime

from odoo import Command

assert env.cr.dbname == "boss20_uat", env.cr.dbname  # noqa: F821
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES", tracking_disable=True))  # noqa: F821
RUN = datetime.now().strftime("%Y%m%d-%H%M%S")
TAG = f"[UAT] escenarios {RUN}"
SO, P = env["sale.order"], env["product.product"]
IMD = env["ir.model.data"]
results = []
MISSING = ("no_tariff", "pending_approval")


def check(name, expected, got, tol=0.005):
    if isinstance(expected, float) or isinstance(got, float):
        ok = got is not None and expected is not None and abs(float(got) - float(expected)) <= tol
    else:
        ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def xid(name):
    imd = IMD.search([("module", "=", "boss_trial"), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id).exists() if imd else None


def product(code):
    return P.search([("default_code", "=", code)], limit=1)


def lines(order, code, size=None):
    return order.order_line.filtered(lambda l: l.product_id.default_code == code
                                     and (size is None or l.boss_container_size == size))


def add(order, codes, **vals):
    env["boss.add.services"].create({"order_id": order.id, "product_ids": [Command.set([product(c).id for c in codes])],
                                     **vals}).action_add()


def template(order, name_start):
    order.sale_order_template_id = env["sale.order.template"].search([("name", "=like", name_start + "%")], limit=1)
    order._onchange_sale_order_template_id()


customer = xid("customer_eu")
msc, wfs_demo = xid("demo_msc").partner_id, xid("demo_wfs").partner_id
vlc, mad = env.ref("boss_pricing.port_esvlc"), env.ref("boss_pricing.port_esmad_air")
cn = env.ref("base.cn")
dv, hc = env.ref("boss_pricing.container_type_dv"), env.ref("boss_pricing.container_type_hc")
sea = {"partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
       "boss_carrier_id": msc.id, "boss_port_id": vlc.id, "boss_country_id": cn.id,
       "boss_planned_date": date(2026, 11, 10), "boss_storage_days": 0}

# S1 -----------------------------------------------------------------------------------------------------------------
s1 = SO.create(dict(sea, origin=f"{TAG} S1 FCL mixto", boss_container_ids=[
    Command.create({"size": "20", "container_type_id": dv.id, "quantity": 2}),
    Command.create({"size": "40", "container_type_id": hc.id, "quantity": 1})]))
template(s1, "[DEMO] IMB FOB")
add(s1, ["GLO-FUELEU"])
check("S1 THC 20' DV: 2 containers x 180", (2.0, 180.0, "ok"),
      (lines(s1, "THC", "20").product_uom_qty, lines(s1, "THC", "20").purchase_price, lines(s1, "THC", "20").boss_cost_status))
check("S1 THC 40' HC: 240 (the 300 € line is reefer only)", (1.0, 240.0), (lines(s1, "THC", "40").product_uom_qty,
                                                                          lines(s1, "THC", "40").purchase_price))
check("S1 BL 60 per file", (1.0, 60.0), (lines(s1, "BL").product_uom_qty, lines(s1, "BL").purchase_price))
check("S1 GLO-FUELEU TEU: 2 x 20' = 2 TEU and 1 x 40' = 2 TEU", [2.0, 2.0],
      sorted(lines(s1, "GLO-FUELEU").mapped("product_uom_qty")))
check("S1 GLO-FUELEU 25 €/TEU from the approved [DEMO] tariff", [25.0, 25.0],
      sorted(lines(s1, "GLO-FUELEU").mapped("purchase_price")))
for code in ("FAD", "GLO-CCC", "TTE-FCL"):
    check(f"S1 {code} without approved tariff: missing price, cost 0 not taken as free", True, all(
        l.boss_cost_status in MISSING and l.boss_cost_kind == "unknown" for l in lines(s1, code)))
check("S1 FMI freight: manual cost expected", True, all(l.boss_cost_status == "manual" for l in lines(s1, "FMI")))
check("S1 CSM done by BOSS: no supplier cost", ("ok", "boss"), (lines(s1, "CSM").boss_cost_status,
                                                                lines(s1, "CSM").boss_cost_kind))

# S2 -----------------------------------------------------------------------------------------------------------------
s2 = SO.create(dict(sea, origin=f"{TAG} S2 LCL + SOIVRE", boss_load_type="lcl", boss_gross_kg=1800.0,
                    boss_volume_m3=4.5))
add(s2, ["THC-LCL", "DOC", "FAD", "SOI"])
check("S2 THC-LCL quantity W/M = max(1.8 t, 4.5 m3)", 4.5, lines(s2, "THC-LCL").product_uom_qty)
check("S2 THC-LCL, DOC, FAD, SOI: missing price (no LCL tariff)", True,
      all(l.boss_cost_status in MISSING for l in s2.order_line))

# S3 -----------------------------------------------------------------------------------------------------------------
s3 = SO.create({"partner_id": customer.id, "origin": f"{TAG} S3 exportación aérea", "boss_direction": "export",
                "boss_transport_mode": "air", "boss_load_type": "air", "boss_carrier_id": wfs_demo.id,
                "boss_port_id": mad.id, "boss_country_id": env.ref("base.us").id, "boss_planned_date": date(2026, 11, 12),
                "boss_awb_kg": 350.0})
template(s3, "[DEMO] EAB")
check("S3 HAN quantity = AWB chargeable kg", 350.0, lines(s3, "HAN").product_uom_qty)
check("S3 TTE-CON, HAN, AWB, DEX: no export tariff -> missing", True, all(
    lines(s3, c).boss_cost_status in MISSING for c in ("TTE-CON", "HAN", "AWB", "DEX")))
check("S3 CSA by BOSS", "boss", lines(s3, "CSA").boss_cost_kind)

# S4 -----------------------------------------------------------------------------------------------------------------
conflict = env["boss.tariff"].search([("name", "=like", "[DEMO] MSC BL alternativo mismo alcance 12/2026%")], limit=1)
s4 = SO.create(dict(sea, origin=f"{TAG} S4 falta/caducada/conflicto", boss_planned_date=date(2026, 12, 15),
                    boss_container_ids=[Command.create({"size": "40", "container_type_id": dv.id, "quantity": 1})]))
add(s4, ["BL", "CES", "TTE-CON"])
check("S4 a second approved BL price of the same scope exists (December)", "approved", conflict.state)
check("S4 BL: conflict, no cost chosen", ("conflict", 0.0), (lines(s4, "BL").boss_cost_status,
                                                            lines(s4, "BL").purchase_price))
check("S4 CES and TTE-CON: missing price", True, all(lines(s4, c).boss_cost_status in MISSING for c in ("CES", "TTE-CON")))
s4b = s4.copy({"origin": f"{TAG} S4b noviembre", "boss_planned_date": date(2026, 11, 10)})
s4b.action_boss_update_costs()
check("S4b same quotation in November: only one BL price valid -> 60", ("ok", 60.0),
      (lines(s4b, "BL").boss_cost_status, lines(s4b, "BL").purchase_price))

# S5 -----------------------------------------------------------------------------------------------------------------
s5 = SO.create({"partner_id": customer.id, "origin": f"{TAG} S5 aéreo cambio de peso", "boss_direction": "import",
                "boss_transport_mode": "air", "boss_load_type": "air", "boss_carrier_id": wfs_demo.id,
                "boss_port_id": mad.id, "boss_country_id": cn.id, "boss_planned_date": date(2026, 11, 12),
                "boss_awb_kg": 500.0, "boss_storage_days": 0})
add(s5, ["HAN", "AWB"])
for l in s5.order_line:
    l.price_unit = {"HAN": 0.12, "AWB": 45.0}[l.product_id.default_code]
check("S5 HAN 500 kg x 0.05 (minimum 20 not reached) = 25", 25.0,
      lines(s5, "HAN").purchase_price * lines(s5, "HAN").product_uom_qty)
s5.action_confirm()
f5 = s5.boss_expediente_id
han = f5.cost_ids.filtered(lambda n: n.product_id.default_code == "HAN")
f5.awb_kg = 620.0
f5.action_recompute_costs()
han.invalidate_recordset()
check("S5 file 620 kg: HAN need 620 kg x 0.05 = 31", (620.0, 31.0), (han.quantity, han.expected_amount))
check("S5 one revision 25 -> 31", [(25.0, 31.0)], [(r.old_amount, r.new_amount) for r in han.revision_ids])
check("S5 accepted sale unchanged (0.12 €/kg)", 0.12, lines(s5, "HAN").price_unit)

# S6 -----------------------------------------------------------------------------------------------------------------
s6 = SO.create(dict(sea, origin=f"{TAG} S6 demoras 12 días", boss_storage_days=12, boss_container_ids=[
    Command.create({"size": "40", "container_type_id": dv.id, "quantity": 2})]))
add(s6, ["DEM", "THC"])
check("S6 DEM 12 days: 12 - 7 free = 5 x 30 (first tier) per container", (2.0, 150.0),
      (lines(s6, "DEM").product_uom_qty, lines(s6, "DEM").purchase_price))
check("S6 THC 40' DV 240", 240.0, lines(s6, "THC").purchase_price)

# S7 -----------------------------------------------------------------------------------------------------------------
Rel = env["boss.airline.handler"]
cathay = env["res.partner"].search([("name", "=", "Cathay Pacific Airways")], limit=1)
qatar = env["res.partner"].search([("name", "=", "Qatar Airways")], limit=1)
wfs = Rel._handlers_for(cathay, mad)
iberia = Rel._handlers_for(qatar, mad)
check("S7 data: Cathay at MAD -> WFS, Qatar at MAD -> Iberia (Odoo 17 HandlingConfig)", ("WFS", "Iberia (handling)"),
      (wfs.name, iberia.name))
s7 = SO.create({"partner_id": customer.id, "origin": f"{TAG} S7 handler", "boss_direction": "import",
                "boss_transport_mode": "air", "boss_load_type": "air", "boss_carrier_id": cathay.id,
                "boss_port_id": mad.id, "boss_country_id": cn.id, "boss_planned_date": date(2026, 11, 12),
                "boss_awb_kg": 300.0})
add(s7, ["HAN", "AWB", "CSA"])
check("S7 quotation: HAN and AWB bought from the only handler of Cathay at MAD", [wfs, wfs],
      [lines(s7, "HAN").boss_supplier_id, lines(s7, "AWB").boss_supplier_id])
for l in s7.order_line:
    l.price_unit = {"HAN": 0.1, "AWB": 40.0, "CSA": 50.0}[l.product_id.default_code]
    if l.boss_cost_kind == "unknown":
        l.boss_unknown_cost_reason = f"{TAG} sin tarifa real del handler en UAT"
s7.action_confirm()
f7 = s7.boss_expediente_id
check("S7 file: handler proposed (WFS)", wfs, f7.handler_id)
check("S7 needs bought from WFS", [wfs, wfs], [f7.cost_ids.filtered(lambda n, c=c: n.product_id.default_code == c).partner_id
                                             for c in ("HAN", "AWB")])
f7.write({"carrier_id": qatar.id, "handler_id": iberia.id})  # what the form proposes for Qatar (one handler at MAD)
check("S7 airline changed to Qatar: only handler offered = Iberia", iberia, f7.handler_candidate_ids)
check("S7 needs not ordered follow the new handler", [iberia, iberia],
      [f7.cost_ids.filtered(lambda n, c=c: n.product_id.default_code == c).partner_id for c in ("HAN", "AWB")])

passed, failed = results.count(True), results.count(False)
print(f"RESULT {passed} passed, {failed} failed | run {TAG} | " + ", ".join(
    o.name for o in (s1, s2, s3, s4, s4b, s5, s6, s7)) + f" | files {f5.name}, {f7.name}")
env.cr.commit()
if failed:
    raise SystemExit(1)
