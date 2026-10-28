"""Checks of the rules confirmed in the second meeting with Ángel (27/10/2026, seven recovered segments; ADR-009) on
boss20: service groups and the file summary by group, freight tariff date = ETD (quotation date while unknown),
one tariff per route with successive versions (1, 8, 13, 17 November) and approval on entry, the supplier-document
switch, one commercial carrier with several legal entities, cost asked case by case accepted and completed in the
file, fixed selling price independent of the supplier (THC 210 with MSC 180 / CMA 190) over cost + 20 %, USD rates,
rate quotations (unit rates, no total, containers before acceptance, no buying price printed), cargo unit type and
goods code to the file, header addresses hidden, selling/buying labels, two-decimal display. Every record is made
here and rolled back. Prints «CHECK PASS|FAIL …» and «RESULT n passed, m failed».
    dev/uat_run.sh check_meeting2.py boss20"""
from datetime import date, datetime

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form
from odoo.tools.binary import BinaryBytes

from odoo.addons.boss_services.models.service_groups import GROUP_XMLIDS, assign_service_groups

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


ref = env.ref
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
state = lambda code: env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", code)], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
Partner, Tariff, Order = env["res.partner"], env["boss.tariff"], env["sale.order"]
company = env.company
belal = env["res.users"].search([("login", "=", "devbms")], limit=1)
msc = Partner.browse(6)  # MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.
dv = ref("boss_pricing.container_type_dv")
doc = lambda text: BinaryBytes(text.encode(), filename="oferta.txt")  # noqa: E731
line_of = lambda o, code: o.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731

# --- service groups and tariff dates (the migration of boss_services does this on the upgrade) ---------------------
root = ref("boss_services.product_category_services")
for key, xmlid in GROUP_XMLIDS.items():
    if not ref(xmlid, raise_if_not_found=False):
        module, name = xmlid.split(".")
        category = env["product.category"].create({"name": f"[PRUEBA] {key}", "parent_id": root.id})
        env["ir.model.data"].create({"module": module, "name": name, "model": "product.category", "res_id": category.id})
assign_service_groups(env)
groups = {c: product(c).categ_id for c in ("FMI", "THC", "FAD", "TTE-CON", "ALM", "ARA", "SEG")}
check("1 service groups by code (Odoo 17 categories): freight, local, customs, inland, storage, duties, insurance",
      [ref(GROUP_XMLIDS[k]) for k in ("freight", "local", "customs", "inland", "storage", "duties", "insurance")],
      [groups[c] for c in ("FMI", "THC", "FAD", "TTE-CON", "ALM", "ARA", "SEG")])
check("1 freight services take the departure as tariff date, the others the key date",
      ("etd", "etd", "etd", "etd", "key", "key"),
      tuple(product(c).boss_tariff_date for c in ("FMI", "FME", "FAI", "FAE", "THC", "TTE-CON")))

# --- settings defaults (meeting part 2) --------------------------------------------------------------------------
check("2 settings: freight rates approved on entry ON, supplier document required ON (Cristina to confirm)",
      (True, True), (company.boss_spot_rate_auto_approve, company.boss_tariff_document_required))

# --- screen: header addresses hidden, pickup by the shipper, labels, containers heading --------------------------
arch = Order.get_view(view_type="form")["arch"]
views_deployed = "boss_rate_quotation" in arch  # the WIP mount loads code, not XML: these checks need the deploy
if views_deployed:
    from lxml import etree
    tree = etree.fromstring(arch.encode())
    hidden = {name: tree.xpath(f"//field[@name='{name}']")[0].get("invisible") for name in ("partner_invoice_id", "partner_shipping_id")}
    check("3 header: invoice and delivery address fields hidden", {"partner_invoice_id": "1", "partner_shipping_id": "1"}, hidden)
    check("3 pickup address chosen among the shipper's addresses", True,
          "[('id', 'child_of', boss_shipper_id or partner_id)]" in arch and "('id', 'child_of', partner_id), ('id', 'child_of', boss_shipper_id" not in arch)
    check("3 delivery address chosen among the consignee's addresses", True,
          "[('id', 'child_of', boss_consignee_id or partner_id)]" in arch)
    check("3 labels: final delivery is an estimate; selling price and buying cost; containers heading", (True, True, True, True),
          ("Final delivery to the client (estimate)" in arch, "Selling price (unit)" in arch, "Buying cost (unit)" in arch,
           "Containers of the shipment" in arch))
else:
    print("CHECK SKIP 3 quotation form (hidden header addresses, pickup by shipper, labels, containers heading): "
          "views not deployed yet, checked after the deploy")
