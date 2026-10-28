"""End-to-end check of a complete file on boss20 (plan «expediente completo», phase F1).

Scenario S1 — sea import FCL with customs (IMB FOB), from the quotation to the financial close, with [PRUEBA] data made
here: quotation from approved supplier prices → acceptance → file → RFQs per supplier and currency (one in USD) →
booking, references, containers, actual dates → «In transit» → arrival, DUA, container dates, delivery → «Delivered» →
performed services → vendor bills (one above the order price, a supplier credit note, a USD bill, the customs broker's
bill of duties paid on behalf without purchase order) → payment held until the customer is invoiced (P30) → partial and
final customer invoices → collections and payments matched with bank statement lines → operational close →
financial close (group checked on the server, variance reviewed first).
Every step not built yet is printed as «GAP <step> → <phase of docs/plan-expediente-completo.md>», with what the system
does today; the other scenarios (S2-S7) are listed the same way until their phase is done. Gaps are not failures.

MODE «rollback» (default and only mode until decision F0 on the production database): everything is rolled back at the
end; only sequence numbers advance. Fictitious prices only ([PRUEBA] suppliers and customer).
Prints «CHECK PASS|FAIL …», «GAP …» and «RESULT n passed, m failed, g gaps».
    dev/uat_run.sh check_file_e2e.py boss20"""
from datetime import date, datetime

from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
MODE = "rollback"
results, gaps = [], []
ERRORS = (UserError, ValidationError, AccessError)


def check(name, expected, got):
    ok = expected == got
    if isinstance(expected, float) and isinstance(got, (int, float)):
        ok = abs(expected - got) < 0.01
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")
    return ok


class _Undo(Exception):
    pass


def outcome(fn):
    """Run fn and undo it: ('accepted', None) or ('refused', message)."""
    try:
        with env.cr.savepoint():
            fn()
            env.flush_all()
            raise _Undo
    except _Undo:
        env.invalidate_all()
        return "accepted", None
    except ERRORS as exc:
        env.invalidate_all()
        return "refused", " ".join(str(exc).split())[:180]


def refused(name, fn):
    got, message = outcome(fn)
    check(name, "refused", got)
    if message:
        print(f"      «{message}»")


def gap(step, phase, observed=""):
    gaps.append(step)
    print(f"GAP {step} → {phase}" + (f" (today: {observed})" if observed else ""))


ref = env.ref
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
state = lambda code: env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", code)], limit=1)  # noqa: E731
template = lambda code: env["sale.order.template"].search([("name", "=like", f"{code} · %")], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
line_of = lambda o, code: o.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731
Partner, Tariff, Move = env["res.partner"], env["boss.tariff"], env["account.move"]
company = env.company
belal = env["res.users"].search([("login", "=", "devbms")], limit=1)
dv = ref("boss_pricing.container_type_dv")
usd, eur = ref("base.USD"), ref("base.EUR")
bank = env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", company.id)], limit=1)
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                                         ("company_id", "=", company.id)], limit=1)
files_before = env["boss.expediente"].search_count([])

# ---- 0b. every form opens (smoke test): the form view loads and every field of the latest records reads ------------
# (28/10/2026: the file form failed for everybody — a computed field called an API Odoo 20 removed — and no check read it)
broken = []
for model in sorted(m for m in env.registry if m.startswith("boss.") and not env[m]._transient and not env[m]._abstract) \
        + ["sale.order", "sale.order.line", "purchase.order", "account.move", "res.partner", "product.template"]:
    try:
        with env.cr.savepoint():
            env[model].get_view(view_type="form")
            env[model].sudo().search([], limit=3, order="id desc").read()
    except Exception as exc:  # noqa: BLE001  any error here is a screen that does not open
        broken.append(f"{model}: {type(exc).__name__}: {' '.join(str(exc).split())[:160]}")
    env.invalidate_all()
check("0b every BOSS form opens (form view and every field of the latest records)", [], broken)
guide = env["product.template"].search([("boss_pricing_mode", "!=", False)], limit=1).action_boss_ws_guide()
check("0b the guide button of the pricing workspace opens its link", True, guide["url"].startswith("http"))
print(f"MODE {MODE} | files before {files_before} | bank journal {bank.code} | setting P30 {company.boss_bill_before_invoice}")

