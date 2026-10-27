"""Check of ADR-006 on boss20 with the cases of the meeting with Ángel (27/10/2026): sea import FCL from Shanghai to a
warehouse in Madrid through Valencia (template «IMB FOB»), sea export from Zaragoza through Barcelona to Tunis, air
import without AWB (chargeable weight 167 kg/m³), agent's client, the file and the opportunity, a cross-trade and a
national shipment (no Spain forced, key date never the unloading date). Every record is made
here and rolled back. Prints «CHECK PASS|FAIL …» and «RESULT n passed, m failed».
    dev/uat_run.sh check_route_cases.py boss20"""
from datetime import date

from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


ref = env.ref
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
state = lambda code: env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", code)], limit=1)  # noqa: E731
template = lambda code: env["sale.order.template"].search([("name", "=like", f"{code} · %")], limit=1)  # noqa: E731
Partner = env["res.partner"]
customer = Partner.create({"name": "[PRUEBA] Ordenante ADR-006", "is_company": True, "country_id": ref("base.es").id})
warehouse = Partner.create({"name": "[PRUEBA] Almacén Madrid", "parent_id": customer.id, "type": "delivery",
                            "city": "Getafe", "state_id": state("M").id, "country_id": ref("base.es").id})
zaragoza = Partner.create({"name": "[PRUEBA] Almacén Zaragoza", "parent_id": customer.id, "type": "delivery",
                           "city": "Zaragoza", "state_id": state("Z").id, "country_id": ref("base.es").id})
msc = Partner.search([("name", "=", "MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.")], limit=1)
check("ports abroad loaded (Shanghai, Tunis, Ningbo)", 3, len(port("CNSHA", "sea") | port("TNTUN", "sea")
                                                              | port("CNNGB", "sea")))

# E1 sea import FCL from the template: the template fills the case, the route gives the pricing inputs
with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.sale_order_template_id = template("IMB FOB")
    case = (form.boss_direction, form.boss_transport_mode, form.boss_load_type, form.incoterm.code, form.boss_business)
    check("E1 template fills the case", ("import", "sea", "fcl", "FOB", "boss"), case)
    check("E1 template fills what BOSS handles", (False, False, True, True, True),
          (form.boss_scope_pickup, form.boss_scope_origin_customs, form.boss_scope_main,
           form.boss_scope_destination_customs, form.boss_scope_delivery))
    check("E1 Spanish side is Spain (destination of an import)", "ES", form.boss_destination_country_id.code)
    form.boss_carrier_id = msc
    form.boss_origin_country_id = ref("base.cn")
    form.boss_origin_port_id = port("CNSHA", "sea")
    form.boss_destination_port_id = port("ESVLC", "sea")
    form.boss_delivery_address_id = warehouse
    form.boss_etd = date(2026, 11, 10)
    form.boss_eta = date(2026, 12, 10)
    with form.boss_container_ids.new() as container:
        container.size = "40"
        container.container_type_id = ref("boss_pricing.container_type_hc")