fields_info = env["sale.order.line"].fields_get(["price_unit", "purchase_price"], ["min_display_digits", "digits"])
check("3 selling price and buying cost shown with two decimals unless more are needed (stored with 4)",
      (2, 2, 4, 4), (fields_info["price_unit"]["min_display_digits"], fields_info["purchase_price"]["min_display_digits"],
                     fields_info["price_unit"]["digits"][1], fields_info["purchase_price"]["digits"][1]))
check("3 supplier price amounts shown with two decimals", 2,
      env["boss.tariff.line"].fields_get(["unit_price"], ["min_display_digits"])["unit_price"]["min_display_digits"])

# --- parties --------------------------------------------------------------------------------------------------------
customer = Partner.create({"name": "[PRUEBA] Cliente reunión 2", "is_company": True, "country_id": ref("base.es").id,
                           "vat": "ESB12345674", "city": "Madrid", "state_id": state("M").id})
warehouse = Partner.create({"name": "[PRUEBA] Almacén Getafe", "parent_id": customer.id, "type": "delivery",
                            "city": "Getafe", "state_id": state("M").id, "country_id": ref("base.es").id})
shipper = Partner.create({"name": "[PRUEBA] Shenzhen Supplier Co", "is_company": True, "country_id": ref("base.cn").id,
                          "city": "Shenzhen"})
factory = Partner.create({"name": "[PRUEBA] Shenzhen factory", "parent_id": shipper.id, "type": "delivery",
                          "city": "Bao'an", "country_id": ref("base.cn").id})
trucker = Partner.create({"name": "[PRUEBA] Camionero caso por caso", "is_company": True, "supplier_rank": 1,
                          "country_id": ref("base.es").id})
cma = Partner.create({"name": "[PRUEBA] CMA CGM Iberica", "is_company": True, "supplier_rank": 1, "country_id": ref("base.es").id})
msc_group = Partner.create({"name": "[PRUEBA] Mediterranean Shipping Company (MSC)", "is_company": True})
msc_swiss = Partner.create({"name": "[PRUEBA] MSC Mediterranean Shipping Company SA (Suiza)", "is_company": True,
                            "country_id": ref("base.ch").id, "supplier_rank": 1, "boss_carrier_group_id": msc_group.id})
msc.boss_carrier_group_id = msc_group  # inside this rolled-back transaction only
check("4 carrier family: the Spanish and the Swiss MSC and the group are one family", True,
      set(msc._boss_carrier_family_ids()) == set(msc_swiss._boss_carrier_family_ids()) == {msc_group.id, msc.id, msc_swiss.id})


def quotation(carrier=msc, origin="CNSZX", eta=date(2026, 11, 16), etd=None, lines=("THC",), containers=1, **extra):
    values = {
        "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
        "boss_carrier_id": carrier.id, "boss_origin_country_id": ref("base.cn").id,
        "boss_origin_port_id": port(origin, "sea").id, "boss_destination_port_id": port("ESVLC", "sea").id,
        "boss_delivery_address_id": warehouse.id, "boss_eta": eta, "boss_etd": etd,
        "boss_container_ids": [Command.create({"size": "40", "container_type_id": dv.id, "quantity": containers})] if containers else [],
        "order_line": [Command.create({"product_id": product(c).id, "product_uom_id": product(c).uom_id.id,
                                       "boss_container_size": "40" if product(c).uom_id.boss_quantity_source == "container" else False,
                                       "boss_container_type_id": dv.id if product(c).uom_id.boss_quantity_source == "container" else False})
                       for c in lines],
    }
    values.update(extra)
    return Order.create(values)


# --- template fills the incoterm (S1) ------------------------------------------------------------------------------
with Form(Order) as form:
    form.partner_id = customer
    form.sale_order_template_id = env["sale.order.template"].search([("name", "=like", "IMB FOB · %")], limit=1)
    check("5 template IMB FOB fills the incoterm FOB, the direction, mode and load type", ("FOB", "import", "sea", "fcl"),
          (form.incoterm.code, form.boss_direction, form.boss_transport_mode, form.boss_load_type))
    form.boss_shipper_id = shipper
    form.boss_pickup_address_id = factory
    form.boss_packages = 72
tpl_order = form.save()
tpl_order.write({"boss_package_type": "CT", "boss_hs_code": "6109100010"})  # on the form once the views are deployed
check("5 pickup at the shipper's address, cargo unit type and goods code stored", (factory, 72, "CT", "6109100010"),
      (tpl_order.boss_pickup_address_id, tpl_order.boss_packages, tpl_order.boss_package_type, tpl_order.boss_hs_code))
file_values = tpl_order._boss_file_values()
check("5 unit type and goods code go to the file", ("CT", "6109100010"), (file_values["package_type"], file_values["hs_code"]))