# ---- 0. parties, users and approved supplier prices ([PRUEBA], fictitious figures) --------------------------------
customer = Partner.create({"name": "[PRUEBA] E2E Importador, S.L.", "is_company": True, "country_id": ref("base.es").id,
                           "vat": "ESB12345674", "street": "Calle Prueba 2", "city": "Madrid", "state_id": state("M").id})
warehouse = Partner.create({"name": "[PRUEBA] E2E Almacén Getafe", "parent_id": customer.id, "type": "delivery",
                            "street": "Polígono Prueba 3", "city": "Getafe", "state_id": state("M").id,
                            "country_id": ref("base.es").id})
supplier = lambda name: Partner.create({"name": name, "is_company": True, "supplier_rank": 1,  # noqa: E731
                                        "country_id": ref("base.es").id})
carrier = supplier("[PRUEBA] E2E Naviera")
broker = supplier("[PRUEBA] E2E Agente de aduanas")
haulier = supplier("[PRUEBA] E2E Transportista")
user = lambda login, groups: env["res.users"].with_context(no_reset_password=True).create({  # noqa: E731
    "name": f"[PRUEBA] E2E {login}", "login": f"prueba_e2e_{login}",
    "group_ids": [Command.set([ref(g).id for g in groups])]})
sales_user = user("ventas", ["sales_team.group_sale_salesman"])
invoicing_user = user("facturacion", ["sales_team.group_sale_salesman", "account.group_account_invoice"])


def approved_tariff(name, partner, currency, prices, **scope):
    values = {"name": f"[PRUEBA] E2E {name}", "partner_id": partner.id, "currency_id": currency.id,
              "valid_from": date(2026, 1, 1), "direction": "import", "transport_mode": "sea", "load_type": "fcl",
              "customer_id": customer.id, "port_ids": [Command.set(port("ESVLC", "sea").ids)], "scope_confirmed": True,
              "document": BinaryBytes(f"[PRUEBA] oferta ficticia {name}".encode(), filename="oferta.txt"),
              "document_name": "oferta.txt",
              "line_ids": [Command.create({
                  "product_id": product(code).id, "uom_id": product(code).uom_id.id, "unit_price": price,
                  "container_size": "40" if product(code).uom_id.boss_quantity_source == "container" else False})
                  for code, price in prices.items()]}
    values.update(scope)
    tariff = Tariff.create(values)
    if tariff.state != "approved":
        tariff.action_submit()
        tariff.with_user(belal).action_approve()
    return tariff


local = approved_tariff("gastos locales", carrier, eur, {"THC": 200.0, "BL": 50.0, "GLO-CCC": 30.0, "T3-PAD": 40.0},
                        carrier_id=carrier.id)
freight = approved_tariff("flete Shanghái-Valencia", carrier, usd, {"FMI": 1000.0}, carrier_id=carrier.id,
                          foreign_port_ids=[Command.set(port("CNSHA", "sea").ids)],
                          valid_from=date(2026, 11, 2), valid_to=date(2026, 11, 8))
customs = approved_tariff("despacho", broker, eur, {"FAD": 100.0})
trucking = approved_tariff("transporte contenedor", haulier, eur, {"TTE-FCL": 300.0})
check("0 four approved [PRUEBA] supplier prices (local EUR, freight USD, customs, trucking)", ["approved"] * 4,
      [local.state, freight.state, customs.state, trucking.state])

# ---- 1. quotation from the IMB template --------------------------------------------------------------------------
with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.sale_order_template_id = template("IMB FOB")
    form.boss_carrier_id = carrier
    form.boss_origin_country_id = ref("base.cn")
    form.boss_origin_port_id = port("CNSHA", "sea")
    form.boss_destination_port_id = port("ESVLC", "sea")
    form.boss_delivery_address_id = warehouse
    form.boss_etd = date(2026, 11, 5)
    form.boss_eta = date(2026, 12, 7)
    form.boss_duties_amount = 500.0
    form.client_order_ref = "PO-[PRUEBA]-E2E"
    with form.boss_container_ids.new() as container:
        container.size = "40"
        container.container_type_id = dv
order = form.save()
order.write({"order_line": [Command.create({"product_id": product("ARA").id, "product_uom_id": product("ARA").uom_id.id})]})
for code, partner in (("FMI", carrier), ("THC", carrier), ("BL", carrier), ("GLO-CCC", carrier), ("T3-PAD", carrier),
                      ("FAD", broker), ("ARA", broker), ("TTE-FCL", haulier)):
    line_of(order, code).boss_supplier_id = partner
