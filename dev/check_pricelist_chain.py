"""Check of roadmap item 3, G1 (boss20, rolled back): selling prices per container size and a customer pricelist that
falls back to the general «cost + %» rule.

A [PRUEBA] customer with its own pricelist agrees THC per container size (fictitious 611 for 20', 622 for 40'); its last
rule is «based on the general pricelist». A sea import FCL quotation (template IMB FOB, MSC, Xingang → Valencia,
1×20' DV + 1×40' HC) must give: THC 20' 611 and THC 40' 622 (agreed), the services it does not agree priced by the
general rule from their cost (cost + %), the freight with a manual cost priced the same way, and, without the last rule,
those services without a selling price (the behaviour before). Prints «CHECK PASS|FAIL …» and «RESULT …».
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
    for line in order.order_line.filtered(lambda l: l.product_id.default_code in ("THC", "BL", "FMI")):
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
bl = order.order_line.filtered(lambda l: l.product_id.default_code == "BL")
expected_bl = round(bl.purchase_price * (1 + markup / 100), 2)
check("BL, not agreed, falls back to the general rule: cost + %", (expected_bl, "cost_based", True),
      (round(bl.price_unit, 2), bl.boss_sale_status, bool(bl.purchase_price)))
print(f"      {bl.boss_sale_explanation}")
fmi = order.order_line.filtered(lambda l: l.product_id.default_code == "FMI")
check("freight with a manual cost falls back to the general rule too",
      [(round(1000.0 * (1 + markup / 100), 2), "cost_based")] * len(fmi),
      [(round(l.price_unit, 2), l.boss_sale_status) for l in fmi])

pricelist.item_ids.filtered(lambda i: i.base == "pricelist").unlink()
order2 = quotation()
fmi2 = order2.order_line.filtered(lambda l: l.product_id.default_code == "FMI")
check("without the last rule the freight has no selling price (the behaviour before)", ["missing"] * len(fmi2),
      fmi2.mapped("boss_sale_status"))
check("... and THC still takes its agreed price per size", [611.0, 622.0],
      sorted(order2.order_line.filtered(lambda l: l.product_id == thc).mapped("price_unit")))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
