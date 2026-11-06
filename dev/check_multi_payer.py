"""Agent business with several payers, USD and the profit share (go-live tracker P4-09) on boss20, inside a transaction
rolled back. An agent abroad orders an import FCL file (its business): it is quoted and invoiced in USD on the USD
price list, with BOSS's profit share as income (705005, exempt by the counterparty: F0-A27). The Spanish consignee gets
its own quotation on the same file through «Quote to another payer», accepted and invoiced to it in EUR with Spanish
VAT (F0-C56: one sale order per payer). The origin agent's profit share is a cost of the file bought in USD (607401,
never sold: P12). A partner that is not a party of the file is refused; a draft invoice cannot be moved to another
partner by hand; a cross-trade service resolves its VAT; the file closes operationally and financially with both payers
invoiced (acceptance criterion of P4-09).
    dev/uat_run.sh check_multi_payer.py boss20"""
from datetime import date, datetime

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def outcome(fn):
    try:
        with env.cr.savepoint():
            fn()
    except (UserError, ValidationError, AccessError) as e:
        print(f"      refused: {' '.join(str(e).split())[:200]}")
        return "refused"
    return "allowed"


ref = env.ref
Partner = env["res.partner"]
company = env.company
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
line_of = lambda o, code: o.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731
accounts = lambda p: p.product_tmpl_id.with_company(company)._get_product_accounts()  # noqa: E731
state_m = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "M")], limit=1)
usd, eur = ref("base.USD"), ref("base.EUR")
usd_list = env["product.pricelist"].search([("currency_id", "=", usd.id), ("company_id", "in", (company.id, False))],
                                            limit=1)
check("0 a USD price list exists (setup_phase4_agents)", True, bool(usd_list))
pft_cost, pft_income = product("PFT-FCL"), product("PFT-BOSS")
check("0 the origin agent's profit share is a cost only (607401, never sold: P12); BOSS's profit share to the agent is "
      "sold as income (705005, F0-C58 / P37-a)", (False, "607401", True, "705005"),
      (pft_cost.sale_ok, accounts(pft_cost)["expense"].code, pft_income.sale_ok, accounts(pft_income)["income"].code))
agent = Partner.create({"name": "[PRUEBA] Agente Shanghai (pagador USD)", "is_company": True,
                        "country_id": ref("base.cn").id, "city": "Shanghai", "property_product_pricelist": usd_list.id})
importer = Partner.create({"name": "[PRUEBA] Importador Madrid (segundo pagador)", "is_company": True,
                           "vat": "ESB12345674", "country_id": ref("base.es").id, "city": "Madrid",
                           "state_id": state_m.id})
broker = Partner.create({"name": "[PRUEBA] Agente de aduanas pagadores", "is_company": True,
                         "country_id": ref("base.es").id, "city": "Valencia"})
carrier = Partner.create({"name": "[PRUEBA] Naviera pagadores", "is_company": True, "country_id": ref("base.es").id,
                          "city": "Valencia"})
stranger = Partner.create({"name": "[PRUEBA] Tercero ajeno al expediente", "is_company": True,
                           "country_id": ref("base.es").id})
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                                         ("company_id", "=", company.id)], limit=1)
fob = env["account.incoterms"].search([("code", "=", "FOB")], limit=1)
dv = ref("boss_pricing.container_type_dv")

# ---- 1. the agent's quotation in USD opens the file (agent business) ---------------------------------------------------
order = env["sale.order"].create({
    "partner_id": agent.id, "boss_business": "agent", "boss_direction": "import", "boss_transport_mode": "sea",
    "boss_load_type": "fcl", "incoterm": fob.id, "boss_origin_country_id": ref("base.cn").id,
    "boss_origin_port_id": port("CNSHA", "sea").id, "boss_destination_port_id": port("ESVLC", "sea").id,
    "boss_scope_main": True, "boss_scope_destination_customs": True, "boss_etd": date(2026, 11, 20),
    "boss_eta": date(2026, 12, 20), "boss_container_ids": [Command.create({"size": "40", "container_type_id": dv.id})],
    "order_line": [
        Command.create({"product_id": pft_income.id, "product_uom_id": pft_income.uom_id.id}),
        Command.create({"product_id": product("CSM").id, "product_uom_id": product("CSM").uom_id.id}),
    ]})