line_of(order, "ARA").write({"boss_manual_cost": 500.0, "boss_manual_cost_note": "[PRUEBA] estimación de aranceles"})
line_of(order, "CSM").price_unit = 60.0
order.action_boss_update_costs()
ara = line_of(order, "ARA")
gap("S1 duties paid on behalf re-invoiced at the exact amount paid (no default margin)", "F9 / decision Ángel",
    f"default sale {ara.price_unit:.2f} for {ara.boss_manual_cost:.2f} paid (cost + default %)")
ara.price_unit = ara.boss_manual_cost  # typed at cost, as an operator does today
print("      ARA VAT trace:", " | ".join((line_of(order, "ARA").boss_vat_trace or "").splitlines())[:600])
for l in order.order_line.filtered("product_id"):
    print(f"      {l.product_id.default_code:8} {l.boss_cost_status:16} cost {l.boss_cost_amount:9.2f} "
          f"{l.boss_cost_currency_id.name or '':3} sale {l.price_unit:9.2f} vat {l.boss_vat_status}")
check("1 template services + duties on the quotation",
      sorted(["FMI", "THC", "BL", "GLO-CCC", "T3-PAD", "FAD", "CSM", "TTE-FCL", "ARA"]),
      sorted(order.order_line.filtered("product_id").mapped("product_id.default_code")))
check("1 every supplier service priced (tariff, or manual cost with its note)", [],
      [l.product_id.default_code for l in order.order_line.filtered("product_id")
       if l.boss_cost_status not in ("ok", "manual")])
check("1 freight from the USD rate of the departure week", ("ok", "USD"),
      (line_of(order, "FMI").boss_cost_status, line_of(order, "FMI").boss_cost_currency_id.name))
check("1 nothing blocks acceptance (VAT decided, every sale price set)", [],
      [l.product_id.default_code for l in order.order_line.filtered("product_id")
       if l.boss_vat_status == "pending" or l.boss_sale_status == "missing"])

# ---- 2. acceptance → file --------------------------------------------------------------------------------------------
order.action_confirm()
file = order.boss_expediente_id
check("2 accepted, one file with its analytic account", ("sale", 1, True),
      (order.state, len(order.boss_expediente_ids), bool(file.analytic_account_id)))
bought = order.order_line.filtered(lambda l: l.product_id and l.boss_execution == "supplier")
check("2 one purchase need per bought service", len(bought), len(file.cost_ids))
gap("S1 operator of the file and milestone plan of its traffic", "F5", "the salesman is the responsible, no activities")
gap("S1 documents folder of the file", "F6", "attachments in the chatter only")

# ---- 3. purchases per supplier and currency --------------------------------------------------------------------------
file.action_create_rfqs()
pos = file.purchase_order_ids
check("3 RFQs: carrier EUR + carrier USD + customs broker + haulier (duties need no order)",
      sorted([(carrier.name, "EUR"), (carrier.name, "USD"), (broker.name, "EUR"), (haulier.name, "EUR")]),
      sorted((p.partner_id.name, p.currency_id.name) for p in pos))
check("3 duties (ARA) wait for the broker's bill without order", "awaiting_bill",
      file.cost_ids.filtered(lambda n: n.product_id == product("ARA")).state)
for po in pos:
    po.partner_ref = f"[PRUEBA] conf. {po.partner_id.name[-12:]}"
    po.button_confirm()
check("3 every order confirmed with the supplier's reference", [("purchase", True)] * len(pos),
      [(p.state, bool(p.partner_ref)) for p in pos])

# ---- 4. booking and departure ----------------------------------------------------------------------------------------
got, _msg = outcome(file.action_in_transit)
gap("S1 «In transit» without departure date, booking or container number", "F5", got)
file.write({"booking_ref": "BK-PRUEBA-1", "mbl_ref": "MBL-PRUEBA-1", "hbl_ref": "HBL-PRUEBA-1", "vessel": "[PRUEBA] VESSEL",
            "voyage": "001E", "atd": datetime(2026, 11, 5, 18, 0)})
file.container_ids.write({"number": "PRUU1234565", "seal": "SEAL-1"})
arch = etree.fromstring(env["boss.expediente"].get_view(view_type="form")["arch"])
atd_field = arch.xpath("//page[@name='references']//field[@name='atd']")
pickup_field = arch.xpath("//page[@name='references']//field[@name='pickup_date']")  # not the containers' column
check("4 ATD and actual pickup shown on every file (import ATD, export pickup)", (True, True),
      (bool(atd_field) and not atd_field[0].get("invisible"), bool(pickup_field) and not pickup_field[0].get("invisible")))