# --- carrier family prices the quotation (S1: «we just need to say Mediterranean Shipping») -----------------------
thc_group = line_of(quotation(carrier=msc_group), "THC")
thc_swiss = line_of(quotation(carrier=msc_swiss), "THC")
thc_cma = line_of(quotation(carrier=cma), "THC")
check("6 quotation naming the MSC group: THC priced by the tariff of MSC Spain (253)", ("ok", 253.0),
      (thc_group.boss_cost_status, round(thc_group.boss_cost_amount, 2)))
check("6 quotation naming MSC Switzerland (legal entity): same tariff, same cost", ("ok", 253.0),
      (thc_swiss.boss_cost_status, round(thc_swiss.boss_cost_amount, 2)))
check("6 the supplier of the line stays the legal entity of the tariff (MSC Spain)", msc, thc_group.boss_tariff_line_id.partner_id)
check("6 another carrier (CMA) is not priced by MSC", "no_tariff", thc_cma.boss_cost_status)
check("6 the tariff scope reads as a route, origin -> destination", True, "CNSZX → ESVLC" in Tariff.browse(98).scope_summary)

# --- freight tariff date = ETD (S4); USD rate converted (S2) -----------------------------------------------------------
rate98 = Tariff.browse(98)  # MSC FMI 2026 v1: CNSZX -> ESVLC, 27/10-07/11/2026, 2,500 USD per 40', approved by Ángel
check("7 the approved weekly rate of Ángel: USD, one week, CNSZX -> ESVLC", ("approved", "USD", date(2026, 10, 27), date(2026, 11, 7)),
      (rate98.state, rate98.currency_id.name, rate98.valid_from, rate98.valid_to))
o = quotation(lines=("FMI", "THC"), eta=date(2026, 11, 16), etd=date(2026, 10, 30))
fmi, thc = line_of(o, "FMI"), line_of(o, "THC")
check("7 ocean freight priced on the ETD 30/10 (inside the week) although the ETA 16/11 is outside", ("ok", True),
      (fmi.boss_cost_status, fmi.boss_cost_amount > 0))
usd, eur = ref("base.USD"), ref("base.EUR")
expected_eur = usd._convert(2500.0, eur, company, fields.Date.to_date(o.date_order))
check("7 USD rate (2,500 USD per 40') converted to EUR on the line by the FX policy of the quotation date",
      ("USD", 2500.0, "EUR", round(expected_eur, 2)),
      (fmi.boss_cost_currency_id.name, round(fmi.boss_cost_amount, 2), fmi.currency_id.name, round(fmi.purchase_price, 2)))
check("7 explanation names the departure as tariff date", True, "departure (ETD)" in (fmi.boss_cost_explanation or ""))
check("7 THC (local charge) keeps the key date ETA", "ok", thc.boss_cost_status)
o.boss_etd = False
fmi._boss_recompute_cost()
check("7 ETD unknown: the quotation date (today, inside the week) chooses the rate", ("ok", True),
      (fmi.boss_cost_status, "quotation date" in (fmi.boss_cost_explanation or "")))
o.boss_etd = date(2026, 11, 20)
fmi._boss_recompute_cost()
check("7 ETD 20/11, after the week: no rate, manual amount", "manual", fmi.boss_cost_status)

# --- one tariff per route, successive versions (S3); approval on entry (S2) ---------------------------------------------
Wizard = env["boss.supplier.price.wizard"]
company.boss_tariff_document_required = False  # the switch Ángel asked for; the rates below come by e-mail
o = quotation(lines=("FMI",), origin="CNSHA", etd=date(2026, 11, 5), eta=date(2026, 12, 5))
fmi = line_of(o, "FMI")


def rate(order, valid_from, valid_to, price, submit=True):
    wiz = Wizard.with_context(default_sale_line_id=line_of(order, "FMI").id).create({})
    wiz.write({"valid_from": valid_from, "valid_to": valid_to, "unit_price": price, "submit": submit,
               "document_reference": f"[PRUEBA] MSC e-mail {valid_from}"})
    lineage = wiz.lineage_id
    wiz.action_save()
    return lineage


w0 = Wizard.with_context(default_sale_line_id=fmi.id).create({})
check("8 wizard: valid from today (this week's rate), one week, origin -> destination order, approval on entry",
      (date.today(), 6, "CNSHA", "ESVLC", True, False),
      (w0.valid_from, (w0.valid_to - w0.valid_from).days, w0.foreign_port_ids.code, w0.port_ids.code, w0.auto_approve, bool(w0.lineage_id)))
lineages = [rate(o, date(2026, 11, 1), date(2026, 11, 30), 2000.0)]
t1 = Tariff.search([("partner_id", "=", msc.id), ("foreign_port_ids.code", "=", "CNSHA"), ("line_ids.product_id", "=", product("FMI").id)],
                   order="id desc", limit=1)
