"""Check of the plan after the meeting with Ángel, phase B (boss20, rolled back): FCL ocean freight bought from the
main carrier in the file when no tariff names its supplier, optional services shown but kept out of the
totals of a rate quotation, services found by their name in Spanish or English or by their description, Spanish dates
in the English interface. Fictitious records only.
    dev/uat_run.sh check_phase_b.py boss20"""
from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


Partner = env["res.partner"]
customer = Partner.create({"name": "[PRUEBA] Cliente fase B", "is_company": True})
carrier_a = Partner.create({"name": "[PRUEBA] Naviera A", "is_company": True, "supplier_rank": 1})
coloader = Partner.create({"name": "[PRUEBA] Consolidador", "is_company": True, "supplier_rank": 1})
dv = env.ref("boss_pricing.container_type_dv")

check("1 FCL ocean freight is bought from the main carrier; LCL freight and THC stay «any supplier»",
      ("carrier", "carrier", "any", "any"),
      tuple(product(c).boss_supplier_role for c in ("FMI", "FME", "FMI-LCL", "THC")))


def line(code, **extra):
    return Command.create(dict({"product_id": product(code).id, "product_uom_id": product(code).uom_id.id}, **extra))


order = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_carrier_id": carrier_a.id,
    "order_line": [line("FMI", boss_container_size="20", boss_container_type_id=dv.id),
                   line("FMI", boss_container_size="40", boss_container_type_id=dv.id, boss_supplier_id=coloader.id),
                   line("THC", boss_container_size="20", boss_container_type_id=dv.id)]})
fmi_free, fmi_hand = order.order_line.filtered(lambda l: l.product_id.default_code == "FMI").sorted("id")
thc = order.order_line.filtered(lambda l: l.product_id.default_code == "THC")
check("2 the quotation line keeps its supplier free (a tariff of an agent or another entity of the carrier prices it)",
      (Partner, coloader), (fmi_free.boss_supplier_id, fmi_hand.boss_supplier_id))
file = env["boss.expediente"].create({"partner_id": customer.id, "business": "boss", "direction": "import",
                                      "transport_mode": "sea", "load_type": "fcl", "carrier_id": carrier_a.id})
Cost = env["boss.expediente.cost"]
partner = lambda l: Partner.browse(Cost._values_from_sale_line(l, file)["partner_id"])  # noqa: E731
check("3 in the file the freight without a tariff is bought from the main carrier; a chosen supplier stays; THC none",
      (carrier_a, coloader, Partner), (partner(fmi_free), partner(fmi_hand), partner(thc)))

# the supplier list of a line: only suppliers with an approved price of the service, valid on its date
from datetime import date, timedelta  # noqa: E402
tariff = env["boss.tariff"].create({
    "name": "[PRUEBA] THC naviera A", "partner_id": carrier_a.id, "valid_from": date.today() - timedelta(days=1),
    "valid_to": date.today() + timedelta(days=60),
    "line_ids": [Command.create({"product_id": product("THC").id, "uom_id": product("THC").uom_id.id,
                                 "unit_price": 1.0})]})
tariff._workflow_write({"state": "approved"})  # the check's own [PRUEBA] tariff, approved without the buttons
thc.invalidate_recordset(["boss_supplier_ids"])
check("3b the supplier list of a THC line offers the supplier with a valid THC price, not one without a price",
      (True, False), (carrier_a in thc.boss_supplier_ids, coloader in thc.boss_supplier_ids))
china = env["boss.tariff"].create({
    "name": "[PRUEBA] THC consolidador origen China", "partner_id": coloader.id, "country_ids": [Command.set(env.ref("base.cn").ids)],
    "valid_from": date.today() - timedelta(days=1), "valid_to": date.today() + timedelta(days=60),
    "line_ids": [Command.create({"product_id": product("THC").id, "uom_id": product("THC").uom_id.id, "unit_price": 1.0})]})
china._workflow_write({"state": "approved"})
hk = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_origin_country_id": env.ref("base.hk").id, "boss_eta": date.today() + timedelta(days=20),
    "order_line": [line("THC", boss_container_size="20", boss_container_type_id=dv.id, boss_supplier_id=coloader.id)]})
thc_hk = hk.order_line
check("3d a price for origin China is not offered for a shipment from Hong Kong, and the line says which price exists",
      (False, "no_tariff", True), (coloader in thc_hk.boss_supplier_ids - thc_hk.boss_supplier_id, thc_hk.boss_cost_status,
                                   "[PRUEBA] THC consolidador origen China" in (thc_hk.boss_cost_explanation or "")))
tariff._workflow_write({"valid_from": date.today() - timedelta(days=10), "valid_to": date.today() - timedelta(days=1)})
thc.invalidate_recordset(["boss_supplier_ids"])
check("3c ... and no longer once its price has expired", False, carrier_a in thc.boss_supplier_ids)

# optional services in a rate quotation
rate = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_rate_quotation": True,
    "order_line": [line("THC", boss_container_size="20", boss_container_type_id=dv.id, price_unit=100.0, sequence=1),
                   Command.create({"display_type": "line_section", "name": "[PRUEBA] Opcionales", "is_optional": True,
                                   "sequence": 2}),
                   line("BL", price_unit=50.0, sequence=3)]})
for l in rate.order_line.filtered(lambda l: not l.display_type):
    l.price_unit = 100.0 if l.product_id.default_code == "THC" else 50.0
matrix = rate._boss_rate_matrix()
optional = [r for r in matrix["rows"] if r.get("optional")]
check("4 a service in an optional section is shown, marked optional and kept out of the total", (1, 100.0),
      (len(optional), round(matrix["totals"][matrix["columns"][0]["key"]], 2)))

# search of services
fmi = product("FMI")
spanish = fmi.with_context(lang="es_ES").name
english = fmi.with_context(lang="en_US").name
Product = env["product.product"].with_context(lang="en_US")
found_es = Product.name_search(spanish[:20], limit=50)
found_en = Product.with_context(lang="es_ES").name_search(english[:20], limit=50)
word = "PRUEBAzunchado"  # a word written in the description inside this transaction only
fmi.product_tmpl_id.with_context(lang="en_US").description = f"<p>[PRUEBA] {word}</p>"
found_desc = Product.name_search(word, limit=80)
check("5 a service is found by its Spanish name in English, by its English name in Spanish, and by its description",
      (True, True, True), (fmi.id in [i for i, _n in found_es], fmi.id in [i for i, _n in found_en],
                           bool(word) and fmi.id in [i for i, _n in found_desc]))
check("6 English interface with Spanish dates, week from Monday", ("%d/%m/%Y", "1"),
      (env["res.lang"]._lang_get("en_US").date_format, env["res.lang"]._lang_get("en_US").week_start))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