file.action_in_transit()
check("4 file in transit", "in_transit", file.state)

# ---- 5. destination: arrival, customs, containers, delivery -----------------------------------------------------------
got, _msg = outcome(file.action_delivered)
gap("S1 «Delivered» without arrival, customs release or delivery date", "F7", got)
file.write({"ata": datetime(2026, 12, 7, 6, 0), "discharge_date": datetime(2026, 12, 7, 14, 0),
            "customs_ref": "[PRUEBA] 26ES00460010000001"})
gap("S1 customs status, channel and release (levante) of the DUA", "F7", "only the DUA number")
file.container_ids.write({"pickup_date": date(2026, 12, 10), "return_date": date(2026, 12, 12)})
file.delivery_date = datetime(2026, 12, 10, 11, 0)
gap("S1 transport order (OT) to the haulier from Odoo", "F7")
file.action_delivered()
check("5 file delivered", "delivered", file.state)

# ---- 6. performed services and vendor bills ---------------------------------------------------------------------------
ordered = file.cost_ids.filtered("purchase_line_ids")
ordered.action_mark_performed()
check("6 every ordered service performed", ["performed"] * len(ordered), ordered.mapped("state"))
po_eur = pos.filtered(lambda p: p.partner_id == carrier and p.currency_id == eur)
po_usd = pos.filtered(lambda p: p.partner_id == carrier and p.currency_id == usd)
po_broker = pos.filtered(lambda p: p.partner_id == broker)
po_haulier = pos.filtered(lambda p: p.partner_id == haulier)


def bill_of(po, ref_text, day, price_changes=None):
    po.action_create_invoice()
    bill = po.invoice_ids.filtered(lambda m: m.state == "draft")[:1]
    bill.write({"invoice_date": day, "ref": ref_text})
    bill.invoice_line_ids.tax_ids = purchase_0
    for code, price in (price_changes or {}).items():
        bill.invoice_line_ids.filtered(lambda l, c=code: l.product_id.default_code == c).price_unit = price
    return bill


bill_eur = bill_of(po_eur, "[PRUEBA] NAV-1", date(2026, 12, 11), {"THC": 220.0})  # 20 above the order
bill_eur.action_post()
check("6 the lines of a bill from the file's order carry the file", True,
      all(l.boss_expediente_id == file for l in bill_eur.invoice_line_ids))
thc_need = file.cost_ids.filtered(lambda n: n.product_id == product("THC"))
check("6 THC billed 220 for 200 ordered: variance to review", (True, 20.0),
      (thc_need.variance_to_review, round(thc_need.variance_company, 2)))
refund = bill_eur._reverse_moves([{"ref": "[PRUEBA] abono BL", "date": date(2026, 12, 12),
                                   "invoice_date": date(2026, 12, 12)}])
refund.invoice_line_ids.filtered(lambda l: l.product_id.default_code != "BL").unlink()
refund.invoice_line_ids.price_unit = 10.0
refund.action_post()
(bill_eur | refund).line_ids.filtered(lambda l: l.account_id.account_type == "liability_payable").reconcile()
bill_usd = bill_of(po_usd, "[PRUEBA] NAV-USD-1", date(2026, 12, 11))
bill_usd.action_post()
check("6 freight bill in USD posted, at the order price", ("USD", 1000.0),
      (bill_usd.currency_id.name, round(bill_usd.amount_untaxed, 2)))
gap("S1 USD variance split into price and exchange rate", "F8", "one variance figure")
for po, ref_text in ((po_broker, "[PRUEBA] ADU-1"), (po_haulier, "[PRUEBA] TTE-1")):
    bill_of(po, ref_text, date(2026, 12, 11)).action_post()
# the customs broker's bill of the duties paid on behalf: no purchase order, from the file («Cost without purchase order»)
ctx = file.action_new_bill()["context"]
duties_bill = Move.with_context(**ctx).create({
    "partner_id": broker.id, "invoice_date": date(2026, 12, 11), "ref": "[PRUEBA] ADU-SUPLIDOS",
    "invoice_line_ids": [Command.create({"product_id": product("ARA").id, "quantity": 1, "price_unit": 500.0,
                                         "tax_ids": [Command.set(purchase_0.ids)]})]})