line_of(order, "PFT-BOSS").price_unit = 500.0  # BOSS's own fees: the price is typed on the line (as CSM in the e2e)
line_of(order, "CSM").price_unit = 60.0
check("1 the agent's quotation is in USD on the USD price list taken from the agent's contact", ("USD", usd_list.id),
      (order.currency_id.name, order.pricelist_id.id))
for l in order.order_line:
    print(f"      {l.product_id.default_code:9} sale {l.price_unit:8.2f} {order.currency_id.name} vat {l.boss_vat_status} "
          f"{l.boss_vat_trace or ''} taxes {l.tax_ids.mapped('name')}")
pft_line = line_of(order, "PFT-BOSS")
check("1 BOSS's profit share to an agent outside the EU is exempt (F0-A27: NR, then EX by the counterparty), nothing pending",
      (True, True), (pft_line.boss_vat_status != "pending", bool(pft_line.tax_ids) and all(t.amount == 0 for t in pft_line.tax_ids)))
order.action_confirm()
file = order.boss_expediente_id
check("1 the accepted quotation opened an agent-business file (traffic IMA) whose customer is the agent",
      ("agent", agent.id, "IMA"), (file.business, file.partner_id.id, file.traffic_code))

# ---- 2. the consignee is quoted on the same file through «Quote to another payer» ----------------------------------------
file.write({"consignee_id": importer.id})
check("2 the payers of the file are its customer (the agent) and its parties (the consignee)", {agent.id, importer.id},
      set(file._boss_payer_partners().ids))
bindings = env["ir.actions.actions"].get_bindings("boss.expediente")["action"]
check("2 «Quote to another payer» is an action of the file form", True,
      any(b["name"] == "Quote to another payer" for b in bindings if b.get("binding_view_types") == "form"))
check("2 the file opens the wizard", "boss.payer.quotation", file.action_new_quotation_payer()["res_model"])
wizard = env["boss.payer.quotation"].create({"expediente_id": file.id, "payer_id": importer.id})
check("2 the wizard offers the parties of the file only and says who pays the freight (Incoterm %s: %s)"
      % (fob.code, fob.boss_freight_payment), ({agent.id, importer.id}, True),
      (set(wizard.allowed_payer_ids.ids), bool(wizard.hint)))
print(f"      hint: {wizard.hint}")
ctx = wizard.action_confirm()["context"]
check("2 the new quotation opens for the consignee, linked to the file, with the file's shipment data",
      (importer.id, file.id, True, "agent"),
      (ctx.get("default_partner_id"), ctx.get("default_boss_expediente_id"),
       ctx.get("default_boss_origin_port_id") == port("CNSHA", "sea").id, ctx.get("default_boss_business")))
quote = env["sale.order"].with_context(ctx).create({"partner_id": importer.id, "order_line": [
    Command.create({"product_id": product("FAD").id, "product_uom_id": product("FAD").uom_id.id}),
    Command.create({"product_id": product("DEM").id, "product_uom_id": product("DEM").uom_id.id}),
]})
# bought services whose supplier has no tariff document yet (F0-C06): asked to the supplier case by case, the cost is
# typed on the file's need when known; the sale price is typed on the line
line_of(quote, "FAD").write({"boss_supplier_id": broker.id, "boss_cost_on_request": True})
line_of(quote, "DEM").write({"boss_supplier_id": carrier.id, "boss_cost_on_request": True})
quote.action_boss_update_costs()
for l in quote.order_line:
    print(f"      {l.product_id.default_code:9} cost {l.boss_cost_status} {l.boss_cost_amount:.2f}")
check("2 services asked to the supplier case by case can be accepted (cost typed in the file later)", ["on_request"] * 2,
      quote.order_line.mapped("boss_cost_status"))
line_of(quote, "FAD").price_unit = 120.0
line_of(quote, "DEM").price_unit = 150.0
check("2 the consignee's quotation is linked to the file, in EUR", (file.id, "EUR"), (quote.boss_expediente_id.id, quote.currency_id.name))
for l in quote.order_line:
    print(f"      {l.product_id.default_code:9} sale {l.price_unit:8.2f} {quote.currency_id.name} vat {l.boss_vat_status} "
          f"{l.boss_vat_trace or ''} taxes {l.tax_ids.mapped('name')}")
