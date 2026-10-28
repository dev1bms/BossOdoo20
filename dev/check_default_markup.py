"""Check of the default sale price «expected cost + %» (Belal, 27/10/2026) on boss20: the Sales setting creates one
rule on the default pricelist, a known cost gives cost + 20 %, an unknown cost gives no price (never built on zero), a
typed price is kept when the cost changes, a customer's own pricelist keeps its agreed prices, a product that is not a
BOSS service keeps its list price, accepted quotations do not move, and 0 removes the rule. Every record is made here
and rolled back; the setting itself is driven through its helpers (the Settings screen is checked in Chrome after
the deploy). Prints «CHECK PASS|FAIL …» and «RESULT n passed, m failed».
    dev/uat_run.sh check_default_markup.py boss20"""
from datetime import date

from odoo import Command
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
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
Partner = env["res.partner"]
Settings = env["res.config.settings"]
Item = env["product.pricelist.item"]
msc = Partner.search([("name", "=", "MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.")], limit=1)
rules = lambda: Item.search([("base", "=", "boss_line_cost"), ("applied_on", "=", "3_global"), ("pricelist_id.active", "=", True)])  # noqa: E731
prices = lambda o: [(l.product_id.default_code, l.boss_sale_status, round(l.price_unit, 2)) for l in o.order_line.filtered("product_id")]  # noqa: E731

customer = Partner.create({"name": "[PRUEBA] Cliente recargo 20", "is_company": True, "country_id": ref("base.es").id,
                           "vat": "ESB12345674", "city": "Madrid", "state_id": state("M").id})
warehouse = Partner.create({"name": "[PRUEBA] Almacén recargo", "parent_id": customer.id, "type": "delivery",
                            "city": "Getafe", "state_id": state("M").id, "country_id": ref("base.es").id})
accepted = env["sale.order"].search([("state", "=", "sale"), ("boss_pricing_frozen", "=", True)], order="id", limit=1)
frozen_before = prices(accepted) if accepted else None

# 1. the setting: off (whatever boss20 has is switched off inside this transaction, rolled back at the end), then 20 %
Settings._boss_set_default_markup(0)
check("1 off: no global rule", 0, len(rules()))
check("1 setting reads 0 while off", 0.0, Settings._boss_get_default_markup())
Settings._boss_set_default_markup(20)
rule = rules()
check("1 one global rule created", 1, len(rule))
default_pricelist = env["product.pricelist"]._get_partner_pricelist_multi([customer.id])[customer.id]
check("1 the rule is on the pricelist a new customer gets", default_pricelist, rule.pricelist_id)
check("1 rule: cost + 20 % (surcharge, stored as a negative discount)", ("markup", 20.0, -20.0),
      (rule.compute_price, rule.price_markup, rule.price_discount))
check("1 setting reads 20 afterwards", 20.0, Settings._boss_get_default_markup())
Settings._boss_set_default_markup(25)
check("1 changing the percentage updates the same rule", (1, 25.0), (len(rules()), rule.price_markup))
Settings._boss_set_default_markup(20)

# 2. quotation: known cost -> cost + 20 %; unknown cost -> no price
with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.sale_order_template_id = template("IMB FOB")
    form.boss_carrier_id = msc
    form.boss_origin_country_id = ref("base.cn")
    form.boss_origin_port_id = port("CNSHA", "sea")
    form.boss_destination_port_id = port("ESVLC", "sea")
    form.boss_delivery_address_id = warehouse
    form.boss_eta = date(2026, 12, 10)
    with form.boss_container_ids.new() as container:
        container.size = "40"
        container.container_type_id = ref("boss_pricing.container_type_dv")
order = form.save()
check("2 quotation on the default pricelist", default_pricelist, order.pricelist_id)
line = lambda code: order.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731
thc, fmi = line("THC"), line("FMI")
check("2 THC: cost 253 from MSC -> sale 303.60 (cost + 20 %)", ("ok", 253.0, "cost_based", 303.6),
      (thc.boss_cost_status, round(thc.purchase_price, 2), thc.boss_sale_status, round(thc.price_unit, 2)))