check("8 rate of 1/11: new tariff, approved on entry by its author, with a note", ("approved", env.user, True),
      (t1.state, t1.approved_by_id, any("Approved on entry" in (m.body or "") for m in t1.message_ids)))
check("8 the quotation is priced at once (no refresh, no approver): 2,000", ("ok", 2000.0), (fmi.boss_cost_status, round(fmi.boss_cost_amount, 2)))
for valid_from, price in ((date(2026, 11, 8), 2100.0), (date(2026, 11, 13), 2200.0), (date(2026, 11, 17), 2300.0)):
    lineages.append(rate(o, valid_from, date(2026, 11, 30), price))
versions = Tariff.search([("lineage_id", "=", t1.lineage_id.id)], order="version")
check("8 replacements of 8, 13 and 17 November are versions 2, 3, 4 of the same tariff (each a version of the latest; no new tariff)",
      ([versions[0], versions[1], versions[2]], [1, 2, 3, 4], ["approved"] * 4, 1, True),
      (lineages[1:], versions.mapped("version"), versions.mapped("state"),
       len(Tariff.search([("name", "=", t1.name), ("partner_id", "=", msc.id)]).mapped("lineage_id")), "CNSHA → ESVLC" in t1.name))
check("8 old rates preserved: 2000, 2100, 2200, 2300", [2000.0, 2100.0, 2200.0, 2300.0],
      [v.line_ids.filtered(lambda l: l.product_id == product("FMI")).unit_price for v in versions])
priced = {}
for etd in (date(2026, 11, 5), date(2026, 11, 10), date(2026, 11, 15), date(2026, 11, 20), date(2026, 11, 25)):
    o.boss_etd = etd
    fmi._boss_recompute_cost()
    priced[etd.day] = (fmi.boss_cost_status, round(fmi.boss_cost_amount, 2), fmi.boss_tariff_line_id.tariff_id.version)
check("8 the newest version valid on the ETD wins: 5/11 v1 2000, 10/11 v2 2100, 15/11 v3 2200, 20/11 and 25/11 v4 2300",
      {5: ("ok", 2000.0, 1), 10: ("ok", 2100.0, 2), 15: ("ok", 2200.0, 3), 20: ("ok", 2300.0, 4), 25: ("ok", 2300.0, 4)}, priced)
rate(o, date(2026, 12, 1), date(2026, 12, 31), 2400.0)  # December rate entered early
o.boss_etd = date(2026, 11, 20)
fmi._boss_recompute_cost()
check("8 a December rate entered early (v5) does not touch November: 20/11 still 2300", ("ok", 2300.0, 4),
      (fmi.boss_cost_status, round(fmi.boss_cost_amount, 2), fmi.boss_tariff_line_id.tariff_id.version))
accepted = Order.search([("state", "=", "sale"), ("boss_pricing_frozen", "=", True)], order="id", limit=1)
if accepted:
    before = [(l.product_id.default_code, round(l.boss_cost_amount, 2), round(l.price_unit, 2)) for l in accepted.order_line.filtered("product_id")]
    accepted.order_line._boss_recompute_cost()
    check(f"8 {accepted.name}: accepted quotation unchanged by the new versions", before,
          [(l.product_id.default_code, round(l.boss_cost_amount, 2), round(l.price_unit, 2)) for l in accepted.order_line.filtered("product_id")])
company.boss_spot_rate_auto_approve = False
o2 = quotation(lines=("FMI",), origin="CNNGB", etd=date(2026, 11, 5), eta=date(2026, 12, 5))
rate(o2, date(2026, 11, 1), date(2026, 11, 30), 1900.0)
t_ngb = Tariff.search([("partner_id", "=", msc.id), ("foreign_port_ids.code", "=", "CNNGB")], order="id desc", limit=1)
check("8 approval on entry OFF: the rate waits for an approver and the freight stays manual", ("to_approve", "manual"),
      (t_ngb.state, line_of(o2, "FMI").boss_cost_status))
company.boss_tariff_document_required = True
try:
    rate(o2, date(2026, 12, 1), date(2026, 12, 31), 1950.0)
    error = ""
except UserError as e:
    error = str(e)
check("8 supplier document required ON: a rate without the file cannot be sent (message names the document)", True,
      "document" in error)
company.boss_spot_rate_auto_approve = True
company.boss_tariff_document_required = False

# --- fixed selling price independent of the supplier (S4, S5) over cost + 20 % ---------------------------------------
env["res.config.settings"]._boss_set_default_markup(20)
pricelist = env["product.pricelist"]._get_partner_pricelist_multi([customer.id])[customer.id]
env["product.pricelist.item"].create({"pricelist_id": pricelist.id, "applied_on": "1_product", "compute_price": "fixed",
                                      "product_tmpl_id": product("THC").product_tmpl_id.id, "product_id": product("THC").id,
                                      "uom_id": product("THC").uom_id.id, "fixed_price": 210.0})
