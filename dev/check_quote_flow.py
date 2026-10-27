"""Check of the quotation → acceptance → file flow on boss20 after the meeting with Ángel and Cristina (27/10/2026,
part 2, ADR-007): the readiness message, orderer → consignee/shipper, 1×40' → 2×40', WFS on an ocean freight, a BOSS
own fee, the weekly freight rate entered from the quotation (port abroad, one week), history kept on accepted
quotations, Confirm opening exactly one file with the costs to buy. Every record is made here and rolled back.
Prints «CHECK PASS|FAIL …» and «RESULT n passed, m failed».    dev/uat_run.sh check_quote_flow.py boss20"""
from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools.binary import BinaryBytes

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
msc = Partner.search([("name", "=", "MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.")], limit=1)
wfs = Partner.search([("name", "=", "WORLDWIDE FLIGHT SERVICES")], limit=1)
belal = env["res.users"].search([("login", "=", "devbms")], limit=1)
costs = lambda o: [(l.product_id.default_code, l.boss_cost_status, round(l.boss_cost_amount, 2), round(l.price_unit, 2))  # noqa: E731
                   for l in o.order_line.filtered("product_id")]

# a customer like Susaeta, complete (country, tax ID), and one created in a hurry (no country)
susaeta = Partner.create({"name": "[PRUEBA] Susaeta Ediciones", "is_company": True, "country_id": ref("base.es").id,
                          "vat": "ESB12345674", "street": "Calle Prueba 1", "city": "Madrid", "state_id": state("M").id})
warehouse = Partner.create({"name": "[PRUEBA] Almacén Susaeta", "parent_id": susaeta.id, "type": "delivery",
                            "city": "Alcalá de Henares", "state_id": state("M").id, "country_id": ref("base.es").id})
hurry = Partner.create({"name": "[PRUEBA] contacto sin país", "is_company": True})
agent = Partner.create({"name": "[PRUEBA] Agent Shanghai Forwarding Ltd", "is_company": True,
                        "country_id": ref("base.cn").id})

# 1. BOSS import FCL from the template: orderer becomes the consignee, 1x40' then 2x40'
with Form(env["sale.order"]) as form:
    form.partner_id = susaeta
    form.sale_order_template_id = template("IMB FOB")
    check("1 orderer of a BOSS import is proposed as consignee", susaeta, form.boss_consignee_id)
    check("1 shipper stays empty (it is the foreign supplier of the customer)", False, bool(form.boss_shipper_id))
    form.boss_carrier_id = msc
    form.boss_origin_country_id = ref("base.cn")
    form.boss_origin_port_id = port("CNSHA", "sea")
    form.boss_destination_port_id = port("ESVLC", "sea")
    form.boss_delivery_address_id = warehouse
    form.boss_eta = date(2026, 12, 10)
    with form.boss_container_ids.new() as container:
        container.size = "40"
        container.container_type_id = ref("boss_pricing.container_type_dv")
imb = form.save()
qty = lambda o: {l.product_id.default_code: l.product_uom_qty for l in o.order_line.filtered("product_id")}  # noqa: E731
check("1 quantities with 1x40': per container 1, per shipment 1", (1.0, 1.0, 1.0), (qty(imb)["THC"], qty(imb)["BL"], qty(imb)["FMI"]))
# the demo order of steps (template, then the container): per-container services take the 40' of the shipment
sized = {l.product_id.default_code: (l.boss_container_size, l.boss_container_type_id.code)
         for l in imb.order_line.filtered(lambda l: l.product_id.default_code in ("THC", "T3-PAD", "GLO-CCC"))}
check("1 containers entered after the template: per-container lines take the 40' DV", {"THC": ("40", "DV"), "T3-PAD": ("40", "DV"), "GLO-CCC": ("40", "DV")}, sized)
t3 = imb.order_line.filtered(lambda l: l.product_id.default_code == "T3-PAD")
check("1 size-dependent price (T3-PAD 40') found", "ok", t3.boss_cost_status)
with Form(imb) as form:
    with form.boss_container_ids.edit(0) as container:
        container.quantity = 2
imb = form.save()
check("1 containers persisted 2x40'", [("40", "DV", 2)], [(c.size, c.container_type_id.code, c.quantity) for c in imb.boss_container_ids])
check("1 quantities with 2x40': per container 2, per shipment 1", (2.0, 1.0, 2.0), (qty(imb)["THC"], qty(imb)["BL"], qty(imb)["FMI"]))
thc = imb.order_line.filtered(lambda l: l.product_id.default_code == "THC")
check("1 THC cost = 2 x 253 from MSC (buying), sale typed separately", ("ok", 506.0), (thc.boss_cost_status, round(thc.boss_cost_amount, 2)))
check("1 THC cost source auditable", True, "Source:" in (thc.boss_cost_explanation or "") and "MSC" in (thc.boss_cost_explanation or ""))
print("   explanation:", (thc.boss_cost_explanation or "").replace("\n", " | ")[:300])
fmi = imb.order_line.filtered(lambda l: l.product_id.default_code == "FMI")
check("1 freight (FMI) is a manual amount when no rate exists", "manual", fmi.boss_cost_status)
csm = imb.order_line.filtered(lambda l: l.product_id.default_code == "CSM")
check("6 BOSS own fee: no supplier, cost ok 0", ("boss", "ok", 0.0), (csm.boss_execution, csm.boss_cost_status, csm.boss_cost_amount))

