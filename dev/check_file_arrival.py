"""Check of roadmap item 10 (boss20, rolled back): the «Arrived» status of Odoo 17 (F0-C22) and the data for the
customs broker (Cristina, «Nuevo Odoo» › OPS- exptes A37). A sea import FCL file of a [PRUEBA] customer, with
fictitious sale prices, goes In transit → Arrived (typing the ATA) → Delivered; a master and its house arrive together.
Prints «CHECK PASS|FAIL …» and «RESULT …»; the broker text is checked, never printed with its amounts.
    dev/uat_run.sh check_file_arrival.py boss20"""
from datetime import date, datetime

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


port = lambda code: env["boss.port"].search([("code", "=", code), ("kind", "=", "sea")], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
Partner, File = env["res.partner"], env["boss.expediente"]
customer = Partner.create({"name": "[PRUEBA] Llegada Importador, S.L.", "is_company": True, "vat": "ESB12345674",
                           "boss_eori": "ESB12345674", "country_id": ref("base.es").id})
shipper = Partner.create({"name": "[PRUEBA] Llegada Shipper Co", "is_company": True, "country_id": ref("base.cn").id})
carrier = Partner.create({"name": "[PRUEBA] Llegada Naviera", "is_company": True, "supplier_rank": 1,
                          "country_id": ref("base.es").id})
broker = Partner.create({"name": "[PRUEBA] Llegada Aduanas", "is_company": True, "supplier_rank": 1, "lang": "es_ES",
                         "country_id": ref("base.es").id})

with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.boss_direction = "import"
    form.boss_transport_mode = "sea"
    form.boss_load_type = "fcl"
    form.boss_carrier_id = carrier
    form.boss_shipper_id = shipper
    form.boss_origin_port_id = port("CNSHA")
    form.boss_destination_port_id = port("ESVLC")
    form.boss_eta = date(2026, 12, 22)
    with form.boss_container_ids.new() as row:
        row.size = "40"
order = form.save()
prices = {"FMI": 1111.0, "THC": 222.0, "T3": 33.0, "SEG": 44.0, "FAD": 55.0}  # fictitious
order.write({"order_line": [Command.create({"product_id": product(c).id, "product_uom_id": product(c).uom_id.id})
                            for c in prices]})
order.order_line.write({"boss_supplier_id": carrier.id})
order.action_boss_update_costs()
for line in order.order_line:
    if line.boss_cost_status != "ok":
        line.boss_cost_on_request = True  # the supplier quotes case by case (M2-19)
    line.price_unit = prices[line.product_id.default_code]
order.order_line.filtered(lambda l: l.boss_cost_kind == "unknown").boss_unknown_cost_reason = "[PRUEBA] coste a consultar"
order.action_confirm()
file = order.boss_expediente_id
file.write({"customs_broker_id": broker.id, "customs_ref": "[PRUEBA] DUA-1", "mbl_ref": "[PRUEBA] MBL-1",
            "hbl_ref": "[PRUEBA] HBL-1", "vessel": "[PRUEBA] VESSEL", "goods_description": "[PRUEBA] bicicletas",
            "hs_code": "871200", "packages": 120, "gross_kg": 8000.0, "customs_guarantee": "boss",
            "scope_destination_customs": True})
file.container_ids[:1].write({"number": "MSCU1234565", "seal": "S-1"})

# the services are costed and ordered first (steps of item 1), so the next step reaches the status
file.cost_ids.filtered("cost_unknown").write({"expected_unit_cost": 1.0})
file.action_create_rfqs()
file.purchase_order_ids.button_confirm()

# 1. status
file.action_in_transit()
check("1 in transit: the next step is the arrival, and it says the ATA is missing",
      ("arrived", True), (file.next_step, "ATA" in (file.next_step_detail or "")))
try:
    with env.cr.savepoint():
        file.action_arrived()
    got = "accepted"
except UserError:
    got = "refused"
check("2 «Arrived» without ATA is refused with the reason", "refused", got)
file.ata = datetime(2026, 12, 22, 9, 0)
check("3 typing the ATA marks the file arrived by itself", "arrived", file.state)
check("4 arrived: the next step is «Delivered» and says what it still lacks",
      ("delivered", True), (file.next_step, "discharge" in (file.next_step_detail or "")))
file.write({"discharge_date": datetime(2026, 12, 22, 18, 0), "customs_release_date": datetime(2026, 12, 23, 10, 0)})
file.action_delivered()
check("5 from arrived to delivered when its conditions are met", "delivered", file.state)

# 2. the data for the customs broker (in the broker's language, Spanish)
text = file.customs_broker_text or ""
check("6 broker text names the file, the DUA, the importer with tax ID and EORI, the exporter",
      (True, True, True, True), (file.name in text, "[PRUEBA] DUA-1" in text, "EORI ESB12345674" in text,
                                 "[PRUEBA] Llegada Shipper Co" in text))
check("7 ... the transport documents, the container with its seal and the goods",
      (True, True, True, True), ("MBL [PRUEBA] MBL-1" in text, "HBL [PRUEBA] HBL-1" in text,
                                 "MSCU1234565" in text and "S-1" in text, "871200" in text))
charges = {line.split(":")[0].strip(): line.split(":", 1)[1] for line in text.splitlines()
           if line.startswith("  ") and ":" in line}
print("      charges:", {k: ("amount" if any(ch.isdigit() for ch in v) else v.strip()) for k, v in charges.items()})
check("8 ... the four charges of the customs value, each with the amount sold (fictitious); customs (FAD) is not one",
      (4, True, False), (len(charges), all(any(ch.isdigit() for ch in v) for v in charges.values()),
                         any("55" in v for v in charges.values())))
check("9 ... in the broker's language (Spanish)", True, text.startswith("Expediente"))
operator = env["res.users"].create({"name": "[PRUEBA] Compras sin ventas", "login": "prueba-operativo-llegada",
                                    "group_ids": [Command.set([ref("base.group_user").id,
                                                               ref("purchase.group_purchase_user").id])]})
other_text = file.with_user(operator).customs_broker_text or ""
check("10 a user who does not see the sale gets the text without the amounts", (True, False),
      (file.name in other_text, len(other_text.splitlines()) == len(text.splitlines())))

# 3. a master and its house arrive together
master = File.create({"partner_id": customer.id, "business": "boss", "direction": "import", "transport_mode": "sea",
                      "load_type": "fcl", "carrier_id": carrier.id, "origin_port_id": port("CNSHA").id,
                      "destination_port_id": port("ESVLC").id, "eta": date(2026, 12, 22)})
house = File.create({"partner_id": customer.id, "business": "boss", "direction": "import", "transport_mode": "sea",
                     "load_type": "lcl", "master_id": master.id})
master.action_in_transit()
master.ata = datetime(2026, 12, 22, 9, 0)
check("11 the master's ATA arrives the master and its house", ("arrived", "arrived"), (master.state, house.state))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