quote.action_confirm()
env.invalidate_all()
check("2 the file has the accepted orders of both payers, each in its currency", {(agent.id, "USD"), (importer.id, "EUR")},
      {(o.partner_id.id, o.currency_id.name) for o in file.sale_order_ids.filtered(lambda o: o.state == "sale")})
check("2 the file sums the sales of both payers in company currency (more than the EUR part alone)", True,
      file.sudo().amount_sale > 270.0)
print(f"      agreed sale of the file {file.sudo().amount_sale:.2f} {file.currency_id.name}")
fad = file.cost_ids.filtered(lambda n: n.product_id == product("FAD"))
check("2 the consignee's customs clearance is a purchase need of the file (customs broker, EUR)",
      ("FAD", broker.id, "EUR"), (fad.product_id.default_code, fad.partner_id.id, fad.currency_id.name))

# ---- 3. guards -------------------------------------------------------------------------------------------------------------
check("3 a quotation of a partner that is not a party of the file is refused (put it on the file first)", "refused",
      outcome(lambda: env["sale.order"].create({"partner_id": stranger.id, "boss_expediente_id": file.id})))

# ---- 4. one invoice per payer ----------------------------------------------------------------------------------------------
inv_usd, inv_eur = order._create_invoices(), quote._create_invoices()
check("4 each payer gets its own invoice in its currency: the agent in USD, the consignee in EUR",
      {(agent.id, "USD"), (importer.id, "EUR")},
      {(m.partner_id.commercial_partner_id.id, m.currency_id.name) for m in inv_usd | inv_eur})
pft_inv = inv_usd.invoice_line_ids.filtered(lambda l: l.product_id == pft_income)
check("4 BOSS's profit share is income on 705005, exempt for the third-country agent (0 %)", ("705005", True),
      (pft_inv.account_id.code, bool(pft_inv.tax_ids) and all(t.amount == 0 for t in pft_inv.tax_ids)))
check("4 the consignee's invoice carries Spanish VAT (21 %) on its services", True,
      bool(inv_eur.invoice_line_ids.tax_ids) and all(t.amount == 21 for t in inv_eur.invoice_line_ids.tax_ids))
check("4 a draft invoice of a file quotation cannot be moved to a stranger by hand", "refused",
      outcome(lambda: inv_eur.with_user(ref("base.user_admin")).write({"partner_id": stranger.id})))
check("4 ... nor to the other payer of the file: each payer has its own quotation and invoice", "refused",
      outcome(lambda: inv_eur.with_user(ref("base.user_admin")).write({"partner_id": agent.id})))
(inv_usd | inv_eur).write({"invoice_date": date(2026, 12, 11)})
(inv_usd | inv_eur).action_post()
check("4 both invoices posted", ["posted", "posted"], (inv_usd | inv_eur).mapped("state"))

# ---- 5. the origin agent's profit share: a cost of the file in USD, ordered, performed and billed to the agent -------------
env["boss.expediente.cost"].create({
    "expediente_id": file.id, "kind": "extra", "product_id": pft_cost.id, "partner_id": agent.id, "currency_id": usd.id,
    "uom_id": pft_cost.uom_id.id, "quantity": 1.0, "expected_unit_cost": 300.0, "extra_class": "covered",
    "reason": "[PRUEBA] profit share pactado con el agente de origen: coste del expediente, nunca se vende (P12)"})
for code, cost in (("FAD", 80.0), ("DEM", 100.0)):  # the costs asked case by case, now known, typed on the needs
    file.cost_ids.filtered(lambda n, c=code: n.product_id.default_code == c).write({"expected_unit_cost": cost})
file.action_create_rfqs()
pos = file.purchase_order_ids
check("5 RFQs of the file: the customs broker and the carrier in EUR, the origin agent in USD",
      {(broker.id, "EUR"), (carrier.id, "EUR"), (agent.id, "USD")}, {(p.partner_id.id, p.currency_id.name) for p in pos})
for po in pos:
    po.partner_ref = f"[PRUEBA] conf. {po.currency_id.name}"
    po.button_confirm()