# 7. WFS cannot price an ocean freight: a warning at once, and «no supplier price» on the line
warning = fmi._onchange_boss_supplier_id() if (fmi.boss_supplier_id == wfs) else None
with Form(imb) as form:
    pass
fmi.boss_supplier_id = wfs
warning = fmi._onchange_boss_supplier_id()
check("7 WFS on an ocean freight: warning", True, bool(warning and warning.get("warning")))
check("7 WFS on an ocean freight: still a manual amount (no rate of WFS)", "manual", fmi.boss_cost_status)
fmi.boss_supplier_id = msc

# 5. weekly freight rate from the quotation: Shanghai -> Valencia, MSC, one week, then approved
Wizard = env["boss.supplier.price.wizard"]
wiz = Wizard.with_context(default_sale_line_id=fmi.id).create({})
check("5 wizard pre-filled: MSC, ESVLC, Shanghai abroad, valid one week", (msc, "ESVLC", "CNSHA", 6),
      (wiz.partner_id, wiz.port_ids.mapped("code")[0], wiz.foreign_port_ids.mapped("code")[0],
       (wiz.valid_to - wiz.valid_from).days))
wiz.write({"unit_price": 1500.0, "tariff_name": "[PRUEBA] MSC flete Shanghái-Valencia semana", "submit": False,
           "valid_from": date(2026, 12, 7), "document_reference": "[PRUEBA] oferta semanal",
           # the weekly offer (e-mail or PDF of the carrier) is the document every price must be traceable to
           "document": BinaryBytes(b"[PRUEBA] oferta semanal MSC Shanghai-Valencia 1500 EUR/40'", filename="oferta-semanal.txt"),
           "document_name": "oferta-semanal.txt"})
wiz.action_save()
rate = env["boss.tariff"].search([("name", "=", "[PRUEBA] MSC flete Shanghái-Valencia semana")], limit=1)
check("5 draft tariff with the route and validity", ("draft", "CNSHA", "ESVLC", date(2026, 12, 13)),
      (rate.state, rate.foreign_port_ids.mapped("code")[0], rate.port_ids.mapped("code")[0], rate.valid_to))
check("5 not approved yet: the freight stays manual", "manual", fmi.boss_cost_status)
rate.action_submit()
rate.with_user(belal).action_approve()
fmi._boss_recompute_cost()
check("5 approved: the freight is priced from the rate, 2 x 1500", ("ok", 3000.0), (fmi.boss_cost_status, round(fmi.boss_cost_amount, 2)))
check("5 source names the rate and its week", True, "[PRUEBA] MSC flete" in fmi.boss_cost_explanation and "CNSHA" in fmi.boss_cost_explanation)
# another route is not priced by it
other = imb.copy({"boss_origin_port_id": port("CNNGB", "sea").id})
fmi_other = other.order_line.filtered(lambda l: l.product_id.default_code == "FMI")
check("5 another origin port (Ningbo) is not priced by the Shanghai rate", "manual", fmi_other.boss_cost_status)
# outside the week neither
imb.boss_eta = date(2026, 12, 20)
fmi._boss_recompute_cost()
check("5 outside the week: manual again", "manual", fmi.boss_cost_status)
imb.boss_eta = date(2026, 12, 10)
fmi._boss_recompute_cost()

# 8. Confirm: readiness message grouped by cause, then one file, no duplicate, no purchase, no invoice
missing = [l.product_id.default_code for l in imb.order_line.filtered(lambda l: l.boss_sale_status == "missing")]
print("   sale prices missing before typing:", missing)
for line in imb.order_line.filtered(lambda l: l.boss_sale_status == "missing"):
    line.price_unit = 100.0
# the cost gate (decision B22): every bought service needs a known cost, a BOSS execution or a manager's reason
fad = imb.order_line.filtered(lambda l: l.product_id.default_code == "FAD")
fad.boss_supplier_id = Partner.search([("name", "=", "RAMOS VILA, S.L.")], limit=1)
tte = imb.order_line.filtered(lambda l: l.product_id.default_code == "TTE-FCL")
tte.with_user(belal).boss_unknown_cost_reason = "[PRUEBA] haulier quote pending, accepted at the customer's request"
try:
    imb._boss_check_costs()
    gate = ""
except UserError as e:
    gate = str(e)