cma_tariff = Tariff.create({
    "name": "[PRUEBA] CMA gastos locales", "partner_id": cma.id, "carrier_id": cma.id, "currency_id": ref("base.EUR").id,
    "valid_from": date(2026, 1, 1), "direction": "import", "transport_mode": "sea", "port_ids": [(6, 0, port("ESVLC", "sea").ids)],
    "scope_confirmed": True, "document": doc("[PRUEBA] CMA THC 190"), "document_name": "cma.txt",
    "line_ids": [Command.create({"product_id": product("THC").id, "uom_id": product("THC").uom_id.id, "unit_price": 190.0,
                                 "container_size": "40"})]})
cma_tariff.action_submit()
cma_tariff.with_user(belal).action_approve()
o = quotation(carrier=msc, origin="CNNGB", lines=("THC", "FMI"))  # Ningbo: no approved freight rate
thc, fmi = line_of(o, "THC"), line_of(o, "FMI")
check("9 THC with MSC: cost 253, selling price 210 agreed (pricelist), not cost + 20 %", (253.0, "agreed", 210.0),
      (round(thc.purchase_price, 2), thc.boss_sale_status, round(thc.price_unit, 2)))
fmi.write({"boss_manual_cost": 1500.0, "boss_manual_cost_note": "[PRUEBA] oferta"})
check("9 FMI without an agreed price: cost + 20 % (1500 -> 1800)", ("cost_based", 1800.0), (fmi.boss_sale_status, round(fmi.price_unit, 2)))
o.boss_carrier_id = cma
thc._boss_recompute_cost()
check("9 same shipment with CMA: THC cost 190, selling price still 210, margin follows the cost", (190.0, 210.0, "agreed", 20.0),
      (round(thc.purchase_price, 2), round(thc.price_unit, 2), thc.boss_sale_status, round(thc.price_unit - thc.purchase_price, 2)))
thc.price_unit = 215.0
o.boss_carrier_id = msc
thc._boss_recompute_cost()
check("9 a typed selling price survives a carrier/supplier change", ("manual", 253.0, 215.0),
      (thc.boss_sale_status, round(thc.purchase_price, 2), round(thc.price_unit, 2)))

# --- cost asked case by case (S6): accepted, completed in the file ------------------------------------------------------
o = quotation(carrier=msc, lines=("THC", "TTE-CON"))
thc, tte = line_of(o, "THC"), line_of(o, "TTE-CON")
tte.write({"boss_supplier_id": trucker.id, "boss_cost_on_request": True, "price_unit": 300.0})
thc.price_unit = 280.0
check("10 TTE-CON with a trucker that quotes case by case: cost on request, kind on request (not unknown)",
      ("on_request", "on_request", True), (tte.boss_cost_status, tte.boss_cost_kind, "case by case" in (tte.boss_cost_explanation or "")))
# the switch is no general exception: without a supplier, with missing shipment data, with a freight waiting for its
# offer, nothing changes (review 2, remark 2)
tte.boss_supplier_id = False
check("10 on request without a supplier named: stays «no supplier price», unknown cost", ("no_tariff", "unknown"),
      (tte.boss_cost_status, tte.boss_cost_kind))
tte.boss_supplier_id = trucker
ireneo = Partner.search([("name", "=", "IRENEO LOGÍSTICA, S.L.")], limit=1)
zaragoza = Partner.create({"name": "[PRUEBA] Almacén Zaragoza r2", "parent_id": customer.id, "type": "delivery",
                           "city": "Zaragoza", "state_id": state("Z").id, "country_id": ref("base.es").id})
o_z = quotation(carrier=msc, lines=("TTE-CON", "FMI"), origin="CNNGB", boss_delivery_address_id=zaragoza.id)
tte_z, fmi_z = line_of(o_z, "TTE-CON"), line_of(o_z, "FMI")
tte_z.write({"boss_supplier_id": ireneo.id, "boss_cost_on_request": True})
check("10 IRENEO has a price but the weights are missing: «missing shipment data» stays, not on request",
      ("missing_input", "unknown"), (tte_z.boss_cost_status, tte_z.boss_cost_kind))
fmi_z.write({"boss_supplier_id": msc.id, "boss_cost_on_request": True})
check("10 a freight without offer keeps «manual amount» (type the offer), not on request", ("manual", "unknown"),
      (fmi_z.boss_cost_status, fmi_z.boss_cost_kind))
try:
    o.action_confirm()
    error = ""
except UserError as e:
    error = str(e)
