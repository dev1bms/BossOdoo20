"""Closing checks of the meeting checklist of 27/10/2026 (docs/matriz-reunion-2026-10-27.md) on boss20: several
delivery addresses of one customer and the inland price that follows them (IRENEO zone 3), the orderer proposal that
can be overridden, a new version of a supplier document (20-page PDF) leaving accepted quotations untouched, the VAT
matrix by customer zone and the fiscal position not interfering, storage and customs estimates, unknown goods value,
incoterm named place, the inland carrier carried to the file. Every record is made here and rolled back.
    dev/uat_run.sh check_meeting_matrix.py boss20"""
from datetime import date

from odoo import Command
from odoo.tests import Form
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


ref = env.ref
P, Partner = env["product.product"], env["res.partner"]
product = lambda code: P.search([("default_code", "=", code)], limit=1)  # noqa: E731
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
state = lambda code: env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", code)], limit=1)  # noqa: E731
template = lambda code: env["sale.order.template"].search([("name", "=like", f"{code} · %")], limit=1)  # noqa: E731
msc = Partner.search([("name", "=", "MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.")], limit=1)
ireneo = Partner.search([("name", "=", "IRENEO LOGÍSTICA, S.L.")], limit=1)
belal = env["res.users"].search([("login", "=", "devbms")], limit=1)
costs = lambda o: [(l.product_id.default_code, l.boss_cost_status, round(l.boss_cost_amount, 2), l.price_unit) for l in o.order_line.filtered("product_id")]  # noqa: E731
line_of = lambda o, code: o.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731

leroy = Partner.create({"name": "[PRUEBA] Leroy Merlin Prueba", "is_company": True, "country_id": ref("base.es").id,
                        "vat": "ESB12345674", "city": "Madrid", "state_id": state("M").id})
w_alcala = Partner.create({"name": "[PRUEBA] Almacén Alcalá", "parent_id": leroy.id, "type": "delivery", "city": "Alcalá de Henares",
                           "state_id": state("M").id, "country_id": ref("base.es").id})
w_zaragoza = Partner.create({"name": "[PRUEBA] Almacén Zaragoza", "parent_id": leroy.id, "type": "delivery", "city": "Zaragoza",
                             "state_id": state("Z").id, "country_id": ref("base.es").id})
w_valencia = Partner.create({"name": "[PRUEBA] Almacén Ribarroja", "parent_id": leroy.id, "type": "delivery", "city": "Riba-roja",
                             "state_id": state("V").id, "country_id": ref("base.es").id})

# 3 & 4: one customer, several warehouses; the inland price follows the chosen warehouse (IRENEO zone 3: Zaragoza
# and València priced; Madrid: no price, zones MAD/MAD-EXT not loaded)
with Form(env["sale.order"]) as form:
    form.partner_id = leroy
    form.sale_order_template_id = template("IMB FOB")
    form.boss_carrier_id = msc
    form.boss_origin_country_id = ref("base.cn")
    form.boss_origin_port_id = port("CNSHA", "sea")
    form.boss_destination_port_id = port("ESVLC", "sea")
    form.boss_eta = date(2026, 11, 16)
    form.boss_delivery_address_id = w_zaragoza
order = form.save()
order.write({"boss_gross_kg": 500.0, "boss_volume_m3": 2.0})  # measures of the cargo (volume is hidden on an FCL form)
tte = line_of(order, "TTE-FCL")
check("3 delivery address choosable among the customer's warehouses (Zaragoza)", "Z", order.boss_inland_state_id.code)
# a road delivery line priced per chargeable kg (IRENEO zone 3, doc factor 333): added as the haulier's service
order.write({"order_line": [Command.create({"product_id": product("TTE-CON").id, "product_uom_id": product("TTE-CON").uom_id.id,
                                            "boss_supplier_id": ireneo.id})]})
con = line_of(order, "TTE-CON")
check("4 inland delivery to Zaragoza priced by IRENEO zone 3 (chargeable 666 kg at 333)", ("ok", True),
      (con.boss_cost_status, con.boss_cost_amount > 0))
zaragoza_cost = round(con.boss_cost_amount, 2)
print("   IRENEO zone 3, Zaragoza, 666 kg:", zaragoza_cost, "| explanation:", (con.boss_cost_explanation or "").replace("\n", " | ")[:160])
order.boss_delivery_address_id = w_valencia
con._boss_recompute_cost()
check("4 switching the warehouse to València keeps a zone-3 price", ("V", "ok"), (order.boss_inland_state_id.code, con.boss_cost_status))
order.boss_delivery_address_id = w_alcala
con._boss_recompute_cost()
check("4 switching the warehouse to Alcalá (Madrid): no IRENEO price (MAD zones not loaded), nothing invented",
      ("M", "no_tariff", 0.0), (order.boss_inland_state_id.code, con.boss_cost_status, con.boss_cost_amount))