duties_bill.action_post()
ara_need = file.cost_ids.filtered(lambda n: n.product_id == product("ARA"))
check("6 duties bill without order: carries the file, the duties need is billed", (file, "billed"),
      (duties_bill.invoice_line_ids.boss_expediente_id, ara_need.state))
file.invalidate_recordset()
all_bills = bill_eur | refund | bill_usd | po_broker.invoice_ids | po_haulier.invoice_ids | duties_bill
check("6 actual cost = posted bills - supplier credit note (USD at the bill rate), duties counted once",
      round(-sum(all_bills.mapped("amount_untaxed_signed")), 2), round(file.amount_cost_actual, 2))

# ---- 7. payment held until the customer is invoiced (P30) -----------------------------------------------------------


def pay(move, label, day=date(2026, 12, 20)):
    """Register the payment (the BOSS payment rule applies), then match it with a bank statement line."""
    amount = abs(move.amount_residual_signed)  # company currency: what the bank line shows
    wizard = env["account.payment.register"].with_context(active_model="account.move", active_ids=move.ids).create(
        {"journal_id": bank.id, "payment_date": day})
    payment = wizard._create_payments()
    sign = 1 if move.move_type in ("out_invoice", "in_refund") else -1
    st_line = env["account.bank.statement.line"].create({
        "journal_id": bank.id, "date": day, "payment_ref": f"[PRUEBA] E2E {label}", "partner_id": move.partner_id.id,
        "amount": sign * amount})
    if payment.move_id:
        to_match = payment.move_id.line_ids.filtered(lambda l: l.account_id == payment.outstanding_account_id)
    else:
        to_match = move.line_ids.filtered(lambda l: l.account_id.account_type in ("asset_receivable", "liability_payable"))
    st_line.set_line_bank_statement_line(to_match.ids)
    move.invalidate_recordset()
    return payment


refused("7 the carrier's bill cannot be paid before the customer is invoiced (P30, payment wizard)",
        lambda: pay(bill_eur, "pago anticipado"))


def pay_by_statement_only():
    st_line = env["account.bank.statement.line"].create({
        "journal_id": bank.id, "date": date(2026, 12, 13), "payment_ref": "[PRUEBA] E2E pago por extracto",
        "partner_id": carrier.id, "amount": -abs(bill_eur.amount_residual_signed)})
    st_line.set_line_bank_statement_line(bill_eur.line_ids.filtered(
        lambda l: l.account_id.account_type == "liability_payable").ids)


got, _msg = outcome(pay_by_statement_only)
gap("S1 P30 also on the bank reconciliation of the bill", "F8", got)

# ---- 8. customer invoices: partial, then the rest -------------------------------------------------------------------
Invoice = env["boss.invoice.services"]
thc_alloc = file.allocation_ids.filtered(lambda a: a.product_id == product("THC"))
inv1 = Move.browse(Invoice.create({"expediente_id": file.id, "allocation_ids": [Command.set(thc_alloc.ids)]})
                   .action_create()["res_id"])
inv1.invoice_date = date(2026, 12, 14)
inv1.action_post()
rest = file.allocation_ids.filtered(lambda a: a.to_invoice_quantity > 0)
inv2 = Move.browse(Invoice.create({"expediente_id": file.id, "allocation_ids": [Command.set(rest.ids)]})
                   .action_create()["res_id"])
inv2.invoice_date = date(2026, 12, 15)
inv2.action_post()
file.invalidate_recordset()
check("8 everything invoiced (partial THC, then the rest)", (round(file.amount_sale, 2), 0.0),
      (round(file.amount_invoiced, 2), round(file.amount_to_invoice, 2)))
check("8 the customer invoice lines carry the file", True,
      all(l.boss_expediente_id == file for l in (inv1 | inv2).invoice_line_ids))
gap("S1 duties invoiced apart from the services (separate invoice / section) and their VAT", "F9",
    "duties are one more line of the invoice")
gap("S1 legal mention of every 0 % tax, company IBAN and agreed series on the invoice", "F4",
    "no bank account on the company; legal notes on some 0 % taxes only")

# ---- 9. collections and payments matched with the bank ------------------------------------------------------------------
for move, label in ((inv1, "cobro THC"), (inv2, "cobro resto")):
    pay(move, label)
for move in (bill_eur | bill_usd | po_broker.invoice_ids | po_haulier.invoice_ids | duties_bill):
    if move.amount_residual:
        pay(move, f"pago {move.ref}")