check("10 the quotation is accepted without the trucker's cost (no manager exception needed)", ("", "sale"), (error, o.state))
file = o.boss_expediente_id
need = file.cost_ids.filtered(lambda n: n.product_id == product("TTE-CON"))
check("10 the file shows the cost of TTE-CON as unknown, to be typed when the trucker answers", (True, 0.0, "on_request"),
      (need.cost_unknown, need.expected_unit_cost, need.accepted_cost_kind))
need.expected_unit_cost = 150.0
need.invalidate_recordset()  # the figures are computed on read (the form reloads them)
check("10 cost typed in the file: known, 150 still expected", (False, 150.0), (need.cost_unknown, round(need.pending_amount_company, 2)))

# --- summary by service group (S7): the Odoo 17 «Resumen» ------------------------------------------------------------
rows = dict(file._boss_summary_rows())
local, inland, total = rows.get(ref(GROUP_XMLIDS["local"]).name), rows.get(ref(GROUP_XMLIDS["inland"]).name), rows["Total"]
check("11 summary rows: local charges (THC) sale 280 cost 253; inland (TTE) sale 300 cost 150", (280.0, 253.0, 300.0, 150.0),
      (round(local["sale"], 2), round(local["pending"], 2), round(inland["sale"], 2), round(inland["pending"], 2)))
check("11 nothing invoiced yet: invoiced 0, to invoice = sale, actual cost 0", (0.0, 580.0, 0.0),
      (round(total["invoiced"], 2), round(total["to_invoice"], 2), round(total["actual"], 2)))
check("11 the total row equals the file figures (agreed sale, forecast cost, forecast margin)", True,
      abs(total["sale"] - file.amount_sale) < 0.01 and abs(total["forecast"] - file.amount_cost_forecast) < 0.01
      and abs(total["margin"] - file.amount_margin_forecast) < 0.01)
check("11 the summary table is on the file (groups, invoiced vs to invoice, expected vs actual cost)", True,
      all(s in (file.summary_html or "") for s in ("Service group", "Invoiced", "To invoice", "Cost still expected", "Actual cost")))
# the billing cycle (same steps as dev/uat_e2e.py): RFQ -> confirmed order -> performed -> posted vendor bill; partial
# customer invoice; partial credit note. Actual replaces expected (no double counting); invoiced is posted invoices.
file.action_create_rfqs()
po_msc = file.purchase_order_ids.filtered(lambda p: p.partner_id == msc)
po_msc.button_confirm()
file.cost_ids.filtered(lambda n: n.product_id == product("THC")).action_mark_performed()
po_msc.action_create_invoice()
bill = po_msc.invoice_ids[:1]
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0), ("company_id", "=", company.id)], limit=1)
bill.write({"invoice_date": date(2026, 11, 23), "ref": "[PRUEBA] MSC THC"})
bill.invoice_line_ids.tax_ids = purchase_0
bill.action_post()
thc_alloc = file.allocation_ids.filtered(lambda a: a.product_id == product("THC"))
inv = env["account.move"].browse(env["boss.invoice.services"].create({
    "expediente_id": file.id, "allocation_ids": [Command.set(thc_alloc.ids)]}).action_create()["res_id"])
inv.invoice_date = date(2026, 11, 24)
inv.action_post()
refund = inv._reverse_moves([{"ref": "[PRUEBA] abono parcial THC", "date": date(2026, 11, 26), "invoice_date": date(2026, 11, 26)}])
refund.invoice_line_ids.price_unit = 80.0
refund.action_post()
file.invalidate_recordset()
file.cost_ids.invalidate_recordset()
rows = dict(file._boss_summary_rows())
local, inland, total = rows[ref(GROUP_XMLIDS["local"]).name], rows[ref(GROUP_XMLIDS["inland"]).name], rows["Total"]
check("11 vendor bill posted (THC 253): actual cost 253 in local charges, nothing still expected there (not counted twice)",
      (253.0, 0.0, 253.0), (round(local["actual"], 2), round(local["pending"], 2), round(local["forecast"], 2)))
check("11 inland (TTE) still expected 150, not billed", (150.0, 0.0), (round(inland["pending"], 2), round(inland["actual"], 2)))
check("11 partial customer invoice (THC 280) less a credit note of 80: invoiced 200, to invoice 80; TTE 300 still to invoice",
      (200.0, 80.0, 0.0, 300.0), (round(local["invoiced"], 2), round(local["to_invoice"], 2), round(inland["invoiced"], 2),
                                  round(inland["to_invoice"], 2)))
check("11 totals after the cycle equal the file figures (invoiced, actual, pending, forecast, margin)", True,
      all(abs(a - b) < 0.01 for a, b in ((total["invoiced"], file.amount_invoiced), (total["actual"], file.amount_cost_actual),
                                          (total["pending"], file.amount_cost_pending), (total["forecast"], file.amount_cost_forecast),
                                          (total["margin"], file.amount_margin_forecast))))
