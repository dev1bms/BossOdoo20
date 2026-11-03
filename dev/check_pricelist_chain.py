"""Check of roadmap item 3, G1 and G4 (boss20, rolled back): selling prices per container size, a customer pricelist
that falls back to the general «cost + %» rule, and the minimum margin warning of Odoo 17.

A [PRUEBA] customer with its own pricelist agrees THC per container size (fictitious 611 for 20', 622 for 40'); its last
rule is «based on the general pricelist». A sea import FCL quotation (template IMB FOB, MSC, Xingang → Valencia,
1×20' DV + 1×40' HC) must give: THC 20' 611 and THC 40' 622 (agreed), the services it does not agree priced by the
general rule from their cost (cost + %), the freight with a manual cost priced the same way, and, without the last rule,
those services without a selling price (the behaviour before). Prints «CHECK PASS|FAIL …» and «RESULT …», never an amount of a boss20 tariff or pricelist (real prices stay out of
Git: only the fictitious prices of the [PRUEBA] pricelist are printed).
    dev/uat_run.sh check_pricelist_chain.py boss20"""
from datetime import date

from odoo import Command
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
settings = env["res.config.settings"]
general = settings._boss_default_markup_rules()[:1].pricelist_id  # the pricelist holding the default «cost + %» rule
markup = settings._boss_get_default_markup()
print(f"      general pricelist {general.name}, default rule cost + {markup} %")
thc = product("THC")
container = ref("boss_services.uom_container")
pricelist = env["product.pricelist"].create({
    "name": "[PRUEBA] Tarifa cliente por tamaño", "currency_id": env.company.currency_id.id,
    "item_ids": [Command.create({"applied_on": "1_product", "product_tmpl_id": thc.product_tmpl_id.id,
                                 "uom_id": container.id, "compute_price": "fixed", "fixed_price": price,
                                 "boss_container_size": size}) for size, price in (("20", 611.0), ("40", 622.0))]
    + [Command.create({"applied_on": "3_global", "compute_price": "discount", "price_discount": 0.0,
                       "base": "pricelist", "base_pricelist_id": general.id})]})
customer = env["res.partner"].create({"name": "[PRUEBA] Cliente tarifa por tamaño", "is_company": True,
                                     "country_id": ref("base.es").id, "vat": "ESB12345674",
                                     "property_product_pricelist": pricelist.id})
msc = env.ref("o17_partner.res_partner_23762")


def quotation():
    with Form(env["sale.order"]) as form:
        form.partner_id = customer
        form.sale_order_template_id = env["sale.order.template"].search([("name", "=like", "IMB FOB · %")], limit=1)
        form.boss_carrier_id = msc
        form.boss_origin_country_id = ref("base.cn")
        form.boss_origin_port_id = port("CNXGG")
        form.boss_destination_port_id = port("ESVLC")
        form.boss_etd = date(2026, 11, 12)
        form.boss_eta = date(2026, 12, 16)
        for size, ctype in (("20", "dv"), ("40", "hc")):
            with form.boss_container_ids.new() as row:
                row.size = size
                row.container_type_id = ref(f"boss_pricing.container_type_{ctype}")
    order = form.save()
    for line in order.order_line.filtered(lambda l: l.product_id.default_code in ("THC", "BL", "FMI", "GLO-CCC")):
        line.boss_supplier_id = msc
    order.order_line.filtered(lambda l: l.product_id.default_code == "FMI").write(
        {"boss_manual_cost": 1000.0, "boss_manual_cost_note": "[PRUEBA] flete ficticio"})
    order.action_boss_update_costs()
    return order


order = quotation()
thc_lines = order.order_line.filtered(lambda l: l.product_id == thc)
check("THC has one line per container size", ["20", "40"], sorted(thc_lines.mapped("boss_container_size")))
check("THC 20' and 40' take the agreed price of their size",
      [("20", 611.0, "agreed"), ("40", 622.0, "agreed")],
      sorted((l.boss_container_size, l.price_unit, l.boss_sale_status) for l in thc_lines))