paid = (inv1 | inv2 | bill_eur | bill_usd | po_broker.invoice_ids | po_haulier.invoice_ids | duties_bill)
check("9 every invoice and bill paid and matched with a bank line", [],
      [m.name for m in paid if m.payment_state not in ("paid", "in_payment")])
file.invalidate_recordset()
check("9 collected = the customer invoices", round(inv1.amount_total + inv2.amount_total, 2), round(file.amount_collected, 2))
gap("S1 supplier payments by SEPA batch (XML generated, never sent)", "F8")


def split_invoice():
    """An invoice shared by two files counts for each in proportion (50 % here)."""
    other = env["account.analytic.account"].create({"name": "[PRUEBA] E2E otro expediente",
                                                    "plan_id": file.analytic_account_id.plan_id.id})
    before = file.amount_collected
    inv = Move.create({"move_type": "out_invoice", "partner_id": customer.id, "invoice_date": date(2026, 12, 16),
                       "invoice_line_ids": [Command.create({
                           "name": "[PRUEBA] servicio compartido", "quantity": 1, "price_unit": 1000.0,
                           "tax_ids": [Command.set(env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 21),
                                                                               ("company_id", "=", company.id)], limit=1).ids)],
                           "analytic_distribution": {str(file.analytic_account_id.id): 50.0, str(other.id): 50.0}})]})
    inv.action_post()
    pay(inv, "cobro compartido")
    file.invalidate_recordset()
    check("9 an invoice shared 50/50 with another file adds 50 % of its collection", round(inv.amount_total / 2, 2),
          round(file.amount_collected - before, 2))


outcome(split_invoice)

# ---- 10. operational and financial close ---------------------------------------------------------------------------------
file.action_close_operations()
check("10 operations closed", "closed", file.state)
gap("S1 conditions of the operational close and freeze of the shipment data", "F10", "a click, nothing frozen")
refused("10 the financial close waits for the cost variances to be reviewed", file.action_close_financial)
to_review = file.cost_ids.filtered("variance_to_review")
check("10 variances to review: THC billed above the order, BL lowered by the supplier credit note", ["BL", "THC"],
      sorted(to_review.mapped("product_id.default_code")))
to_review.write({"variance_reviewed": True, "variance_note": "[PRUEBA] revisado: tarifa nueva y abono de la naviera"})
env.invalidate_all()  # the figures of the file and of its needs are computed on read (the form reloads them)
check("10 nothing left in «To do»", False, file.completeness)
refused("10 a sales user cannot close financially (checked on the server)",
        lambda: file.with_user(sales_user).action_close_financial())
file.action_close_financial()
check("10 file closed financially", True, file.financial_closed)
refused("10 an invoicing user who is not accounting manager cannot reopen it",
        lambda: file.with_user(invoicing_user).action_reopen_financial())


def late_bill():
    bill = Move.with_context(**ctx).create({
        "move_type": "in_invoice", "partner_id": haulier.id, "invoice_date": date(2026, 12, 21), "ref": "[PRUEBA] tarde",
        "invoice_line_ids": [Command.create({"product_id": product("TTE-FCL").id, "quantity": 1, "price_unit": 50.0,
                                             "tax_ids": [Command.set(purchase_0.ids)]})]})
    bill.action_post()


got, _msg = outcome(late_bill)
gap("S1 nothing can be posted on a financially closed file", "F10", got)
file.invalidate_recordset()
print(f"      {file.name}: sale {file.amount_sale:.2f} invoiced {file.amount_invoiced:.2f} actual cost "
      f"{file.amount_cost_actual:.2f} final margin {file.amount_margin_final:.2f} collected {file.amount_collected:.2f} "
      f"paid {file.amount_paid:.2f}")
check("10 final margin = invoiced - actual cost", round(file.amount_invoiced - file.amount_cost_actual, 2),
      round(file.amount_margin_final, 2))

# ---- other traffics: not built yet ------------------------------------------------------------------------------------
for scenario, phase in (("S2 air export (EAB) quotation to financial close", "F11"),
                        ("S3 air import (IAB) with NOA, handler and storage period", "F11"),
                        ("S4 sea export FCL (EMB) with cut-offs and detention", "F12"),
                        ("S5 LCL import and export", "F12"), ("S6 road / national", "F12"),
                        ("S7 agent's business in USD with profit share", "F13")):
    gap(scenario, phase)

passed, failed = results.count(True), results.count(False)
print(f"RESULT {passed} passed, {failed} failed, {len(gaps)} gaps | file {file.name} | order {order.name}")
env.cr.rollback()