check("11 figures: invoiced 200, actual 253, pending 150, forecast 403, margin 177 (580 - 403)", (200.0, 253.0, 150.0, 403.0, 177.0),
      (round(file.amount_invoiced, 2), round(file.amount_cost_actual, 2), round(file.amount_cost_pending, 2),
       round(file.amount_cost_forecast, 2), round(file.amount_margin_forecast, 2)))

# --- rate quotation (S6): 20' DV / 40' DV / 40' HC alternatives, document, chosen shipment, containers gate ---------
hc = ref("boss_pricing.container_type_hc")
o = quotation(carrier=msc, lines=("THC", "FMI"), containers=0, boss_rate_quotation=True)
thc, fmi = line_of(o, "THC"), line_of(o, "FMI")
o.write({"order_line": [
    Command.create({"product_id": product("THC").id, "product_uom_id": product("THC").uom_id.id, "boss_container_size": "20", "boss_container_type_id": dv.id}),
    Command.create({"product_id": product("THC").id, "product_uom_id": product("THC").uom_id.id, "boss_container_size": "40", "boss_container_type_id": hc.id}),
]})
thc20 = o.order_line.filtered(lambda l: l.product_id.default_code == "THC" and l.boss_container_size == "20")
thc40hc = o.order_line.filtered(lambda l: l.product_id.default_code == "THC" and l.boss_container_type_id == hc)
check("12 rate quotation without containers: 20' DV, 40' DV and 40' HC each priced for one container of its kind",
      (1.0, 1.0, 1.0, "ok", 253.0, "ok", "ok"), (thc20.product_uom_qty, thc.product_uom_qty, thc40hc.product_uom_qty,
                                                 thc.boss_cost_status, round(thc.boss_cost_amount, 2), thc20.boss_cost_status, thc40hc.boss_cost_status))
fmi.write({"boss_manual_cost": 1234.56, "boss_manual_cost_note": "[PRUEBA] nota interna oferta", "price_unit": 2000.0})
thc.price_unit, thc20.price_unit, thc40hc.price_unit = 300.0, 220.0, 310.0
html = env["ir.actions.report"]._render_qweb_html("sale.report_saleorder", [o.id])[0].decode()
if ref("boss_pricing_sale.report_saleorder_document_boss", raise_if_not_found=False):
    check("12 the document shows the three alternatives with their basis (20' DV, 40' DV, 40' HC) and no amount column or total",
          (True, True, True, False, False, False),
          ("20' DV" in html, "40' DV" in html, "40' HC" in html, "o_total_table" in html, ">Total<" in html, "o_price_total" in html))
else:
    print("CHECK SKIP 12 rate quotation document (unit rates, no total): report template not deployed yet, checked after the deploy")
check("12 no buying price, margin or internal note in the customer document", (False, False, False, False),
      ("1,234.56" in html, "1.234,56" in html, "nota interna" in html, "Margin" in html))
normal_html = env["ir.actions.report"]._render_qweb_html("sale.report_saleorder", [tpl_order.id])[0].decode()
check("12 a normal quotation document keeps its quantities and totals", (True, True, True),
      ("o_total_table" in normal_html, ">Total<" in normal_html, "o_price_total" in normal_html))
try:
    o.action_confirm()
    error = ""
except UserError as e:
    error = str(e)
check("12 acceptance waits for the containers of the shipment", True, "containers" in error and o.state == "draft")
o.boss_container_ids = [Command.create({"size": "40", "container_type_id": hc.id, "quantity": 1})]  # the client books 1 x 40' HC
try:
    o.action_confirm()
    error = ""
except UserError as e:
    error = str(e)
check("12 the alternatives the client did not book are named (THC 20' DV, THC 40' DV, FMI 40' DV), not silently dropped nor turned into containers",
      (True, True, True, False, 1), ("THC 20' DV" in error, "THC 40' DV" in error, "FMI 40' DV" in error, "40' HC" in error, len(o.boss_container_ids)))
(thc20 | thc).unlink()  # what the trash icon of the line does on screen
fmi.boss_container_type_id = hc  # the freight rate of the booked container (edited on the line)
fmi._boss_recompute_cost()
o.action_confirm()
check("12 after removing them the quotation is accepted: file with 1 x 40' HC and one THC need", ("sale", [("40", "HC")], 1),
      (o.state, [(c.size, c.container_type_id.code) for c in o.boss_expediente_id.container_ids],
       len(o.boss_expediente_id.cost_ids.filtered(lambda n: n.product_id == product("THC")))))
# an ordinary FCL quotation (not a rate quotation) keeps its behaviour: no new gate (review 2, remark 3)
o_plain = quotation(carrier=msc, lines=("THC",), containers=0)
check("12 an ordinary quotation without containers is not touched by the gate (per-container line quantity 0)", (0.0, ""),
      (line_of(o_plain, "THC").product_uom_qty, "" if not (lambda: o_plain._boss_check_containers())() else "x"))