check("2 THC explanation names the pricelist rule", True,
      "20" in (thc.boss_sale_explanation or "") and rule.pricelist_id.name in (thc.boss_sale_explanation or ""))
check("2 FMI: no cost -> no sale price (never built on zero), missing", ("manual", 0.0, "missing"),
      (fmi.boss_cost_status, fmi.price_unit, fmi.boss_sale_status))
check("2 the quotation still says what is missing", True, "FMI" in (order.boss_pricing_alert or "") or bool(order.boss_pricing_alert))

# 3. manual cost typed -> sale follows; a typed sale price is kept when the cost changes
fmi.write({"boss_manual_cost": 1500.0, "boss_manual_cost_note": "[PRUEBA] oferta MSC"})
check("3 FMI manual cost 1500 -> sale 1800 (price and technical price agree)", ("cost_based", 1800.0, 1800.0, True),
      (fmi.boss_sale_status, round(fmi.price_unit, 2), round(fmi.technical_price_unit, 2), bool(fmi.pricelist_item_id)))
fmi.price_unit = 1700.0
check("3 typed sale price -> manual", ("manual", 1700.0), (fmi.boss_sale_status, round(fmi.price_unit, 2)))
fmi.boss_manual_cost = 1600.0
check("3 cost changed: the typed price is kept", ("manual", 1600.0, 1700.0),
      (fmi.boss_sale_status, round(fmi.purchase_price, 2), round(fmi.price_unit, 2)))
thc.price_unit = 300.0
order.order_line._boss_recompute_cost()
check("3 explicit re-pricing keeps the typed THC price", ("manual", 300.0), (thc.boss_sale_status, round(thc.price_unit, 2)))

# 4. a customer with an agreed pricelist keeps it (no surcharge on top)
cofitel = Partner.search([("name", "=ilike", "COFITEL%"), ("is_company", "=", True)], limit=1)
if cofitel and cofitel.property_product_pricelist.item_ids:
    agreed = env["sale.order"].create({
        "partner_id": cofitel.id, "boss_direction": "import", "boss_transport_mode": "air", "boss_load_type": "air",
        "order_line": [Command.create({"product_id": product("AWB").id, "product_uom_id": product("AWB").uom_id.id})]})
    awb = agreed.order_line
    check("4 COFITEL: agreed AWB 75 from its own pricelist, not cost + 20 %", ("agreed", 75.0),
          (awb.boss_sale_status, round(awb.price_unit, 2)))
else:
    print("CHECK SKIP 4 no customer with an agreed pricelist on boss20")

# 5. a product that is not a BOSS service keeps its list price under the global rule
plain = env["product.product"].create({"name": "[PRUEBA] Artículo sin tarifa BOSS", "type": "consu", "list_price": 10.0})
order.write({"order_line": [Command.create({"product_id": plain.id})]})
plain_line = order.order_line.filtered(lambda l: l.product_id == plain)
check("5 non-BOSS product: list price 10", 10.0, round(plain_line.price_unit, 2))

# 5b. paid on behalf of the customer (Belal 28/10/2026, F0-A00): re-invoiced at the amount paid, never cost + 20 %
flagged = sorted(env["product.template"].search([("boss_paid_on_behalf", "=", True)]).mapped("default_code"))
print(f"      services with the explicit flag «Paid on behalf»: {flagged}")
check("5b the services re-invoiced at cost are the ones with the explicit flag (not a list of codes)", True,
      bool(flagged) and all(env["product.product"].search([("default_code", "=", c)]).boss_paid_on_behalf for c in flagged))