file.cost_ids.filtered("purchase_line_ids").action_mark_performed()
bills = env["account.move"]
for po in pos:
    po.action_create_invoice()
    bill = po.invoice_ids.filtered(lambda m: m.state == "draft")[:1]
    bill.write({"invoice_date": date(2026, 12, 12), "ref": f"[PRUEBA] factura agente {po.currency_id.name}"})
    bill.invoice_line_ids.tax_ids = purchase_0
    bill.action_post()
    bills |= bill
pft_bill = bills.invoice_line_ids.filtered(lambda l: l.product_id == pft_cost)
check("5 the origin agent's profit share is billed in USD at the agreed amount on 607401", ("USD", "607401", 300.0),
      (pft_bill.move_id.currency_id.name, pft_bill.account_id.code, round(pft_bill.price_subtotal, 2)))
check("5 every need of the file is performed and billed", [], [
    (n.product_id.default_code, n.state) for n in file.cost_ids if n.state not in ("performed", "billed", "closed")
    and n.qty_billed < n.quantity])

# ---- 6. operations and the two closes --------------------------------------------------------------------------------------
file.write({"booking_ref": "[PRUEBA] BK-PAG-1", "mbl_ref": "[PRUEBA] MBL-PAG-1", "hbl_ref": "[PRUEBA] HBL-PAG-1",
            "vessel": "[PRUEBA] BUQUE", "voyage": "001E", "atd": datetime(2026, 11, 20, 18, 0)})
file.container_ids.write({"number": "PRUU1234565", "seal": "SEAL-1"})
file.action_in_transit()
file.write({"ata": datetime(2026, 12, 20, 6, 0), "discharge_date": datetime(2026, 12, 20, 14, 0),
            "customs_ref": "[PRUEBA] 26ES00460010000002", "customs_guarantee": "boss",
            "customs_admission_date": datetime(2026, 12, 21, 9, 0), "customs_channel": "green",
            "customs_release_date": datetime(2026, 12, 21, 12, 0), "hbl_release": "released",
            "delivery_date": datetime(2026, 12, 22, 11, 0)})
file.container_ids.write({"pickup_date": date(2026, 12, 22), "return_date": date(2026, 12, 24)})
file.action_delivered()
check("6 the file is delivered", "delivered", file.state)
file.action_close_operations()  # first: the parties to rate
file.rating_ids.write({"rating": "8"})
file.action_close_operations()
check("6 operations closed: both payers invoiced, parties rated", "closed", file.state)
env.invalidate_all()
check("6 nothing left to review (the USD cost billed at the order amount has no variance to review, P2-12)", False,
      bool(file.completeness))
file.action_close_financial()
check("6 the file closes financially with two payers and a USD cost", True, file.financial_closed)
row = env["boss.margin.report"].search([("expediente_id", "=", file.id)])
check("6 «Margin by file» keeps the agent file with a positive final margin (sales of both payers in EUR above its costs)",
      (1, True), (len(row), bool(row) and row.amount_margin_final > 0))
print(f"      final margin {row.amount_margin_final:.2f} {file.currency_id.name} on sales {file.sudo().amount_sale:.2f}")

# ---- 7. cross-trade: a service between two third countries resolves its VAT (no Spanish leg) -----------------------------
cross = env["sale.order"].create({
    "partner_id": agent.id, "boss_business": "agent", "boss_direction": "import", "boss_transport_mode": "sea",
    "boss_load_type": "fcl", "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id,
    "boss_destination_country_id": ref("base.us").id, "order_line": [
        Command.create({"product_id": product("CSM").id, "product_uom_id": product("CSM").uom_id.id})]})
csm = line_of(cross, "CSM")
csm.price_unit = 60.0
print(f"      cross-trade CSM vat {csm.boss_vat_status} {csm.boss_vat_trace or ''} taxes {csm.tax_ids.mapped('name')}")
check("7 a cross-trade service (third country to third country) is exempt (NR, then EX by the route), VAT decided, in USD",
      (True, True, "USD"), (csm.boss_vat_status != "pending", bool(csm.tax_ids) and all(t.amount == 0 for t in csm.tax_ids),
                            cross.currency_id.name))
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if not all(results):
    raise SystemExit(1)