# --- roles (review 2, remark 4): Wendy enters a rate from the quotation and uses it at once; Pepe cannot ------------
Users = env["res.users"].with_context(no_reset_password=True)
wendy = Users.create({"name": "[PRUEBA] Wendy (pricing, China)", "login": "prueba_wendy", "group_ids": [Command.set([
    ref("base.group_user").id, ref("sales_team.group_sale_salesman_all_leads").id, ref("boss_pricing.group_tariff_user").id])]})
pepe = Users.create({"name": "[PRUEBA] Pepe (sales only)", "login": "prueba_pepe", "group_ids": [Command.set([
    ref("base.group_user").id, ref("sales_team.group_sale_salesman_all_leads").id])]})
check("13 Wendy: tariff user and salesperson, not an approver; Pepe: salesperson only", (True, False, False),
      (wendy.has_group("boss_pricing.group_tariff_user"), wendy.has_group("boss_pricing.group_tariff_approver"),
       pepe.has_group("boss_pricing.group_tariff_user")))
company.boss_spot_rate_auto_approve = True
ow = env["sale.order"].with_user(wendy).create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_carrier_id": msc.id, "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id,
    "boss_destination_port_id": port("ESVLC", "sea").id, "boss_delivery_address_id": warehouse.id,
    "boss_eta": date(2026, 12, 5), "boss_etd": date(2026, 11, 5),
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": dv.id, "quantity": 1})],
    "order_line": [Command.create({"product_id": product(c).id, "product_uom_id": product(c).uom_id.id,
                                   "boss_container_size": "40", "boss_container_type_id": dv.id}) for c in ("FMI", "THC")]})
fmi_w = ow.order_line.filtered(lambda l: l.product_id.default_code == "FMI")
wiz = Wizard.with_user(wendy).with_context(default_sale_line_id=fmi_w.id).create({})
wiz.write({"valid_from": date(2026, 11, 1), "valid_to": date(2026, 11, 30), "unit_price": 2050.0,
           "document_reference": "[PRUEBA] MSC e-mail Wendy"})
wiz.action_save()
t_w = fmi_w.boss_tariff_line_id.tariff_id
check("13 Wendy's rate: version of the Shanghai tariff, approved on entry BY WENDY, priced at once", (True, "approved", wendy, "ok", 2050.0),
      (t_w.lineage_id == t1.lineage_id, t_w.state, t_w.approved_by_id, fmi_w.boss_cost_status, round(fmi_w.boss_cost_amount, 2)))
check("13 the entry is recorded: created by Wendy, note «Approved on entry» in the tariff", (wendy, True),
      (t_w.create_uid, any("Approved on entry" in (m.body or "") for m in t_w.message_ids)))
ow.order_line.filtered(lambda l: l.product_id.default_code == "THC").price_unit = 300.0
fmi_w.price_unit = 2500.0
ow.with_user(wendy).action_confirm()
check("13 Wendy completes the quotation without waiting for anyone: accepted, file opened", ("sale", True),
      (ow.state, bool(ow.boss_expediente_id)))
try:
    Wizard.with_user(pepe).with_context(default_sale_line_id=fmi_w.id).create({})
    pepe_error = ""
except AccessError as e:
    pepe_error = "access"
check("13 Pepe (no tariff rights) cannot enter supplier prices", "access", pepe_error)
company.boss_spot_rate_auto_approve = False
ow2 = ow.copy({"boss_origin_port_id": port("CNNGB", "sea").id})
fmi_w2 = ow2.order_line.filtered(lambda l: l.product_id.default_code == "FMI")
wiz = Wizard.with_user(wendy).with_context(default_sale_line_id=fmi_w2.id).create({})
wiz.write({"valid_from": date(2026, 11, 1), "valid_to": date(2026, 11, 30), "unit_price": 1900.0, "document_reference": "[PRUEBA]"})
wiz.action_save()
t_w2 = Tariff.search([("partner_id", "=", msc.id), ("foreign_port_ids.code", "=", "CNNGB")], order="id desc", limit=1)
try:
    t_w2.with_user(wendy).action_approve()
    approve_error = ""
except UserError as e:
    approve_error = "approver only"
check("13 approval on entry OFF: Wendy's rate waits, she cannot approve it herself, the freight stays manual",
      ("to_approve", "approver only", "manual"), (t_w2.state, approve_error, fmi_w2.boss_cost_status))
company.boss_spot_rate_auto_approve = True
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if len(results) - sum(results):  # a failed check fails the run (dev/uat_run.sh records the exit status)
    raise SystemExit(1)
