"""End-to-end check of a complete file on boss20 (plan «expediente completo»; phase F1, reinforced 28/10/2026).

Scenario S1 — sea import FCL with customs (IMB FOB), from the quotation to the financial close, each step run by a
[PRUEBA] user with the role that does it at BOSS (sales: quotation and acceptance; operations: purchases, dates, states;
accounting: bills, invoices, payments, bank, financial close), with negative checks on what each role must not do.
Payments are proven settled: nothing left to pay, every receivable/payable line reconciled, the matched amounts equal
the total, the bank statement line reconciled for the amount paid.

What the current path needs a person to do by hand is printed as «MANUAL …». Steps not built yet are printed as
«GAP [kind] <step> → <phase>» where kind is: defect (approved behaviour not met), decision (business rule missing,
question in docs/decisiones-f0.md), feature (not built yet). Gaps are declared, never counted as failures.

MODE «rollback»: everything made here is undone at the end (decision F0 on the production database pending). The
rollback does NOT give back sequence numbers (files E26…, orders S…, journal sequences): each run consumes some.
Fictitious prices only ([PRUEBA] suppliers and customer). Prints «CHECK PASS|FAIL …», «MANUAL …», «GAP …» and
«RESULT n passed, m failed, g gaps, k manual steps»; exits with status 1 when a check fails.
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
FORCE_FAIL = False  # set True only to prove the exit status (never committed as True)
results, gaps, manual_steps = [], [], []
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


def gap(step, kind, phase, observed=""):
    assert kind in ("defect", "decision", "feature"), kind
    gaps.append((kind, step))
    print(f"GAP [{kind}] {step} → {phase}" + (f" (today: {observed})" if observed else ""))


def manual(step):
    manual_steps.append(step)
    print(f"MANUAL {step}")


def next_step(label, expected, user=None):
    """The suggested next step of the file (roadmap item 1), as the role that works on it sees it."""
    env.invalidate_all()
    check(f"{label} next step «{expected}»", expected, (file.with_user(user) if user else file).next_step)


def go(user):
    """The «Go» button of the next step, pressed by the role: the action it returns (or None)."""
    env.invalidate_all()
    return file.with_user(user).action_next_step()


ref = env.ref
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
state = lambda code: env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", code)], limit=1)  # noqa: E731
template = lambda code: env["sale.order.template"].search([("name", "=like", f"{code} · %")], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
line_of = lambda o, code: o.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731
Partner, Tariff = env["res.partner"], env["boss.tariff"]
company = env.company
belal = env["res.users"].search([("login", "=", "devbms")], limit=1)
dv = ref("boss_pricing.container_type_dv")
usd, eur = ref("base.USD"), ref("base.EUR")
bank = env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", company.id), ("code", "=", "BNK1")],
                                    limit=1) or env["account.journal"].search([("type", "=", "bank"),
                                                                              ("company_id", "=", company.id)], limit=1)
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                                         ("company_id", "=", company.id)], limit=1)
sale_21 = env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 21),
                                      ("company_id", "=", company.id)], limit=1)
files_before = env["boss.expediente"].search_count([])
print(f"MODE {MODE} | files before {files_before} | bank journal {bank.code} | setting P30 {company.boss_bill_before_invoice}")

# ---- 0b. every form opens (smoke test) -------------------------------------------------------------------------------
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
if FORCE_FAIL:
    check("0z deliberate failure (proves the exit status)", True, False)

# ---- 0. parties, users by role, approved supplier prices ([PRUEBA], fictitious figures) ------------------------------
# The customer gets its own [PRUEBA] pricelist with only «cost + %»: the general pricelist holds BOSS's real selling prices
# since 03/11/2026 (Odoo 17 «Standard»), which must not drive this check nor appear in its evidence.
markup = env["res.config.settings"]._boss_get_default_markup() or 20.0
test_pricelist = env["product.pricelist"].create({
    "name": "[PRUEBA] E2E tarifa (coste + %)", "currency_id": eur.id,
    "item_ids": [Command.create({"applied_on": "3_global", "base": "boss_line_cost", "compute_price": "markup",
                                 "price_markup": markup, "price_round": 0.01})]})
customer = Partner.create({"name": "[PRUEBA] E2E Importador, S.L.", "is_company": True, "country_id": ref("base.es").id,
                           "vat": "ESB12345674", "street": "Calle Prueba 2", "city": "Madrid", "state_id": state("M").id,
                           "property_product_pricelist": test_pricelist.id})
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
sales = user("comercial", ["sales_team.group_sale_salesman"])
ops = user("operaciones", ["sales_team.group_sale_salesman", "purchase.group_purchase_user"])
acct = user("contabilidad", ["account.group_account_user", "sales_team.group_sale_salesman",
                             "purchase.group_purchase_user"])
print(f"      roles: comercial = salesman; operaciones = salesman + purchase user; contabilidad = full accounting "
      f"(not administrator) + salesman + purchase user; tariffs approved by {belal.login}")


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


tariffs = [approved_tariff("gastos locales", carrier, eur, {"THC": 200.0, "BL": 50.0, "GLO-CCC": 30.0, "T3-PAD": 40.0},
                           carrier_id=carrier.id),
           approved_tariff("flete Shanghái-Valencia", carrier, usd, {"FMI": 1000.0}, carrier_id=carrier.id,
                           foreign_port_ids=[Command.set(port("CNSHA", "sea").ids)],
                           valid_from=date(2026, 11, 2), valid_to=date(2026, 11, 8)),
           approved_tariff("despacho", broker, eur, {"FAD": 100.0}),
           approved_tariff("transporte contenedor", haulier, eur, {"TTE-FCL": 300.0})]
check("0 approved [PRUEBA] supplier prices (local EUR, freight USD, customs, trucking)", ["approved"] * 4,
      [t.state for t in tariffs])

# ---- 1. quotation (sales) ---------------------------------------------------------------------------------------------
with Form(env["sale.order"].with_user(sales)) as form:
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
manual("1 duties (ARA): the amount paid on behalf is typed as a manual cost (no tariff for duties)")
line_of(order, "CSM").price_unit = 60.0
manual("1 BOSS own fee (CSM): selling price typed (no supplier cost)")
order.action_boss_update_costs()
ara = line_of(order, "ARA")
check("1 duties paid on behalf proposed at the amount paid, without margin (F0-A00)", (500.0, "cost_based"),
      (round(ara.price_unit, 2), ara.boss_sale_status))
for l in order.order_line.filtered("product_id"):
    print(f"      {l.product_id.default_code:8} {l.boss_cost_status:16} cost {l.boss_cost_amount:9.2f} "
          f"{l.boss_cost_currency_id.name or '':3} sale {l.price_unit:9.2f} vat {l.boss_vat_status}")
check("1 every supplier service priced (tariff, or manual amount with its note)", [],
      [l.product_id.default_code for l in order.order_line.filtered("product_id")
       if l.boss_cost_status not in ("ok", "manual")])
check("1 freight from the USD rate of the departure week", ("ok", "USD"),
      (line_of(order, "FMI").boss_cost_status, line_of(order, "FMI").boss_cost_currency_id.name))
check("1 nothing blocks acceptance (VAT decided, every sale price set)", [],
      [l.product_id.default_code for l in order.order_line.filtered("product_id")
       if l.boss_vat_status == "pending" or l.boss_sale_status == "missing"])

# ---- 2. acceptance → file (sales) ----------------------------------------------------------------------------------------
order.action_confirm()
file = env["boss.expediente"].browse(order.boss_expediente_id.id)  # observed as superuser; each role acts with_user
check("2 the salesman accepts: one file with its analytic account", ("sale", 1, True),
      (order.state, len(order.boss_expediente_ids), bool(file.analytic_account_id)))
bought = order.order_line.filtered(lambda l: l.product_id and l.boss_execution == "supplier")
check("2 one purchase need per bought service", len(bought), len(file.cost_ids))
refused("2 the salesman cannot read the cost variance of a need (cost groups only)",
        lambda: file.cost_ids[:1].with_user(sales).read(["variance_company"]))
next_step("2 the salesman sees the", "order", sales)
check("2 «Create RFQs» shown (something to order) and «Invoice services» shown (something to invoice)", (True, True),
      (file.has_to_order, file.has_to_invoice))
bindings = env["ir.actions.actions"].with_user(ops).get_bindings("boss.expediente")["action"]
check("2 occasional actions in the «Actions» menu of the form; «Add a service» for sales managers only",
      ["Move services to another file", "Recompute expected cost", "Sell another service"],
      sorted(b["name"] for b in bindings if b.get("binding_view_types") == "form"))
gap("S1 milestone plan of the traffic (an activity per step)", "feature",
    "F5 (Cristina's list: Nuevo Odoo › Hoja1 A13/A19)", "the next step guides the file; operator from the table")
gap("S1 documents folder of the file", "feature", "F6", "attachments in the chatter only")

# ---- 3. purchases (operations) -------------------------------------------------------------------------------------------
file_ops = file.with_user(ops)
go(ops)  # «Go» on «Create the requests for quotation»
pos = file.purchase_order_ids
print(f"      purchase orders seen by superuser {len(pos)}, by operations {len(file_ops.purchase_order_ids)}, "
      f"by the salesman {len(file.with_user(sales).purchase_order_ids)}")
check("3 operations creates the RFQs: carrier EUR + carrier USD + customs broker + haulier (duties need no order)",
      sorted([(carrier.name, "EUR"), (carrier.name, "USD"), (broker.name, "EUR"), (haulier.name, "EUR")]),
      sorted((p.partner_id.name, p.currency_id.name) for p in pos))
check("3 duties (ARA) wait for the broker's bill without order", "awaiting_bill",
      file.cost_ids.filtered(lambda n: n.product_id == product("ARA")).state)
next_step("3", "confirm_rfq", ops)
action = go(ops)
check("3 «Go» opens the 4 RFQs to confirm, «Create RFQs» hidden", ("purchase.order", sorted(pos.ids), False),
      (action["res_model"], sorted(action["domain"][0][2]), file.has_to_order))
for po in pos.with_user(ops):
    po.partner_ref = f"[PRUEBA] conf. {po.partner_id.name[-12:]}"
    po.button_confirm()
manual("3 supplier confirmation: the supplier's reference typed on each order")
check("3 every order confirmed by operations with the supplier's reference", [("purchase", True)] * len(pos),
      [(p.state, bool(p.partner_ref)) for p in pos])

# ---- 4. booking and departure (operations) -------------------------------------------------------------------------------
env.invalidate_all()
check("4 the next step says what the file still lacks before leaving (departure, booking, B/L, containers)", True,
      "ATD" in (file.with_user(ops).next_step_detail or ""))
got, _msg = outcome(file_ops.action_in_transit)
check("4 «In transit» without those data is accepted with a warning in its history (Odoo 17 practice, package 3)",
      "accepted", got)
file_ops.write({"booking_ref": "BK-PRUEBA-1", "mbl_ref": "MBL-PRUEBA-1", "hbl_ref": "HBL-PRUEBA-1",
                "vessel": "[PRUEBA] VESSEL", "voyage": "001E", "atd": datetime(2026, 11, 5, 18, 0)})
file_ops.container_ids.write({"number": "PRUU1234565", "seal": "SEAL-1"})
arch = etree.fromstring(env["boss.expediente"].get_view(view_type="form")["arch"])
atd_field = arch.xpath("//page[@name='references']//field[@name='atd']")
pickup_field = arch.xpath("//page[@name='references']//field[@name='pickup_date']")  # not the containers' column
check("4 ATD and actual pickup shown on every file (import ATD, export pickup)", (True, True),
      (bool(atd_field) and not atd_field[0].get("invisible"), bool(pickup_field) and not pickup_field[0].get("invisible")))
next_step("4", "in_transit", ops)
go(ops)  # «Go» on «Put the file in transit»
check("4 operations puts the file in transit", "in_transit", file.state)
next_step("4", "arrived", ops)

# ---- 5. destination (operations) ------------------------------------------------------------------------------------------
refused("5 «Delivered» is refused while arrival, discharge, customs release, delivery date or B/L release are missing "
        "(Cristina OPS- exptes A42/A73; Odoo 17 «Check Update 3-4»)", file_ops.action_delivered)
file_ops.write({"ata": datetime(2026, 12, 7, 6, 0), "discharge_date": datetime(2026, 12, 7, 14, 0),
                "customs_ref": "[PRUEBA] 26ES00460010000001", "customs_guarantee": "boss",
                "customs_admission_date": datetime(2026, 12, 8, 9, 0)})
check("5 typing the ATA marks the file arrived (Odoo 17 «Llegado», F0-C22)", "arrived", file.state)
next_step("5", "delivered", ops)
file_ops.container_ids.write({"pickup_date": date(2026, 12, 10), "return_date": date(2026, 12, 12)})
file_ops.delivery_date = datetime(2026, 12, 10, 11, 0)
refused("5 no transport order to the haulier before the house B/L is released or a sea waybill (Cristina A73)",
        file_ops.action_print_transport_order)
refused("5 ... nor «Delivered» without the customs release (levante) of a declaration cleared by BOSS",
        file_ops.action_delivered)
file_ops.write({"customs_channel": "green", "customs_release_date": datetime(2026, 12, 9, 12, 0),
                "hbl_release": "released"})
manual("5 customs: channel, admission and release (levante) typed by operations from the DUA")
check("5 the transport order is printed for the haulier once the B/L is released",
      "ir.actions.report", file_ops.action_print_transport_order()["type"])
html = env["ir.actions.report"]._render_qweb_html("boss_documents.action_report_transport_order", file.ids)[0].decode()
check("5 the transport order shows the file, the haulier and the container, not the customer's reference",
      (True, True, True, False), (file.name in html, haulier.name in html, "PRUU1234565" in html, "PO-[PRUEBA]-E2E" in html))
go(ops)  # «Go» on «Mark the file delivered»
check("5 operations marks the file delivered", "delivered", file.state)
check("5 the day of the delivery is kept (Cristina: close operations within a week of it)", True, bool(file.delivered_date))
refused("5 operations cannot close before every service is invoiced (F0-A07, Belal; F0-C60, Cristina)",
        file_ops.action_close_operations)

# ---- 6. performed services (operations) and vendor bills (accounting) -----------------------------------------------------
ordered = file.cost_ids.filtered("purchase_line_ids")
next_step("6", "perform", ops)
action = go(ops)
todo_view = ref("boss_expediente.boss_expediente_cost_view_list_todo")
check("6 «Go» opens the ordered services in the list where they are marked performed",
      ("boss.expediente.cost", sorted(ordered.ids), todo_view.id),
      (action["res_model"], sorted(action["domain"][0][2]), action["views"][0][0]))
ordered.with_user(ops).action_mark_performed()
check("6 operations marks every ordered service performed", ["performed"] * len(ordered), ordered.mapped("state"))
next_step("6 operations sees the", "invoice", ops)
check("6 «Go» on «Invoice the customer» opens the invoice wizard", "boss.invoice.services", go(ops)["res_model"])
po_eur = pos.filtered(lambda p: p.partner_id == carrier and p.currency_id == eur)
po_usd = pos.filtered(lambda p: p.partner_id == carrier and p.currency_id == usd)
po_broker = pos.filtered(lambda p: p.partner_id == broker)
po_haulier = pos.filtered(lambda p: p.partner_id == haulier)


def bill_of(po, ref_text, day, price_changes=None):
    po.with_user(acct).action_create_invoice()
    bill = po.invoice_ids.filtered(lambda m: m.state == "draft")[:1].with_user(acct)
    bill.write({"invoice_date": day, "ref": ref_text})
    bill.invoice_line_ids.tax_ids = purchase_0
    for code, price in (price_changes or {}).items():
        bill.invoice_line_ids.filtered(lambda l, c=code: l.product_id.default_code == c).price_unit = price
    return bill


bill_eur = bill_of(po_eur, "[PRUEBA] NAV-1", date(2026, 12, 11), {"THC": 220.0})  # 20 above the order
manual("6 vendor bills: supplier reference, date and the tax of the supplier document typed by accounting")
refused("6 the salesman cannot post a vendor bill", lambda: bill_eur.with_user(sales).action_post())
bill_eur.action_post()
check("6 accounting posts the bill; its lines carry the file", ("posted", True),
      (bill_eur.state, all(l.boss_expediente_id == file for l in bill_eur.invoice_line_ids)))
thc_need = file.cost_ids.filtered(lambda n: n.product_id == product("THC"))
check("6 THC billed 220 for 200 ordered: variance to review", (True, 20.0),
      (thc_need.variance_to_review, round(thc_need.variance_company, 2)))
refund = bill_eur._reverse_moves([{"ref": "[PRUEBA] abono BL", "date": date(2026, 12, 12),
                                   "invoice_date": date(2026, 12, 12)}]).with_user(acct)
refund.invoice_line_ids.filtered(lambda l: l.product_id.default_code != "BL").unlink()
refund.invoice_line_ids.price_unit = 10.0
refund.action_post()
(bill_eur | refund).line_ids.filtered(lambda l: l.account_id.account_type == "liability_payable").reconcile()
bill_usd = bill_of(po_usd, "[PRUEBA] NAV-USD-1", date(2026, 12, 11))
bill_usd.action_post()
check("6 freight bill in USD posted, at the order price", ("USD", 1000.0),
      (bill_usd.currency_id.name, round(bill_usd.amount_untaxed, 2)))
gap("S1 USD variance split into price and exchange rate", "decision", "F8 (P03: Ángel)", "one variance figure")
bills_po = [bill_of(po, ref_text, date(2026, 12, 11)) for po, ref_text in
            ((po_broker, "[PRUEBA] ADU-1"), (po_haulier, "[PRUEBA] TTE-1"))]
for bill in bills_po:
    bill.action_post()
ctx = file.action_new_bill()["context"]
duties_bill = env["account.move"].with_user(acct).with_context(**ctx).create({
    "partner_id": broker.id, "invoice_date": date(2026, 12, 11), "ref": "[PRUEBA] ADU-SUPLIDOS",
    "invoice_line_ids": [Command.create({"product_id": product("ARA").id, "quantity": 1, "price_unit": 500.0,
                                         "tax_ids": [Command.set(purchase_0.ids)]})]})
duties_bill.action_post()
ara_need = file.cost_ids.filtered(lambda n: n.product_id == product("ARA"))
check("6 duties bill without order: carries the file, the duties need is billed", (file, "billed"),
      (duties_bill.invoice_line_ids.boss_expediente_id, ara_need.state))
env.invalidate_all()
all_bills = bill_eur | refund | bill_usd | bills_po[0] | bills_po[1] | duties_bill
check("6 actual cost = posted bills - supplier credit note (USD at the bill rate), duties counted once",
      round(-sum(all_bills.sudo().mapped("amount_untaxed_signed")), 2), round(file.amount_cost_actual, 2))

# ---- 7. P30: no payment issued before the customer invoice; a bank movement that happened is recorded and flagged ---------


def register_payment(move, day):
    wizard = env["account.payment.register"].with_user(acct).with_context(
        active_model="account.move", active_ids=move.ids).create({"journal_id": bank.id, "payment_date": day})
    return wizard._create_payments()


def statement_line(partner, amount, label, day):
    return env["account.bank.statement.line"].with_user(acct).create({
        "journal_id": bank.id, "date": day, "payment_ref": f"[PRUEBA] E2E {label}", "partner_id": partner.id,
        "amount": amount})


refused("7 accounting cannot issue the carrier's payment before the customer is invoiced (P30, payment wizard)",
        lambda: register_payment(bill_eur, date(2026, 12, 13)))
refused("7 operations cannot register payments at all", lambda: env["account.payment.register"].with_user(ops)
        .with_context(active_model="account.move", active_ids=bill_usd.ids).create({"journal_id": bank.id}))


def bank_movement_before_invoice():
    st = statement_line(carrier, -abs(bill_eur.amount_residual_signed), "cargo directo naviera", date(2026, 12, 13))
    st.set_line_bank_statement_line(bill_eur.line_ids.filtered(
        lambda l: l.account_id.account_type == "liability_payable").ids)
    env.invalidate_all()
    notes = bill_eur.sudo().message_ids.filtered(lambda m: "P30" in (m.body or ""))
    check("7 a bank movement that already happened is recorded and flagged (bill note, file «To do»), not blocked",
          (True, True, True, True),
          (st.is_reconciled, bill_eur.boss_paid_before_invoice, bool(notes), "paid before" in (file.completeness or "")))


got, message = outcome(bank_movement_before_invoice)
check("7 ... the reconciliation itself is accepted", "accepted", got)
gap("S1 P30 on a bank movement already made: record and flag (implemented) or block", "decision",
    "F0-A81 (Ángel + Cristina)")

# ---- 8. customer invoices (accounting): partial, then the rest -------------------------------------------------------------
Invoice = env["boss.invoice.services"].with_user(acct)
thc_alloc = file.allocation_ids.filtered(lambda a: a.product_id == product("THC"))
inv1 = env["account.move"].with_user(acct).browse(
    Invoice.create({"expediente_id": file.id, "allocation_ids": [Command.set(thc_alloc.ids)]}).action_create()["res_id"])
inv1.invoice_date = date(2026, 12, 14)
inv1.action_post()
rest = file.allocation_ids.filtered(lambda a: a.to_invoice_quantity > 0)
result = Invoice.create({"expediente_id": file.id, "allocation_ids": [Command.set(rest.ids)]}).action_create()
inv2 = env["account.move"].with_user(acct).browse(result.get("res_id") or result["domain"][0][2])
inv2.invoice_date = date(2026, 12, 15)
inv2.action_post()
duties_inv = inv2.filtered(lambda m: all(l.product_id.boss_paid_on_behalf for l in m.invoice_line_ids))
check("8 the duties paid on behalf get an invoice of their own, the services another, same series (F0-A21, F0-A22)",
      (2, 1, {inv1.journal_id}), (len(inv2), len(duties_inv), set(inv2.journal_id)))
check("8 ... with the mention of art. 78.Tres.3º Ley 37/1992 and the DUA (F0-A15)", (True, True),
      ("78.Tres" in str(duties_inv.narration or ""), (file.customs_ref or "-") in str(duties_inv.narration or "")))
env.invalidate_all()
check("8 everything invoiced (partial THC, then the rest)", (round(file.amount_sale, 2), 0.0),
      (round(file.amount_invoiced, 2), round(file.amount_to_invoice, 2)))
next_step("8", "close_operations", ops)
check("8 «Invoice services» hidden (nothing left to invoice)", False, file.has_to_invoice)
check("8 the customer invoice lines carry the file", True,
      all(l.boss_expediente_id == file for l in (inv1 | inv2).invoice_line_ids))
gap("S1 legal mention of every 0 % tax, company IBAN and agreed series on the invoice", "decision",
    "F4 (texts, bank, series: Ángel)", "no bank account on the company; legal notes on some 0 % taxes only")

# ---- 9. collections and payments, proven settled ------------------------------------------------------------------------


def pay_and_prove(move, label, day=date(2026, 12, 20)):
    """Register the payment, match it with a bank statement line, then prove the settlement."""
    expected = abs(move.amount_residual_signed)  # company currency: what the bank line shows
    total = abs(move.amount_total_signed)
    payment = register_payment(move, day)
    sign = 1 if move.move_type in ("out_invoice", "in_refund") else -1
    st = statement_line(move.partner_id, sign * expected, label, day)
    if payment.move_id:
        to_match = payment.move_id.line_ids.filtered(lambda l: l.account_id == payment.outstanding_account_id)
    else:
        to_match = move.line_ids.filtered(lambda l: l.account_id.account_type in ("asset_receivable", "liability_payable"))
    st.set_line_bank_statement_line(to_match.ids)
    env.invalidate_all()
    terms = move.sudo().line_ids.filtered(lambda l: l.account_id.account_type in ("asset_receivable", "liability_payable"))
    matched = sum(terms.matched_debit_ids.mapped("amount")) + sum(terms.matched_credit_ids.mapped("amount"))
    check(f"9 {label}: nothing left to pay, every term line reconciled, matched = total, bank line reconciled for the "
          f"amount paid", (True, True, round(total, 2), True, round(expected, 2)),
          (move.currency_id.is_zero(move.amount_residual), all(terms.mapped("reconciled")), round(matched, 2),
           st.is_reconciled, round(abs(st.amount), 2)))


for move, label in [(inv1, "cobro THC")] + [(m, f"cobro resto {i}") for i, m in enumerate(inv2, 1)]:
    pay_and_prove(move, label)
for move in (bill_eur, bill_usd, bills_po[0], bills_po[1], duties_bill):
    pay_and_prove(move, f"pago {move.ref}")
env.invalidate_all()
check("9 collected = the customer invoices", round(inv1.amount_total + sum(inv2.mapped("amount_total")), 2),
      round(file.amount_collected, 2))
check("9 paid = the bills less the supplier credit note (company currency)",
      round(-sum((bill_eur | bill_usd | bills_po[0] | bills_po[1] | duties_bill | refund).sudo().mapped("amount_total_signed")), 2),
      round(file.amount_paid, 2))
gap("S1 supplier payments by SEPA batch (XML generated, never sent)", "feature", "F8")
other = env["account.analytic.account"].create({"name": "[PRUEBA] E2E otro expediente",
                                                "plan_id": file.analytic_account_id.plan_id.id})
split = {str(file.analytic_account_id.id): 50.0, str(other.id): 50.0}


def shared(move_type, partner, tax, label):
    before = (file.amount_collected, file.amount_paid)
    move = env["account.move"].with_user(acct).create({
        "move_type": move_type, "partner_id": partner.id, "invoice_date": date(2026, 12, 16), "ref": f"[PRUEBA] {label}",
        "invoice_line_ids": [Command.create({"name": f"[PRUEBA] {label}", "quantity": 1, "price_unit": 1000.0,
                                             "tax_ids": [Command.set(tax.ids)], "analytic_distribution": split})]})
    move.action_post()
    pay_and_prove(move, label)
    env.invalidate_all()
    delta = (file.amount_collected - before[0], file.amount_paid - before[1])
    return move, delta


def shared_invoice():
    move, delta = shared("out_invoice", customer, sale_21, "servicio compartido")
    check("9 a customer invoice shared 50/50 with another file adds 50 % of its collection",
          (round(move.amount_total / 2, 2), 0.0), (round(delta[0], 2), round(delta[1], 2)))


def shared_bill():
    move, delta = shared("in_invoice", haulier, purchase_0, "coste compartido")
    check("9 a vendor bill shared 50/50 with another file adds 50 % of its payment to «paid»",
          (0.0, round(move.amount_total / 2, 2)), (round(delta[0], 2), round(delta[1], 2)))


outcome(shared_invoice)
outcome(shared_bill)

# ---- 10. closes: operations, then accounting -----------------------------------------------------------------------------
action = go(ops)  # «Go» on «Close operations»: the parties are not rated yet (F0-C66, as Odoo 17)
check("10 the close first asks to rate the customer and the suppliers (lines listed in «Ratings», nothing closed)",
      ("display_notification", "delivered", True), (action["tag"], file.state, bool(file.rating_ids)))
check("10 the customer and every supplier bought from are listed to rate", True,
      {customer.commercial_partner_id, haulier.commercial_partner_id} <= set(file.rating_ids.partner_id))
file.rating_ids.with_user(ops).write({"rating": "8"})
manual("10 operations rates the customer and the suppliers of the file (0-10)")
go(ops)  # «Go» on «Close operations»
check("10 operations closes operations", "closed", file.state)
check("10 the supplier's average rating is on the contact and in «Services to buy»", (8.0, 8.0),
      (haulier.commercial_partner_id.boss_rating_avg,
       file.cost_ids.filtered(lambda n: n.partner_id.commercial_partner_id == haulier.commercial_partner_id)[:1].supplier_rating))
refused("10 the shipment data is frozen once operations are closed (Odoo 17 froze it): the vessel cannot change",
        lambda: file.with_user(ops).write({"vessel": "[PRUEBA] OTRO BUQUE"}))
next_step("10", "review", acct)
action = go(acct)
# Since the daily ECB rates (05/11/2026) a USD cost billed at the order price shows a variance that is only the exchange
# rate (ordered at the quotation rate, billed at the bill rate): accounting reviews it like any other until P03 splits
# price and rate variances (gap declared below).
fx_only = sorted(n.product_id.default_code for n in file.cost_ids.filtered("variance_to_review")
                 if n.currency_id != env.company.currency_id)
if fx_only:
    print(f"      exchange-rate-only variances to review: {fx_only}")
check("10 «Go» opens the services to review (variances)", sorted(["BL", "THC"] + fx_only),
      sorted(env["boss.expediente.cost"].browse(action["domain"][0][2]).mapped("product_id.default_code")))
refused("10 the financial close waits for the cost variances to be reviewed",
        lambda: file.with_user(acct).action_close_financial())
to_review = file.cost_ids.filtered("variance_to_review")
check("10 variances to review: THC billed above the order, BL lowered by the supplier credit note", sorted(["BL", "THC"] + fx_only),
      sorted(to_review.mapped("product_id.default_code")))
to_review.with_user(acct).write({"variance_reviewed": True,
                                 "variance_note": "[PRUEBA] revisado: tarifa nueva y abono de la naviera"})
manual("10 variances reviewed by accounting with a note (THC +20, BL -10)")
env.invalidate_all()
check("10 nothing left in «To do»", False, file.completeness)
next_step("10", "close_financial", acct)
refused("10 operations cannot close financially (checked on the server)", lambda: file_ops.action_close_financial())
file.with_user(acct).action_close_financial()
check("10 accounting closes financially", True, file.financial_closed)
row = env["boss.margin.report"].search([("expediente_id", "=", file.id)])
check("10 «Margin by file» keeps the final margin of the file closed financially", (1, True, True),
      (len(row), row.margin_final, file.currency_id.compare_amounts(row.amount_margin_final, file.amount_margin_final) == 0))
next_step("10 the salesman sees the", "done", sales)
refused("10 accounting (not administrator) cannot reopen it", lambda: file.with_user(acct).action_reopen_financial())


def late_bill():
    bill = env["account.move"].with_user(acct).with_context(**ctx).create({
        "move_type": "in_invoice", "partner_id": haulier.id, "invoice_date": date(2026, 12, 21), "ref": "[PRUEBA] tarde",
        "invoice_line_ids": [Command.create({"product_id": product("TTE-FCL").id, "quantity": 1, "price_unit": 50.0,
                                             "tax_ids": [Command.set(purchase_0.ids)]})]})
    bill.action_post()


refused("10 nothing is posted on a financially closed file (reopen first)", late_bill)
refused("10 no RFQ from a financially closed file", file_ops.action_create_rfqs)
refused("10 no customer invoice from a financially closed file", file.with_user(acct).action_invoice_services)
gap("S1 posting on a closed file blocked (implemented) or only warned", "decision", "F0-A80 (Ángel)")
env.invalidate_all()
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
    gap(scenario, "feature", phase)

passed, failed = results.count(True), results.count(False)
kinds = {k: sum(1 for kind, _s in gaps if kind == k) for k in ("defect", "decision", "feature")}
print(f"RESULT {passed} passed, {failed} failed, {len(gaps)} gaps ({kinds['defect']} defect, {kinds['decision']} decision, "
      f"{kinds['feature']} feature), {len(manual_steps)} manual steps | file {file.name} | order {order.name}")
env.cr.rollback()
if failed:
    raise SystemExit(1)