glo = order.order_line.filtered(lambda l: l.product_id.default_code == "GLO-CCC")[:1]
expected_glo = round(glo.purchase_price * (1 + markup / 100), 2)
check("GLO-CCC, agreed nowhere, falls back to the general rule: cost + % (amounts compared, not printed)",
      (True, "cost_based", True), (round(glo.price_unit, 2) == expected_glo, glo.boss_sale_status, bool(glo.purchase_price)))
bl = order.order_line.filtered(lambda l: l.product_id.default_code == "BL")
check("BL takes the general pricelist's agreed price (Odoo 17 «Standard»), not cost + %", "agreed", bl.boss_sale_status)
fmi = order.order_line.filtered(lambda l: l.product_id.default_code == "FMI")
check("freight with a manual cost falls back to the general rule too",
      [(round(1000.0 * (1 + markup / 100), 2), "cost_based")] * len(fmi),
      [(round(l.price_unit, 2), l.boss_sale_status) for l in fmi])

# a container entered as 40' DV and then changed to 40' HC (as on screen): its lines follow it, none stays beside
with Form(order) as form:
    with form.boss_container_ids.edit(1) as row:
        row.container_type_id = ref("boss_pricing.container_type_dv")
order.action_boss_update_costs()
with Form(order) as form:
    with form.boss_container_ids.edit(1) as row:
        row.container_type_id = ref("boss_pricing.container_type_hc")
check("a container type changed on screen: one THC line per container, none left for the old type",
      [("20", "DV"), ("40", "HC")],
      sorted((l.boss_container_size, l.boss_container_type_id.code) for l in order.order_line if l.product_id == thc))

# G4: the minimum margin warning of Odoo 17 (10 % of the cost per service group, 10 of tolerance; paid on behalf exact)
check("no margin warning while every group is above 10 % of its cost", False, bool(order.boss_margin_alert))
fad = order.order_line.filtered(lambda l: l.product_id.default_code == "FAD")
fad.boss_supplier_id = env.ref("o17_partner.res_partner_22998")  # ADUCEX: customs clearance tariff on boss20
order.action_boss_update_costs()
fad.price_unit = round(fad.purchase_price - 5.0, 2)  # 5 below the cost: margin -5 + 10 < 10 % of the cost
order.write({"order_line": [Command.create({"product_id": product("ARA").id, "product_uom_id": product("ARA").uom_id.id,
                                            "boss_manual_cost": 500.0, "boss_manual_cost_note": "[PRUEBA] aranceles"})]})
order.action_boss_update_costs()
ara = order.order_line.filtered(lambda l: l.product_id.default_code == "ARA")
ara.price_unit = 520.0  # typed with a margin: an amount paid on behalf is re-invoiced at the amount paid
alert = order.boss_margin_alert or ""
check("a service group sold below 10 % of its cost is warned (customs, typed below cost)", True,
      fad.product_id.categ_id.name in alert and "minimum" in alert)
check("an amount paid on behalf re-invoiced with a margin is warned (must be equal)", True, "paid on behalf" in alert)
check("the warning does not block the quotation (nothing about the margin in what stops it)", False,
      any("margin" in issue.lower() for issue in order._boss_readiness_issues()))

pricelist.item_ids.filtered(lambda i: i.base == "pricelist").unlink()
order2 = quotation()
fmi2 = order2.order_line.filtered(lambda l: l.product_id.default_code == "FMI")
check("without the last rule the freight has no selling price (the behaviour before)", ["missing"] * len(fmi2),
      fmi2.mapped("boss_sale_status"))
check("... and THC still takes its agreed price per size", [611.0, 622.0],
      sorted(order2.order_line.filtered(lambda l: l.product_id == thc).mapped("price_unit")))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
