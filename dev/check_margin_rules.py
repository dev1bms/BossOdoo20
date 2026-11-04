"""Check of roadmap item 15 (boss20, rolled back): the minimum margin control of Odoo 17 (groups of services, rules by
kind of shipment, policies of single services, exceptions per customer), loaded by dev/load_margin_rules.py. Fictitious
sale and cost figures; the rules are read from boss20 and only the minimums of these invented cases are printed.
    dev/uat_run.sh check_margin_rules.py boss20"""
from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []
Policy = env["boss.margin.policy"]
money = lambda amount: f"{amount:.2f}"  # noqa: E731


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


P = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
customer = env["res.partner"].create({"name": "[PRUEBA] Márgenes Cliente", "is_company": True})


def ctx(mode, load=False, business="boss", n20=0, n40=0, kg=0.0, customer_=None, direction="import", freight=False,
        carriers=()):
    return {"transport_mode": mode, "load_type": load, "business": business, "direction": direction,
            "freight_payment": freight, "customer": customer_ or customer, "carrier_ids": set(carriers),
            "containers_20": n20, "containers_40": n40, "chargeable_kg": kg}


def row(by_product, context, label):
    rows = Policy._boss_check(by_product, context, money)
    found = [r for r in rows if r[0] == label]
    return found[0] if found else None


check("0 loaded from Odoo 17: 4 groups, 4 policies, 13 rules, 16 exceptions", (4, 4, 13, 16),
      (env["boss.margin.family"].search_count([("kind", "=", "group")]),
       env["boss.margin.family"].search_count([("kind", "=", "policy")]),
       env["boss.margin.rule"].search_count([]), env["boss.margin.exception"].search_count([])))
fmi = P("FMI")
r = row({fmi: (1200.0, 1000.0)}, ctx("sea", "fcl", n20=1, n40=1), "Flete")
check("1 sea FCL, BOSS customer, 1×20' + 1×40': freight minimum = 100 + 150 per container (above 10 %)",
      (250.0, True), (r[3], bool(r[4])))
r = row({fmi: (1250.0, 1000.0)}, ctx("sea", "fcl", n20=1, n40=1), "Flete")
check("2 ... with 250 of margin, no warning", False, bool(r[4]))
r = row({fmi: (1050.0, 1000.0)}, ctx("sea", "fcl", business="agent", n20=1, n40=1), "Flete")
check("3 agent business: 25 per container (above 1.5 %), 50 of margin is fine", (50.0, False), (r[3], bool(r[4])))
fai = P("FAI")
r = row({fai: (1100.0, 1000.0)}, ctx("air", "air", kg=400.0), "Flete")
check("4 air, BOSS customer, 400 kg: max(50, 0.30 × 400) = 120 (above 10 %)", (120.0, True), (r[3], bool(r[4])))
tte = P("TTE-FCL")
r = row({tte: (3100.0, 3000.0)}, ctx("road", n40=1), "Transporte")
check("5 road: 10 % of the cost, at most 200 per container", (200.0, True), (r[3], bool(r[4])))
exception = env["boss.margin.exception"].search([("customer_id", "!=", False), ("family_id.name", "=", "Flete"),
                                                ("force_percent", "=", True)], limit=1)
if exception:  # its customer and percentage stay private (loaded from .research/), never printed
    r = row({fmi: (1100.0, 1000.0)}, ctx("sea", "fcl", n20=1, n40=1, customer_=exception.customer_id), "Flete")
    check("6 a customer exception of Odoo 17 replaces the rule for that customer (its own % of the cost)",
          (True, True), (round(r[3], 2) == round(exception.percent / 100 * 1000.0, 2), r[5] == exception.name))
dem = P("DEM")
r = row({dem: (100.0, 105.0)}, ctx("sea", "fcl", n40=1), "DEM")
check("7 «no margin» service at a loss is flagged (no tolerance), as in Odoo 17", True, bool(r[4]))
pft = P("PFT-FCL")
r = row({pft: (0.0, 50.0)}, ctx("sea", "fcl", n40=1), "PFT-FCL")
check("8 «may lose» service (profit share): no warning", False, bool(r[4]))
ara = P("ARA")
r = row({ara: (100.0, 90.0)}, ctx("sea", "fcl", n40=1), "ARA")
check("9 duties paid on behalf re-invoiced differently: flagged", True, bool(r[4]))
fad = P("FAD")
r = row({fad: (105.0, 100.0)}, ctx("sea", "fcl", n40=1), "FAD")
check("10 a service outside every group: 10 % of its cost, within 10 of tolerance", (10.0, False), (r[3], bool(r[4])))

# 11. the quotation's warning uses the rules
order = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_business": "boss", "boss_container_ids": [Command.create({"size": "40", "quantity": 1,
                                                                    "container_type_id": ref("boss_pricing.container_type_dv").id})],
    "order_line": [Command.create({"product_id": fmi.id, "product_uom_qty": 1, "price_unit": 1100.0,
                                   "boss_manual_cost": 1000.0, "boss_manual_cost_note": "[PRUEBA]"})]})
order.order_line.price_unit = 1100.0  # typed by the salesperson (otherwise cost + 20 % = 1200, above the minimum)
order.invalidate_recordset(["boss_margin_alert"])
check("11 the quotation warns with the rule (150 per 40', not 10 %)", (True, True),
      ("Flete" in (order.boss_margin_alert or ""), "150" in (order.boss_margin_alert or "")))
print("      alert:", order.boss_margin_alert)

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