ob = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_carrier_id": msc.id, "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id,
    "boss_destination_port_id": port("ESVLC", "sea").id, "boss_eta": date(2026, 12, 10), "boss_duties_amount": 500.0,
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_dv").id, "quantity": 1})],
    "order_line": [Command.create({"product_id": product("THC").id, "product_uom_id": product("THC").uom_id.id,
                                   "boss_container_size": "40", "boss_container_type_id": ref("boss_pricing.container_type_dv").id}),
                   Command.create({"product_id": product("ARA").id, "product_uom_id": product("ARA").uom_id.id})]})
ara = ob.order_line.filtered(lambda l: l.product_id.default_code == "ARA")
thc_ob = ob.order_line.filtered(lambda l: l.product_id.default_code == "THC")
check("5b duties (ARA) with no amount yet: no price proposed (never 0 taken as a price)", ("missing", 0.0),
      (ara.boss_sale_status, ara.price_unit))
ara.write({"boss_manual_cost": 500.0})
check("5b duties 500 paid -> sale 500, without margin, shown as an estimate", (500.0, "cost_based", True, True),
      (round(ara.price_unit, 2), ara.boss_sale_status, "without margin" in (ara.boss_sale_explanation or ""),
       "Estimate" in (ara.boss_sale_explanation or "")))
ara.boss_manual_cost_note = "[PRUEBA] DUA 26ES0046"
check("5b with a reference typed: shown as typed and unverified (no longer «estimate», never «documented»)",
      (True, False, True), ("[PRUEBA] DUA 26ES0046" in ara.boss_sale_explanation, "Estimate" in ara.boss_sale_explanation,
                            "does not check" in ara.boss_sale_explanation))
check("5b THC on the same quotation keeps cost + 20 %", ("cost_based", True),
      (thc_ob.boss_sale_status, abs(thc_ob.price_unit - round(thc_ob.purchase_price * 1.2, 2)) < 0.011))
ara.price_unit = 510.0
check("5b a selling price typed by a person is kept", ("manual", 510.0), (ara.boss_sale_status, round(ara.price_unit, 2)))
Item.create({"pricelist_id": default_pricelist.id, "applied_on": "0_product_variant", "product_id": product("ARA").id,
             "uom_id": product("ARA").uom_id.id, "compute_price": "fixed", "fixed_price": 520.0})
ob.write({"order_line": [Command.create({"product_id": product("ARA").id, "product_uom_id": product("ARA").uom_id.id,
                                         "boss_manual_cost": 500.0, "boss_manual_cost_note": "[PRUEBA] DUA 2"})]})
ara2 = ob.order_line.filtered(lambda l: l.product_id.default_code == "ARA")[-1:]
check("5b a price agreed in the pricelist for the service is kept (only the cost + % default changes)",
      ("agreed", 520.0), (ara2.boss_sale_status, round(ara2.price_unit, 2)))

# 6. accepted quotations do not move
if accepted:
    accepted.order_line._boss_recompute_cost()
    check(f"6 {accepted.name}: frozen prices unchanged", frozen_before, prices(accepted))

# 7. switched off: the rule is removed and a new line gets no price
Settings._boss_set_default_markup(0)
check("7 off: no rule", 0, len(rules()))
check("7 setting reads 0", 0.0, Settings._boss_get_default_markup())
other = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_carrier_id": msc.id, "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id,
    "boss_destination_port_id": port("ESVLC", "sea").id, "boss_eta": date(2026, 12, 10),
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_dv").id, "quantity": 1})],
    "order_line": [Command.create({"product_id": product("THC").id, "product_uom_id": product("THC").uom_id.id,
                                   "boss_container_size": "40", "boss_container_type_id": ref("boss_pricing.container_type_dv").id})]})
thc2 = other.order_line
check("7 off: THC cost known but no sale price proposed", ("ok", "missing", 0.0),
      (thc2.boss_cost_status, thc2.boss_sale_status, thc2.price_unit))
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if len(results) - sum(results):  # a failed check fails the run (dev/uat_run.sh records the exit status)
    raise SystemExit(1)
