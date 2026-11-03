"""[PRUEBA] consolidation on boss20 (roadmap item 8, ADR-013), modelled on the real Odoo 17 file E260468: one 40'
container from Shekou to Valencia for one importer of books, with house B/Ls of several shippers. Here: a master file
with its shared purchases (fictitious amounts) and two houses of the same customer (two shippers), each sold per W/M,
accepted and linked, so the screens of a consolidation can be seen. Idempotent: kept by its customer reference.
Prints «CASE …» and «RESULT …», never an amount of a boss20 tariff or pricelist.
    dev/uat_run.sh sample_consolidation.py boss20"""
from datetime import date

from odoo import Command
from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
belal = env["res.users"].search([("login", "=", "devbms")], limit=1)  # noqa: F821
env = env(user=belal, context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
o17 = lambda i: ref(f"o17_partner.res_partner_{i}")  # noqa: E731
port = lambda code: env["boss.port"].search([("code", "=", code), ("kind", "=", "sea")], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
line_of = lambda o, code: o.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731
customer, carrier, broker, agent = o17(23212), o17(36546), o17(23015), o17(23584)  # Susaeta, ONE, Ramos Vila, Publiship
REFERENCE = "[PRUEBA] consolidación modelo E260468"
File = env["boss.expediente"]
master = File.search([("partner_id", "=", customer.id), ("mbl_ref", "=", f"{REFERENCE} MBL"), ("state", "!=", "cancel")],
                     limit=1)
if not master:
    master = File.create({
        "partner_id": customer.id, "business": "boss", "direction": "import", "transport_mode": "sea", "load_type": "fcl",
        "carrier_id": carrier.id, "agent_id": agent.id, "origin_country_id": ref("base.cn").id,
        "origin_port_id": port("CNSHK").id, "destination_country_id": ref("base.es").id,
        "destination_port_id": port("ESVLC").id, "etd": date(2026, 11, 25), "eta": date(2026, 12, 30),
        "mbl_ref": f"{REFERENCE} MBL", "vessel": "[PRUEBA] ONE VESSEL", "voyage": "001W",
        "booking_ref": "[PRUEBA] BK-CONSOL", "scope_main": True, "scope_destination_customs": True, "scope_delivery": True,
        "container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id})],
        "cost_ids": [Command.create({"kind": "extra", "product_id": product(code).id, "uom_id": product(code).uom_id.id,
                                     "partner_id": partner.id, "quantity": 1.0, "expected_unit_cost": cost,
                                     "extra_class": "covered",
                                     "reason": "[PRUEBA] compra compartida de la consolidación (importe ficticio)"})
                     for code, partner, cost in (("FMI", carrier, 2000.0), ("THC", carrier, 300.0),
                                                 ("TTE-FCL", carrier, 400.0))],
    })
    print(f"CASE master {master.name} created")
else:
    print(f"CASE master {master.name} reused")
HOUSES = [("casa 1 · shipper Luhao", "[PRUEBA] Libros infantiles", 400, 6150.0, 18.7),
          ("casa 2 · shipper Everpurple", "[PRUEBA] Libros ilustrados", 200, 1900.0, 5.2)]
for label, goods, packages, kg, m3 in HOUSES:
    reference = f"{REFERENCE} · {label}"
    order = env["sale.order"].search([("client_order_ref", "=", reference), ("state", "!=", "cancel")], limit=1)
    if order:
        print(f"CASE house {order.boss_expediente_id.name} reused ({label})")
        continue
    with Form(env["sale.order"]) as form:
        form.partner_id = customer
        form.boss_direction = "import"
        form.boss_transport_mode = "sea"
        form.boss_load_type = "lcl"
        form.boss_carrier_id = carrier
        form.boss_origin_country_id = ref("base.cn")
        form.boss_origin_port_id = port("CNSHK")
        form.boss_destination_port_id = port("ESVLC")
        form.boss_etd = date(2026, 11, 25)
        form.boss_eta = date(2026, 12, 30)
        form.boss_gross_kg = kg
        form.boss_volume_m3 = m3
        form.boss_goods_description = goods
        form.boss_packages = packages
        form.boss_package_type = "CT"
        form.client_order_ref = reference
    order = form.save()
    order.write({"order_line": [Command.create({"product_id": product(c).id, "product_uom_id": product(c).uom_id.id})
                                for c in ("FMI-LCL", "THC-LCL", "FAD", "CSM")]})
    for code, partner in (("FMI-LCL", carrier), ("THC-LCL", carrier), ("FAD", broker)):
        line_of(order, code).boss_supplier_id = partner
    order.action_boss_update_costs()
    for line in order.order_line.filtered(lambda l: l.boss_cost_status == "no_tariff" and l.boss_supplier_id):
        line.boss_cost_on_request = True
    line_of(order, "FMI-LCL").write({"boss_manual_cost": 60.0, "boss_manual_cost_note": "[PRUEBA] parte estimada del contenedor"})
    for code, price in (("FMI-LCL", 95.0), ("THC-LCL", 20.0)):  # fictitious prices per W/M
        line_of(order, code).price_unit = price
    for line in order.order_line.filtered(lambda l: l.product_id and l.boss_sale_status == "missing"):
        line.price_unit = round(100.0 / (line.product_uom_qty or 1.0), 4)
    order.action_confirm()
    house = order.boss_expediente_id
    house.master_id = master
    print(f"CASE house {house.name} created for {label}")
env.invalidate_all()
print(f"RESULT master {master.name}: {master.house_count} houses, shares "
      f"{[h.master_share for h in master.house_ids]} (sum {round(sum(master.house_ids.mapped('master_share')), 2)})")
env.cr.commit()