imb = form.save()
check("E1 traffic code", "IMB", imb.boss_traffic_code)
check("E1 Spanish port = destination port", "ESVLC", imb.boss_port_id.code)
check("E1 country abroad = origin country", "CN", imb.boss_country_id.code)
check("E1 province from the delivery address", "M", imb.boss_inland_state_id.code)
check("E1 destination place from the address", "Getafe", imb.boss_destination_place)
check("E1 tariff date = ETA (import)", date(2026, 12, 10), imb.boss_planned_date)
check("E1 storage estimate 0 days, indicated", (0, True), (imb.boss_storage_days, imb.boss_storage_days_known))
# same costs as a quotation with the same pricing inputs typed directly (the old way): the route changes no price
legacy = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_carrier_id": msc.id, "boss_port_id": port("ESVLC", "sea").id, "boss_country_id": ref("base.cn").id,
    "boss_inland_state_id": state("M").id, "boss_planned_date": date(2026, 12, 10),
    "boss_container_ids": [(0, 0, {"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id})],
    "order_line": [(0, 0, {"product_id": l.product_id.id, "product_uom_id": l.product_uom_id.id,
                           "boss_container_size": l.boss_container_size,
                           "boss_container_type_id": l.boss_container_type_id.id}) for l in imb.order_line]})
costs = lambda o: [(l.product_id.default_code, l.boss_cost_status, round(l.boss_cost_amount, 2)) for l in o.order_line]  # noqa: E731
check("E1 costs equal to the same inputs typed directly", costs(legacy), costs(imb))
check("E1 MSC THC priced from the route (ESVLC, China)", ("ok", 253.0),
      next((s, a) for c, s, a in costs(imb) if c == "THC"))
print("   E1 lines:", costs(imb))

# E2 sea export: pickup in Zaragoza, Barcelona -> Tunis; the side abroad is never Spain
with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.boss_direction = "export"
    form.boss_transport_mode = "sea"
    form.boss_load_type = "fcl"
    check("E2 Spanish side is Spain (origin of an export)", "ES", form.boss_origin_country_id.code)
    form.boss_pickup_address_id = zaragoza
    form.boss_origin_port_id = port("ESBCN", "sea")
    form.boss_destination_country_id = ref("base.tn")
    form.boss_destination_port_id = port("TNTUN", "sea")
    form.boss_etd = date(2026, 11, 20)
    form.boss_eta = date(2026, 11, 25)
    form.boss_destination_country_id = ref("base.es")
    form.boss_direction = "import"
    form.boss_direction = "export"
    check("E2 the side abroad cannot be Spain", False, bool(form.boss_destination_country_id))
    form.boss_destination_country_id = ref("base.tn")
exp = form.save()
check("E2 traffic code", "EMB", exp.boss_traffic_code)
check("E2 Spanish port = origin port", "ESBCN", exp.boss_port_id.code)
check("E2 country abroad = destination country", "TN", exp.boss_country_id.code)
check("E2 province from the pickup address", "Z", exp.boss_inland_state_id.code)
check("E2 tariff date = ETD (export)", date(2026, 11, 20), exp.boss_planned_date)

# E3 air import without AWB: chargeable weight = max(gross, volume x 167)
with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.sale_order_template_id = template("IAB FOB")
    form.boss_origin_country_id = ref("base.cn")
    form.boss_origin_port_id = port("PVG", "air")
    form.boss_destination_port_id = port("MAD", "air")
    form.boss_eta = date(2026, 11, 16)
    form.boss_gross_kg = 500
    form.boss_volume_m3 = 4
air = form.save()
check("E3 traffic code", "IAB", air.boss_traffic_code)
check("E3 volume weight 4 m3 x 167", 668.0, air.boss_volume_weight_kg)
check("E3 chargeable weight = higher", 668.0, air.boss_chargeable_kg)
check("E3 pricing AWB weight = estimate", 668.0, air._boss_shipment_inputs()["awb_kg"])
han = air.order_line.filtered(lambda l: l.product_id.default_code == "HAN")
check("E3 HAN quantity on the chargeable weight", 668.0, han.product_uom_qty)
wfs = env["boss.tariff"].search([("name", "=", "WFS Tarifas MAD/BCN desde 01/06/2026")], limit=1)
res = env["boss.pricing"].price_cost(han.product_id, han.product_uom_id,
                                    dict(han._boss_inputs(), supplier_id=wfs.partner_id.id),
                                    air.boss_planned_date, simulate=wfs)
check("E3 WFS HAN import on 668 kg (simulated, tariff waiting approval) = 668 x 0.05", ("ok", 33.4),
      (res.status, round(res.amount, 2)))
air.boss_awb_kg = 700
check("E3 the AWB weight wins when known", 700.0, air._boss_shipment_inputs()["awb_kg"])
air.boss_gross_kg, air.boss_volume_m3, air.boss_awb_kg = 900, 2, 0
check("E3 dense cargo: chargeable = gross", 900.0, air.boss_chargeable_kg)

# E4 agent's client
imb.boss_business = "agent"
check("E4 traffic code of an agent's client", "IMA", imb.boss_traffic_code)

# E5 file: receives the route, dates and business, derives the same pricing inputs
values = imb._boss_file_values()
file = env["boss.expediente"].create(values)
check("E5 file route", ("CNSHA", "ESVLC", warehouse, "agent", "IMA"),
      (file.origin_port_id.code, file.destination_port_id.code, file.delivery_address_id, file.business,
       file.traffic_code))
check("E5 file dates", (date(2026, 11, 10), date(2026, 12, 10)), (file.etd, file.eta))
check("E5 file pricing inputs", ("ESVLC", "CN", "M"), (file.port_id.code, file.country_id.code,
                                                       file.inland_state_id.code))
file.destination_port_id = port("ESBCN", "sea")
check("E5 file: changing the destination port changes the Spanish port", "ESBCN", file.port_id.code)

# E6 opportunity: the quotation receives the route once
lead = env["crm.lead"].create({
    "name": "[PRUEBA] Oportunidad ADR-006", "type": "opportunity", "partner_id": customer.id,
    "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNNGB", "sea").id,
    "boss_destination_country_id": ref("base.es").id, "boss_destination_port_id": port("ESVLC", "sea").id,
    "boss_delivery_address_id": warehouse.id, "boss_eta": date(2026, 12, 1)})
check("E6 opportunity traffic and pricing inputs", ("IMB", "ESVLC", "CN", "M"),
      (lead.boss_traffic_code, lead.boss_port_id.code, lead.boss_country_id.code, lead.boss_inland_state_id.code))