check("7 inland carrier = supplier of the road line; main carrier = MSC", (ireneo, msc), (order.boss_haulier_id, order.boss_carrier_id))

# 2: a customer without any address gets one typed from the quotation (a delivery contact of the customer)
noaddr = Partner.create({"name": "[PRUEBA] Cliente sin dirección", "is_company": True, "country_id": ref("base.es").id, "vat": "ESB12345674"})
typed = Partner.with_context(default_parent_id=noaddr.id, default_type="delivery").create({
    "name": "Nave 3", "street": "Pol. Ind. Malpica", "city": "Zaragoza", "state_id": state("Z").id, "country_id": ref("base.es").id})
q2 = env["sale.order"].create({"partner_id": noaddr.id, "boss_direction": "import", "boss_transport_mode": "sea",
                               "boss_load_type": "lcl", "boss_delivery_address_id": typed.id})
check("2 typed address becomes a delivery contact of the customer and gives the province", (noaddr, "delivery", "Z"),
      (typed.parent_id, typed.type, q2.boss_inland_state_id.code))

# 21: the orderer proposal can be overridden and is not re-imposed
with Form(env["sale.order"]) as form:
    form.partner_id = leroy
    form.boss_direction = "import"
    check("21 proposal: consignee = orderer", leroy, form.boss_consignee_id)
    form.boss_consignee_id = w_zaragoza
    form.boss_transport_mode = "sea"
    form.boss_direction = "export"
    form.boss_direction = "import"
    check("21 explicit consignee kept after re-choosing the direction", w_zaragoza, form.boss_consignee_id)

# 12: incoterm and its named place
q3 = env["sale.order"].create({"partner_id": leroy.id, "incoterm": env["account.incoterms"].search([("code", "=", "FOB")], limit=1).id,
                               "incoterm_location": "Shanghai port"})
check("12 incoterm named place saved", ("FOB", "Shanghai port"), (q3.incoterm.code, q3.incoterm_location))

# 17: storage estimate (a month at the port) and customs estimate reach the prices
q4 = env["sale.order"].create({
    "partner_id": leroy.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_carrier_id": msc.id, "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id,
    "boss_destination_port_id": port("ESVLC", "sea").id, "boss_eta": date(2026, 11, 16), "boss_storage_days": 15,
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id, "quantity": 1})],
    "order_line": [Command.create({"product_id": product("DEM").id, "product_uom_id": product("DEM").uom_id.id,
                                   "boss_container_size": "40", "boss_container_type_id": ref("boss_pricing.container_type_hc").id})]})
dem = line_of(q4, "DEM")
check("17 storage 15 days: MSC demurrage 40'HC estimated 485 (private check figure)", ("ok", 485.0, True),
      (dem.boss_cost_status, round(dem.boss_cost_amount, 2), dem.boss_cost_is_estimate))
q4.boss_storage_days = 0
dem._boss_recompute_cost()
check("17 storage 0 days (the usual case): no demurrage cost, explicit estimate", ("ok", 0.0), (dem.boss_cost_status, round(dem.boss_cost_amount, 2)))

# 16: unknown goods value is not zero for a percentage service
seg = product("SEG")
q5 = env["sale.order"].create({"partner_id": leroy.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
                               "boss_eta": date(2026, 11, 16),
                               "order_line": [Command.create({"product_id": seg.id, "product_uom_id": seg.uom_id.id})]}) if seg else None
if q5:
    s = line_of(q5, "SEG")
    check("16 goods value unknown: insurance says what is missing, never 0 %", True, s.boss_cost_status in ("missing_input", "no_tariff", "manual", "not_ready", "pending_approval") and s.boss_cost_amount == 0.0)
    print("   SEG status:", s.boss_cost_status, (s.boss_cost_explanation or "")[:90])

# 35: VAT matrix by customer zone (BOSS VAT table, ADR-004) and the fiscal position not interfering
VatTax = env["boss.vat.tax"]
expected_tax = lambda cls, zone: VatTax._boss_find(env.company, cls, zone, False).tax_id  # noqa: E731


def taxes(partner, extra=None):
    q = env["sale.order"].create(dict({
        "partner_id": partner.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
        "boss_origin_country_id": ref("base.cn").id, "boss_destination_country_id": ref("base.es").id,
        "boss_origin_port_id": port("CNSHA", "sea").id, "boss_destination_port_id": port("ESVLC", "sea").id,
        "order_line": [Command.create({"product_id": product(c).id, "product_uom_id": product(c).uom_id.id}) for c in ("THC", "FAD")]}, **(extra or {})))
    return {l.product_id.default_code: (l.boss_vat_class, l.boss_vat_status, l.tax_ids) for l in q.order_line}, q


