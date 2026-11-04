"""Check of the rate quotation as the commercial team sends it (plan of 04/11/2026, phase A; Ángel's sheet «SEA FCL»),
boss20, rolled back: rates by container size in columns, the basis of each price, the total of one container of each
size (services per B/L or shipment counted once), the exchange rate and the totals in the currency of the supplier
prices, the conditions of the template in the customer's language, the incoterm of the template, and a maximum per
shipment. Fictitious records and prices only.
    dev/uat_run.sh check_rate_matrix.py boss20"""
from datetime import date, timedelta
from html import unescape

from odoo import Command
from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


Order = env["sale.order"]
dv = env.ref("boss_pricing.container_type_dv")
hc = env.ref("boss_pricing.container_type_hc")
customer = env["res.partner"].create({"name": "[PRUEBA] Cliente tarifas", "is_company": True, "lang": "es_ES",
                                      "country_id": env.ref("base.es").id})
template = env["sale.order.template"].search([("name", "=like", "IMB FOB · %")], limit=1)

# 1. the template gives the incoterm and its conditions, in the customer's language
with Form(Order) as form:
    form.partner_id = customer
    form.sale_order_template_id = template
order = form.save()
check("1 the IMB FOB template gives the incoterm FOB and its conditions in Spanish", ("FOB", True),
      (order.incoterm.code, "Condiciones de la oferta" in str(order.note or "")))

# 2. rates by size: THC 20' DV and 40' HC, BL once per shipment
order.write({"boss_rate_quotation": True, "order_line": [Command.clear()] + [
    Command.create({"product_id": product("THC").id, "product_uom_id": product("THC").uom_id.id,
                    "boss_container_size": size, "boss_container_type_id": ctype.id, "price_unit": price})
    for size, ctype, price in (("20", dv, 350.0), ("40", hc, 440.0))] + [
    Command.create({"product_id": product("BL").id, "product_uom_id": product("BL").uom_id.id, "price_unit": 85.0})]})
order.order_line.write({"tax_ids": [Command.clear()]})
for line, price in zip(order.order_line.sorted("id"), (350.0, 440.0, 85.0)):
    line.price_unit = price  # typed prices: the customer's rates
matrix = order._boss_rate_matrix()
labels = [c["label"] for c in matrix["columns"]]
totals = [round(matrix["totals"][c["key"]], 2) for c in matrix["columns"]]
check("2 one column per container size and type, one row per service, the B/L in every column",
      (["20' DV", "40' HC"], 2, True),
      (labels, len([r for r in matrix["rows"] if r["kind"] == "line"]),
       all(len(r["cells"]) == 2 for r in matrix["rows"] if r["kind"] == "line" and "BL" in r["name"])))
check("3 the total of each column is one container of that size in one shipment (THC + BL)", [435.0, 525.0], totals)

# 3. other currency of the supplier prices: rate used and totals in it
usd = env.ref("base.USD")
thc20 = order.order_line.filtered(lambda l: l.boss_container_size == "20")
env.cr.execute("UPDATE sale_order_line SET boss_cost_currency_id = %s WHERE id = %s", (usd.id, thc20.id))
thc20.invalidate_recordset(["boss_cost_currency_id"])
matrix = order._boss_rate_matrix()
other = matrix["others"][:1]
rate = order.currency_id._convert(1.0, usd, order.company_id, order.date_order.date(), round=False)
check("4 a supplier price in USD: the rate of Odoo and the totals in USD are given", ("USD", True),
      (other[0]["currency"].name if other else None,
       bool(other) and abs(other[0]["totals"][matrix["columns"][0]["key"]] - 435.0 * rate) < 0.01))

# 4. the customer document: matrix, totals per container, no quantities, no shipment total, no buying price
order.order_line.write({"boss_manual_cost": 123.45})
html = env["ir.actions.report"].with_context(lang="en_US")._render_qweb_html("sale.report_saleorder", order.ids)[0].decode()
text = unescape(html)
check("5 the PDF shows the rates by size with their totals and exchange rate, not the standard lines or total",
      (True, True, True, True, False, False),
      ("boss_rate_matrix" in html, "20' DV" in text and "40' HC" in text, "Total for one container" in html,
       "Exchange rate" in html, "o_total_table" in html, "123.45" in html or "123,45" in html))
shipment = order.copy({"boss_rate_quotation": False})
normal = env["ir.actions.report"]._render_qweb_html("sale.report_saleorder", shipment.ids)[0].decode()
check("6 a shipment quotation keeps the standard lines and total", (False, True),
      ("boss_rate_matrix" in normal, "o_total_table" in normal))

# 5. a maximum per shipment («máx. 90 € por embarque»): 60 per container, 2 containers, at most 90
supplier = env["res.partner"].create({"name": "[PRUEBA] Proveedor con máximo", "is_company": True, "supplier_rank": 1})
service = product("THC")
tariff = env["boss.tariff"].create({
    "name": "[PRUEBA] Máximo por embarque", "partner_id": supplier.id, "valid_from": date.today() - timedelta(days=1),
    "valid_to": date.today() + timedelta(days=30),
    "line_ids": [Command.create({"product_id": service.id, "uom_id": service.uom_id.id, "unit_price": 60.0,
                                 "max_amount": 90.0})]})
tariff._workflow_write({"state": "approved"})  # the check's own [PRUEBA] tariff, approved without the buttons
port = lambda code: env["boss.port"].search([("code", "=", code), ("kind", "=", "sea")], limit=1)  # noqa: E731
capped = Order.create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_carrier_id": supplier.id, "boss_origin_country_id": env.ref("base.cn").id,
    "boss_origin_port_id": port("CNSZX").id, "boss_destination_port_id": port("ESVLC").id,
    "boss_eta": date.today() + timedelta(days=10),
    "boss_container_ids": [Command.create({"size": "20", "container_type_id": dv.id, "quantity": 2})],
    "order_line": [Command.create({"product_id": service.id, "product_uom_id": service.uom_id.id,
                                   "boss_container_size": "20", "boss_container_type_id": dv.id,
                                   "boss_supplier_id": supplier.id})]})
line = capped.order_line[:1]
if line.boss_cost_status != "ok":
    print("      ", " ".join((line.boss_cost_explanation or "").split())[:300])
check("7 a maximum per shipment: 2 containers × 60 = 120, charged 90", (2.0, "ok", 90.0),
      (line.product_uom_qty, line.boss_cost_status, round(line.boss_cost_amount, 2)))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