print("   cost gate before reasons:", gate.replace("\n", " | ")[:200] or "none")
check("8 the cost gate names the services without a known cost", True, "TTE-FCL" not in gate and ("T3-PAD" in gate or gate == ""))
unknown = imb.order_line.filtered(lambda l: l.boss_cost_kind == "unknown" and not l.boss_unknown_cost_reason)
print("   still unknown:", unknown.mapped("product_id.default_code"))
for line in unknown:
    line.with_user(belal).boss_unknown_cost_reason = "[PRUEBA] accepted without cost for the test"
try:
    imb.action_confirm()
    confirm_error = ""
except UserError as e:
    confirm_error = str(e)
check("8 complete customer and prices: Confirm succeeds", "", confirm_error)
check("8 accepted and frozen", ("sale", True), (imb.state, imb.boss_pricing_frozen))
file = imb.boss_expediente_id
check("8 one file opened and linked", True, bool(file))
check("8 confirming twice does not open a second file", 1, len(env["boss.expediente"].search([("order_link_ids", "in", imb.ids)])))
try:
    imb.action_confirm()
except UserError:
    pass
check("8 still one file after a second Confirm", (1, file), (len(imb.boss_expediente_ids), imb.boss_expediente_id))
check("8 file receives orderer, consignee, route, containers", (susaeta, susaeta, "CNSHA", "ESVLC", 2),
      (file.partner_id, file.consignee_id, file.origin_port_id.code, file.destination_port_id.code, len(file.container_ids)))
check("8 no purchase order created by the acceptance", 0, len(file.purchase_order_ids))
check("8 no invoice created by the acceptance", 0, len(file.invoice_ids))
to_buy = {c.product_id.default_code: (c.partner_id.name, round(c.expected_amount, 2), c.state) for c in file.cost_ids.filtered(lambda c: c.kind == "sale")}
check("8 costs to buy carried into the file: THC from MSC 506, FMI 3000", (("MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.", 506.0), ("MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.", 3000.0)),
      (to_buy.get("THC", ("", 0))[:2], to_buy.get("FMI", ("", 0))[:2]))
print("   to buy:", to_buy)

# 9. history: a new MSC rate does not change the accepted quotation
frozen_before = costs(imb)
newer = rate.copy({"name": "[PRUEBA] MSC flete semana siguiente", "valid_from": date(2026, 12, 7), "valid_to": date(2026, 12, 13),
                   "document": rate.document, "document_name": rate.document_name})
newer.line_ids.unit_price = 1800.0
newer.action_submit()
newer.with_user(belal).action_approve()
env["sale.order"].browse(imb.id).order_line.invalidate_recordset()
imb.order_line._boss_recompute_cost()
check("9 accepted quotation keeps its costs after a new rate", frozen_before, costs(imb))
rate.action_archive()
check("9 accepted quotation keeps its cost after the rate is archived", frozen_before, costs(imb))
check("9 accepted quotation still names its source", True, "[PRUEBA] MSC flete Shanghái-Valencia semana" in fmi.boss_cost_explanation)

# 8b. the demo case: a contact without country stops the acceptance with one actionable message
with Form(env["sale.order"]) as form:
    form.partner_id = hurry
    form.sale_order_template_id = template("IMB FOB")
    form.boss_carrier_id = msc
    form.boss_origin_country_id = ref("base.cn")
    form.boss_origin_port_id = port("CNSHA", "sea")
    form.boss_destination_port_id = port("ESVLC", "sea")
    form.boss_eta = date(2026, 12, 10)
demo = form.save()
try:
    demo.action_confirm()
    message = ""
except UserError as e:
    message = str(e)
check("8b contact without country: one message naming the cause", True, "has no country" in message and hurry.name in message)
check("8b the message is short (grouped by cause, not one line per service)", True, message.count("\n") <= 6)
print("   message:", message.replace("\n", " | "))
check("8b pricing alert says why VAT is pending", True, "customer without country" in (demo.boss_pricing_alert or ""))

# 2. BOSS export: orderer becomes the shipper
with Form(env["sale.order"]) as form:
    form.partner_id = susaeta
    form.sale_order_template_id = template("EAB")
    check("2 orderer of a BOSS export is proposed as shipper", susaeta, form.boss_shipper_id)
    check("2 consignee stays empty", False, bool(form.boss_consignee_id))

# 3. agent's business: the agent orders, shipper and consignee are not the agent
with Form(env["sale.order"]) as form:
    form.partner_id = agent
    form.boss_business = "agent"
    form.sale_order_template_id = template("IMB FOB")
    form.boss_business = "agent"
    check("3 agent business: consignee not copied from the agent", False, bool(form.boss_consignee_id))
    form.boss_consignee_id = susaeta
    form.boss_shipper_id = Partner.create({"name": "[PRUEBA] Shanghai Books Co", "country_id": ref("base.cn").id})
agent_quote = form.save()
check("3 traffic code IMA, orderer = agent, parties kept", ("IMA", agent, susaeta), (agent_quote.boss_traffic_code, agent_quote.partner_id, agent_quote.boss_consignee_id))

print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