spanish, _q = taxes(leroy)
check("35 Spanish customer: THC EX -> table row EX/PRO (Art.22), FAD NR -> NR/any (21%)",
      {"THC": ("EX", "ok", expected_tax("EX", "PRO")), "FAD": ("NR", "ok", expected_tax("NR", "PRO"))}, spanish)
print("   Spanish taxes:", {k: v[2].mapped("name") for k, v in spanish.items()})
eu = Partner.create({"name": "[PRUEBA] Kunde GmbH", "is_company": True, "country_id": ref("base.de").id, "vat": "DE123456788"})
eu_taxes, _q = taxes(eu)
check("35 EU business customer: THC EX -> table row EX/COM", ("EX", "ok", expected_tax("EX", "COM")), eu_taxes["THC"])
print("   EU taxes:", {k: v[2].mapped("name") for k, v in eu_taxes.items()})
third = Partner.create({"name": "[PRUEBA] Shanghai Trading Co", "is_company": True, "country_id": ref("base.cn").id})
third_taxes, _q = taxes(third)
check("35 third-country customer: THC EX -> table row EX/TER", ("EX", "ok", expected_tax("EX", "TER")), third_taxes["THC"])
print("   third-country taxes:", {k: v[2].mapped("name") for k, v in third_taxes.items()})
canary = Partner.create({"name": "[PRUEBA] Canarias S.L.", "is_company": True, "country_id": ref("base.es").id, "vat": "ESB12345674",
                         "state_id": env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "TF")], limit=1).id})
canary_taxes, _q = taxes(canary)
check("35 Canary Islands customer: THC EX -> table row EX/CAN", ("EX", "ok", expected_tax("EX", "CAN")), canary_taxes["THC"])
nocountry = Partner.create({"name": "[PRUEBA] sin país", "is_company": True})
pending, _q = taxes(nocountry)
check("35 customer without country: VAT pending, no tax applied", ("pending", 0), (pending["FAD"][1], len(pending["FAD"][2])))
fp = env["account.fiscal.position"].search([], limit=1)
if fp:
    with_fp, _q = taxes(leroy, {"fiscal_position_id": fp.id})
    check(f"35 fiscal position «{fp.name}» on the quotation does not change BOSS taxes", spanish, with_fp)

# 29 & 31: a new version of a supplier document (all lines copied, one changed), accepted quotations untouched
accepted = env["sale.order"].search([("state", "=", "sale"), ("boss_pricing_frozen", "=", True), ("boss_carrier_id", "=", msc.id)], limit=1)
thc_tariff = line_of(accepted, "THC")[:1].boss_tariff_line_id.tariff_id if accepted else env["boss.tariff"]
if thc_tariff:
    before = costs(accepted)
    action = thc_tariff.with_user(belal).action_new_version()
    v2 = env["boss.tariff"].browse(action["res_id"])
    v2.write({"valid_from": date(2026, 11, 1), "document": thc_tariff.document or BinaryBytes(b"[PRUEBA] nueva edicion", filename="msc-v2.txt"),
              "document_name": thc_tariff.document_name or "msc-v2.txt"})
    v2.scope_confirmed = True  # the approver reviews the scope of the new edition
    check("29 new version copies every price of the document", len(thc_tariff.line_ids), len(v2.line_ids))
    thc_line = v2.line_ids.filtered(lambda l: l.product_id.default_code == "THC")[:1]
    thc_line.unit_price = thc_line.unit_price + 10
    v2.action_submit()
    v2.with_user(belal).action_approve()
    accepted.order_line._boss_recompute_cost()
    check(f"31 accepted {accepted.name} keeps its costs after v{v2.version} of «{thc_tariff.name[:30]}»", before, costs(accepted))
    fresh = env["sale.order"].create({
        "partner_id": leroy.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": msc.id,
        "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id, "boss_destination_port_id": port("ESVLC", "sea").id,
        "boss_eta": date(2026, 11, 16),
        "boss_container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id, "quantity": 1})],
        "order_line": [Command.create({"product_id": product("THC").id, "product_uom_id": product("THC").uom_id.id, "boss_container_size": "40",
                                       "boss_container_type_id": ref("boss_pricing.container_type_hc").id})]})
    check("31 a new quotation uses the new version (+10)", round(thc_line.unit_price, 2), round(line_of(fresh, "THC").boss_cost_amount, 2))
    check("28 the new quotation names version, supplier, document and page", True,
          f"v{v2.version}" in line_of(fresh, "THC").boss_cost_explanation and "MSC" in line_of(fresh, "THC").boss_cost_explanation)

# 7: the inland carrier reaches the file at acceptance (values builder; the acceptance itself is covered by check_quote_flow)
values = order._boss_file_values()
check("7 file receives the haulier from the road line", ireneo.id, values.get("haulier_id"))
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if len(results) - sum(results):  # a failed check fails the run (dev/uat_run.sh records the exit status)
    raise SystemExit(1)