ctx = lead._prepare_opportunity_quotation_context()
from_lead = env["sale.order"].with_context(**ctx).create({"partner_id": customer.id})
check("E6 quotation from the opportunity", ("CNNGB", "ESVLC", "CN", "M", date(2026, 12, 1)),
      (from_lead.boss_origin_port_id.code, from_lead.boss_port_id.code, from_lead.boss_country_id.code,
       from_lead.boss_inland_state_id.code, from_lead.boss_planned_date))

# E8 cross-trade: Shanghai -> Rotterdam, Spain is not a party and is not forced; only unscoped tariffs; VAT TER->TER
rotterdam = port("NLRTM", "sea") or env["boss.port"].search([("country_id.code", "=", "NL"), ("kind", "=", "sea")], limit=1)
with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.boss_direction = "cross"
    form.boss_transport_mode = "sea"
    form.boss_load_type = "fcl"
    check("E8 cross-trade: no country proposed", (False, False),
          (bool(form.boss_origin_country_id), bool(form.boss_destination_country_id)))
    form.boss_origin_country_id = ref("base.cn")
    form.boss_origin_port_id = port("CNSHA", "sea")
    form.boss_destination_country_id = rotterdam.country_id
    form.boss_destination_port_id = rotterdam
    form.boss_etd = date(2026, 11, 20)
    form.boss_eta = date(2026, 12, 15)
    with form.order_line.new() as line:
        line.product_id = env["product.product"].search([("default_code", "=", "FAD")], limit=1)
cross = form.save()
check("E8 traffic code", "XMB", cross.boss_traffic_code)
check("E8 sides kept as typed (CN -> NL)", ("CN", "NL"),
      (cross.boss_origin_country_id.code, cross.boss_destination_country_id.code))
check("E8 no Spanish port, no country abroad for tariffs", (False, False), (bool(cross.boss_port_id), bool(cross.boss_country_id)))
check("E8 no port abroad for tariffs either", False, bool(cross._boss_foreign_port()))
check("E8 key date = ETD, never an unloading date", date(2026, 11, 20), cross.boss_planned_date)
fad = cross.order_line.filtered(lambda l: l.product_id.default_code == "FAD")
check("E8 VAT from the route: China (TER) -> Netherlands (COM) is an NR pair, Spanish customer -> NR", "NR", fad.boss_vat_class)
check("E8 orderer not proposed as a party of a cross-trade", (False, False), (bool(cross.boss_shipper_id), bool(cross.boss_consignee_id)))

# E9 national: Zaragoza -> Madrid by road, both sides Spain, province from the delivery address, VAT PRO->PRO -> NR
with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.boss_direction = "national"
    form.boss_transport_mode = "road"
    form.boss_load_type = "road"
    check("E9 national: both sides proposed as Spain", ("ES", "ES"),
          (form.boss_origin_country_id.code, form.boss_destination_country_id.code))
    form.boss_pickup_address_id = zaragoza
    form.boss_delivery_address_id = warehouse
    form.boss_etd = date(2026, 11, 20)
    form.boss_gross_kg = 500
    form.boss_volume_m3 = 2
    with form.order_line.new() as line:
        line.product_id = env["product.product"].search([("default_code", "=", "FAD")], limit=1)
national = form.save()
check("E9 traffic code", "NTB", national.boss_traffic_code)
check("E9 no country abroad; no Spanish port without ports", (False, False), (bool(national.boss_country_id), bool(national.boss_port_id)))
check("E9 province from the delivery address", "M", national.boss_inland_state_id.code)
check("E9 key date = ETD", date(2026, 11, 20), national.boss_planned_date)
check("E9 road chargeable weight 2 m3 x 333 = 666 > 500", 666.0, national.boss_chargeable_kg)
fad = national.order_line.filtered(lambda l: l.product_id.default_code == "FAD")
check("E9 VAT from the route: PRO -> PRO, Spanish customer -> NR", "NR", fad.boss_vat_class)
file = env["boss.expediente"].create(national._boss_file_values())
check("E9 file: national, ETD as key date, province, no country abroad", ("NTB", date(2026, 11, 20), "M", False),
      (file.traffic_code, file._boss_pricing_date(), file.inland_state_id.code, bool(file.country_id)))
check("E9 file pricing inputs: no port abroad", False, bool(file._boss_inputs()["foreign_port_id"]))

# E7 accepted quotations keep their stored values (frozen lines are never recomputed by the route)
accepted = env["sale.order"].search([("state", "=", "sale"), ("boss_pricing_frozen", "=", True)], limit=1)
if accepted:
    before = costs(accepted)
    accepted.with_context(tracking_disable=True).boss_etd = date(2026, 1, 1)
    check(f"E7 {accepted.name}: frozen costs unchanged after a route edit", before, costs(accepted))
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
