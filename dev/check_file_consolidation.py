"""Check of roadmap item 8 (consolidations, ADR-013) on boss20, rolled back: a master file (one 40' container, the
master B/L and the shared purchases) with two houses of two customers, modelled on the real Odoo 17 file E260468 (one
container, five house B/Ls of one importer). [PRUEBA] customers, supplier and fictitious figures only.
Prints «CHECK PASS|FAIL …» and «RESULT …».
    dev/uat_run.sh check_file_consolidation.py boss20"""
from datetime import date, datetime

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []
ERRORS = (UserError, ValidationError, AccessError)


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def refused(name, fn):
    try:
        with env.cr.savepoint():
            fn()
        got = "accepted"
    except ERRORS as exc:
        got = "refused"
        print(f"      «{' '.join(str(exc).split())[:160]}»")
    check(name, "refused", got)


port = lambda code: env["boss.port"].search([("code", "=", code), ("kind", "=", "sea")], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
line_of = lambda o, code: o.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731
Partner, File = env["res.partner"], env["boss.expediente"]
company = lambda name: Partner.create({"name": name, "is_company": True, "country_id": ref("base.es").id,  # noqa: E731
                                       "vat": "ESB12345674"})
importer = company("[PRUEBA] Consol Importador A, S.L.")
other = company("[PRUEBA] Consol Importador B, S.L.")
carrier = Partner.create({"name": "[PRUEBA] Consol Naviera", "is_company": True, "supplier_rank": 1,
                          "country_id": ref("base.es").id})
broker = Partner.create({"name": "[PRUEBA] Consol Aduanas", "is_company": True, "supplier_rank": 1,
                         "country_id": ref("base.es").id})

# ---- the master: one container, the master B/L, the shared purchases (fictitious expected costs typed)
master = File.create({
    "partner_id": importer.id, "business": "boss", "direction": "import", "transport_mode": "sea", "load_type": "fcl",
    "carrier_id": carrier.id, "origin_country_id": ref("base.cn").id, "origin_port_id": port("CNSHA").id,
    "destination_country_id": ref("base.es").id, "destination_port_id": port("ESVLC").id,
    "etd": date(2026, 11, 20), "eta": date(2026, 12, 22), "mbl_ref": "[PRUEBA] MBL-CONSOL", "vessel": "[PRUEBA] VESSEL",
    "container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id})],
})
for code, cost in (("FMI", 1000.0), ("THC", 200.0), ("TTE-FCL", 300.0)):
    master.cost_ids = [Command.create({"kind": "extra", "product_id": product(code).id, "uom_id": product(code).uom_id.id,
                                       "partner_id": carrier.id, "quantity": 1.0, "expected_unit_cost": cost,
                                       "extra_class": "covered", "reason": "[PRUEBA] shared purchase of the consolidation"})]
check("the master forecasts its shared costs (freight, THC, haulage of the container)", 1500.0,
      round(master.amount_cost_forecast, 2))


def house_quotation(customer, prices, kg, m3):
    with Form(env["sale.order"]) as form:
        form.partner_id = customer
        form.boss_direction = "import"
        form.boss_transport_mode = "sea"
        form.boss_load_type = "lcl"
        form.boss_carrier_id = carrier
        form.boss_origin_country_id = ref("base.cn")
        form.boss_origin_port_id = port("CNSHA")
        form.boss_destination_port_id = port("ESVLC")
        form.boss_etd = date(2026, 11, 20)
        form.boss_eta = date(2026, 12, 22)
        form.boss_gross_kg = kg
        form.boss_volume_m3 = m3
    order = form.save()
    order.write({"order_line": [Command.create({"product_id": product(c).id, "product_uom_id": product(c).uom_id.id})
                                for c in prices]})
    for code, partner in (("FMI-LCL", carrier), ("THC-LCL", carrier), ("FAD", broker)):
        line_of(order, code).boss_supplier_id = partner
    order.action_boss_update_costs()
    for line in order.order_line.filtered(lambda l: l.boss_cost_status == "no_tariff" and l.boss_supplier_id):
        line.boss_cost_on_request = True  # the coloader and the broker quote case by case (M2-19)
    # the freight is a manual amount: the house's estimated part of the container, until the master's cost is shared
    line_of(order, "FMI-LCL").write({"boss_manual_cost": prices["FMI-LCL"] * 0.6,
                                     "boss_manual_cost_note": "[PRUEBA] parte estimada del contenedor"})
    for code, price in prices.items():
        line_of(order, code).price_unit = price
    order.action_confirm()
    return order.boss_expediente_id


house_a = house_quotation(importer, {"FMI-LCL": 900.0, "THC-LCL": 150.0, "FAD": 100.0, "CSM": 60.0}, 20000.0, 20.0)
house_b = house_quotation(other, {"FMI-LCL": 500.0, "THC-LCL": 80.0, "FAD": 100.0, "CSM": 60.0}, 10000.0, 10.0)
check("two houses accepted, each for its own customer, sold per W/M", (importer, other, "lcl"),
      (house_a.partner_id, house_b.partner_id, house_b.load_type))
(house_a | house_b).write({"master_id": master.id})
env.invalidate_all()
check("the master has two houses, the houses know their master", ("master", 2, "house", "house"),
      (master.consolidation_role, master.house_count, house_a.consolidation_role, house_b.consolidation_role))
check("a master sells nothing itself: it is not asked to link a quotation, its next step is to order", "order",
      master.next_step)
check("the master's transport data is copied to the houses (master B/L, vessel, carrier, dates)",
      [("[PRUEBA] MBL-CONSOL", "[PRUEBA] VESSEL", carrier, date(2026, 12, 22))] * 2,
      [(h.mbl_ref, h.vessel, h.carrier_id, h.eta) for h in (house_a, house_b)])
master.write({"vessel": "[PRUEBA] VESSEL 2", "atd": datetime(2026, 11, 21, 8, 0)})
check("... and follows every later change of the master", [("[PRUEBA] VESSEL 2", True)] * 2,
      [(h.vessel, bool(h.atd)) for h in (house_a, house_b)])
covered = house_a.cost_ids.filtered("master_covered")
check("the house's freight and local charges are bought on the master, not ordered again; its customs stay its own",
      (["FMI-LCL", "THC-LCL"], ["FAD"]),
      (sorted(covered.mapped("product_id.default_code")),
       sorted(house_a.cost_ids.filtered(lambda n: not n.master_covered).mapped("product_id.default_code"))))
check("shared costs split by chargeable weight (W/M): 20 000 kg and 10 000 kg", (66.67, 33.33),
      (house_a.master_share, house_b.master_share))
master.allocation_basis = "equal"
env.invalidate_all()
check("... by equal parts", (50.0, 50.0), (house_a.master_share, house_b.master_share))
master.allocation_basis = "manual"
house_a.master_share, house_b.master_share = 70.0, 30.0
env.invalidate_all()
check("... or typed by hand", (70.0, 30.0), (house_a.master_share, house_b.master_share))
master.allocation_basis = "chargeable"
env.invalidate_all()
for house in (house_a, house_b):  # the broker quotes: operations types the customs cost on each house
    house.cost_ids.filtered(lambda n: n.product_id == product("FAD")).write({"expected_unit_cost": 50.0})
env.invalidate_all()
check("house A bears 66.67 % of the master's 1 500 and its own customs cost", (1000.05, 1050.05),
      (round(house_a.amount_master_cost, 2), round(house_a.amount_cost_forecast, 2)))
check("house A's margin = its sale - its cost (share of the master + own customs)",
      round(house_a.amount_sale - 1050.05, 2), round(house_a.amount_margin_forecast, 2))
check("house B bears the other 33.33 %", (499.95, 549.95),
      (round(house_b.amount_master_cost, 2), round(house_b.amount_cost_forecast, 2)))
houses_sale = round(house_a.amount_sale + house_b.amount_sale, 2)
check("the master's consolidated view: sale of the houses, shared costs 1 500, own costs of the houses 100, margin",
      (houses_sale, 1500.0, 100.0, round(houses_sale - 1600.0, 2)),
      (round(master.amount_houses_sale, 2), round(master.amount_cost_forecast, 2),
       round(master.amount_houses_cost, 2), round(master.amount_consolidated_margin, 2)))
# «Margin per file» report (go-live tracker P2-17): the master's row is net of the costs passed to its houses, so the
# rows of a consolidation add up to the consolidated margin instead of counting the shared costs twice.
Report = env["boss.margin.report"]
Report._boss_refresh(master | house_a | house_b)
rows = Report.search([("expediente_id", "in", (master | house_a | house_b).ids)])
check("margin report: the rows of the master and its houses add up to the consolidated margin (no double count)",
      round(master.amount_consolidated_margin, 2), round(sum(rows.mapped("amount_margin_forecast")), 2))
check("margin report: the master's row shows its costs net of what it passed to the houses", 0.0,
      round(rows.filtered(lambda r: r.expediente_id == master).amount_cost_forecast, 2))
check("the explanation of house A names its share of the master", True,
      master.name in (house_a.profit_explanation or "") and "66.67" in (house_a.profit_explanation or ""))

# ---- the consolidation leaves and is invoiced per house
master.action_in_transit()
env.invalidate_all()
check("putting the master in transit puts its houses in transit", ["in_transit"] * 3,
      [f.state for f in (master, house_a, house_b)])
Invoice = env["boss.invoice.services"]
invoices = env["account.move"]
for house in (house_a, house_b):
    todo = house.allocation_ids.filtered(lambda a: a.to_invoice_quantity > 0)
    result = Invoice.create({"expediente_id": house.id, "allocation_ids": [Command.set(todo.ids)]}).action_create()
    invoices |= env["account.move"].browse(result.get("res_id") or result["domain"][0][2])
check("each house is invoiced to its own customer", {importer, other}, set(invoices.mapped("partner_id")))


def close_financially(file):
    file.write({"state": "closed"})
    file.action_close_financial()


refused("a house cannot close financially while the master's shared costs are not billed (its share is pending)",
        lambda: close_financially(house_a))
refused("a master cannot close financially while a house is open", lambda: close_financially(master))
refused("a house cannot be the master of another file", lambda: house_b.write({"master_id": house_a.id}))
new_house = File.browse(master.action_new_house()["res_id"])
check("«New house» on the master opens a house with the same case and route, linked and synced",
      ("house", "import", port("ESVLC"), "[PRUEBA] MBL-CONSOL", importer),
      (new_house.consolidation_role, new_house.direction, new_house.destination_port_id, new_house.mbl_ref,
       new_house.partner_id))
single = File.search([("master_id", "=", False), ("house_ids", "=", False), ("state", "=", "open")], limit=1)
check("a file that is neither master nor house is a single shipment: nothing changes for it", ("single", 0.0),
      (single.consolidation_role, single.master_share))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
