"""boss20_uat only: the full BOSS cycle in one run, with explicit checks (expected value computed here from the [DEMO]
tariffs, then compared with what the system did). Each run creates its own records (tag «[UAT-E2E] <run>») and keeps
them, so every step can be opened in the UI afterwards.
    dev/uat_run.sh uat_e2e.py        (evidence with the tested commit in docs/evidencias/)

customer and shipment -> quotation template -> supplier, cost and sale price -> acceptance -> file and analytic account
-> purchases without duplicates -> actual execution (dates, performed) -> vendor bill -> partial and full customer
invoices -> credit note and extra cost re-invoiced -> test payments and bank reconciliation -> profitability.
[DEMO] tariffs used (fictitious): «[DEMO] MSC gastos locales importación Valencia 2026 (cliente español)»
THC 20' 180 €, THC 40' 240 €, DEM 7 free days then 30 €/day up to day 5 and 60 €/day after (per container)."""
from datetime import date, datetime

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.binary import BinaryBytes

assert env.cr.dbname == "boss20_uat", env.cr.dbname  # noqa: F821
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES", tracking_disable=True))  # noqa: F821
RUN = datetime.now().strftime("%Y%m%d-%H%M%S")
TAG = f"[UAT-E2E] {RUN}"
IMD = env["ir.model.data"]
results = []


def check(name, expected, got, tol=0.005):
    if isinstance(expected, float) or isinstance(got, float):
        ok = got is not None and expected is not None and abs(float(got) - float(expected)) <= tol
    else:
        ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")
    return ok


def refused(name, fn):
    try:
        with env.cr.savepoint():
            fn()
    except (UserError, ValidationError) as exc:
        return check(name, "refused", "refused") and print("      «" + " ".join(str(exc).split())[:200] + "»")
    return check(name, "refused", "accepted")


def xid(name):
    imd = IMD.search([("module", "=", "boss_trial"), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id).exists() if imd else None


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


def line(order, code, size=None):
    lines = order.order_line.filtered(lambda l: l.product_id.default_code == code
                                      and (size is None or l.boss_container_size == size))
    return lines[:1]


def pay_and_reconcile(move, label):
    """Register the payment (the BOSS payment block applies), then match it with a bank statement line."""
    journal = env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", env.company.id)], limit=1)
    amount = move.amount_residual
    wizard = env["account.payment.register"].with_context(active_model="account.move", active_ids=move.ids).create(
        {"journal_id": journal.id, "payment_date": date(2026, 11, 20)})
    payment = wizard._create_payments()
    sign = 1 if move.move_type == "out_invoice" else -1
    st_line = env["account.bank.statement.line"].create({
        "journal_id": journal.id, "date": date(2026, 11, 21), "payment_ref": f"{TAG} {label}",
        "partner_id": move.partner_id.id, "amount": sign * amount})
    if payment.move_id:  # payment with its own entry: the bank line matches the outstanding line
        to_match = payment.move_id.line_ids.filtered(lambda l: l.account_id == payment.outstanding_account_id)
    else:  # Odoo 20 payment without entry: the bank line matches the invoice itself
        to_match = move.line_ids.filtered(lambda l: l.account_id.account_type in ("asset_receivable", "liability_payable"))
    st_line.set_line_bank_statement_line(to_match.ids)
    move.invalidate_recordset()
    return payment, st_line


customer = xid("customer")  # [DEMO] Cliente Ejemplo, S.L. (Spain, NIF set by dev/uat_cycle.py)
tariff = env["boss.tariff"].search([("name", "=", "[DEMO] MSC gastos locales importación Valencia 2026 (cliente español)")])
msc = tariff.partner_id
check("0 data: [DEMO] Spanish customer with NIF and approved MSC tariff for it",
      (True, "approved"), (bool(customer.vat), tariff.state))

# 1. Customer and shipment data
order = env["sale.order"].create({
    "partner_id": customer.id, "client_order_ref": TAG, "origin": f"{TAG} importación marítima FCL",
    "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": msc.id,
    "boss_port_id": env.ref("boss_pricing.port_esvlc").id, "boss_country_id": env.ref("base.cn").id,
    "boss_planned_date": date(2026, 11, 10), "boss_storage_days": 10,
    "boss_container_ids": [Command.create({"size": "20", "container_type_id": env.ref("boss_pricing.container_type_dv").id,
                                           "quantity": 1}),
                           Command.create({"size": "40", "container_type_id": env.ref("boss_pricing.container_type_hc").id,
                                           "quantity": 1})]})

# 2. Services from the case template (IMB FOB) + DEM
template = env["sale.order.template"].search([("name", "=like", "[DEMO] IMB FOB%")], limit=1)
order.sale_order_template_id = template
order._onchange_sale_order_template_id()
env["boss.add.services"].create({"order_id": order.id, "product_ids": [Command.set(product("DEM").ids)]}).action_add()
codes = sorted(set(order.order_line.filtered(lambda l: not l.display_type).mapped("product_id.default_code")))
check("2 template services + DEM", sorted(set(template.sale_order_template_line_ids.product_id.mapped("default_code")) | {"DEM"}),
      codes)
check("2 THC split per container size (20' and 40')", ["20", "40"],
      sorted(order.order_line.filtered(lambda l: l.product_id.default_code == "THC").mapped("boss_container_size")))

# 3. Supplier, cost and sale price
check("3 THC 20' cost from the approved tariff", 180.0, line(order, "THC", "20").purchase_price)
check("3 THC 40' HC cost from the approved tariff", 240.0, line(order, "THC", "40").purchase_price)
check("3 THC supplier = MSC", msc, line(order, "THC", "20")._boss_purchase_partner())
dem = line(order, "DEM")
check("3 DEM estimate 10 days: (5 x 30 + (10-7-5<0 → 0)) → 3 chargeable days x 30 € per container", 90.0,
      dem.purchase_price)
# Services without an approved [DEMO] tariff for this customer: never a zero "free" cost. As on the quotation screen:
# freight (FMI, manual mode) and GLO-CCC get a manual cost from a (fictitious) supplier offer; BL, FAD and TTE-FCL get a
# supplier price recorded by the salesman and approved by the tariff approver (role user uat_operaciones).
broker, haulier = xid("demo_broker"), xid("haulier")
approver = env["res.users"].search([("login", "=", "uat_operaciones")], limit=1)
manual = {"FMI": (900.0, msc)}
priced = {"BL": (60.0, msc, "line"), "FAD": (85.0, broker, "line"), "TTE-FCL": (300.0, haulier, "containers"),
          "GLO-CCC": (40.0, msc, "containers")}
for l in order.order_line.filtered(lambda l: l.product_id.default_code in manual or l.product_id.default_code in priced):
    check(f"3 {l.product_id.default_code}{' ' + l.boss_container_size if l.boss_container_size else ''} without tariff "
          f"is not priced at 0", True, l.boss_cost_status in ("no_tariff", "pending_approval", "manual", "not_ready")
          and not l.purchase_price)
for l in order.order_line.filtered(lambda l: l.product_id.default_code in manual):
    cost, supplier = manual[l.product_id.default_code]
    l.write({"boss_manual_cost": cost, "boss_manual_cost_note": f"{TAG} oferta [DEMO]", "boss_supplier_id": supplier.id})
for code, (price, supplier, basis) in priced.items():
    prod = product(code)
    tariff_new = env["boss.tariff"].create({
        "name": f"{TAG} {supplier.name} {code}", "partner_id": supplier.id, "currency_id": env.company.currency_id.id,
        "valid_from": date(2026, 1, 1), "valid_to": date(2026, 12, 31), "direction": "import", "transport_mode": "sea",
        "load_type": "fcl", "customer_id": customer.id, "is_demo": True, "scope_confirmed": True,
        "document_reference": f"{TAG} oferta ficticia", "document_name": "demo.txt",
        "document": BinaryBytes(b"DEMO", filename="demo.txt"),
        "line_ids": [Command.create({"product_id": prod.id, "uom_id": prod.uom_id.id, "method": "per_unit",
                                     "basis": basis, "unit_price": price})]})
    tariff_new.action_submit()
    refused(f"3 {code}: the salesman cannot approve the supplier price",
            lambda t=tariff_new: t.with_user(env["res.users"].search([("login", "=", "uat_ventas")])).action_approve())
    tariff_new.with_user(approver).action_approve()
    check(f"3 {code}: supplier price approved by {approver.login}", ("approved", approver), (tariff_new.state,
                                                                                           tariff_new.approved_by_id))
order.action_boss_update_costs()
check("3 BL cost from the new approved price", 60.0, line(order, "BL").purchase_price)
check("3 TTE-FCL 20' cost from the new approved price", 300.0, line(order, "TTE-FCL", "20").purchase_price)
check("3 manual costs are taken as the line cost", 900.0, line(order, "FMI", "20").purchase_price)
sale = {"FMI": 1100.0, "THC": 280.0, "BL": 75.0, "GLO-CCC": 55.0, "FAD": 120.0, "CSM": 60.0, "TTE-FCL": 380.0,
        "DEM": 120.0}
for l in order.order_line.filtered(lambda l: not l.display_type):
    l.price_unit = sale[l.product_id.default_code]
expected_sale = sum(sale[l.product_id.default_code] * l.product_uom_qty for l in order.order_line if not l.display_type)
check("3 quotation untaxed = sum of the sale prices x quantities", expected_sale, order.amount_untaxed)
check("3 nothing blocks acceptance (VAT decided, every sale price set)", False, bool(order.order_line.filtered(
    lambda l: l.boss_vat_status == "pending" or l.boss_sale_status == "missing")))

# 4. Acceptance -> file and analytic account
print('      lines:', [(l.product_id.default_code, l.boss_container_size, l.display_type, l.boss_cost_kind,
                        l.boss_cost_status, l.purchase_price) for l in order.order_line])
order.action_confirm()
file = order.boss_expediente_id
check("4 order confirmed and file opened", ("sale", True), (order.state, bool(file)))
check("4 file has its analytic account", True, bool(file.analytic_account_id))
check("4 every sale line on the file's analytic account (100 %)", True, all(
    l.analytic_distribution == {str(file.analytic_account_id.id): 100.0} for l in order.order_line if not l.display_type))
supplier_needs = file.cost_ids.filtered(lambda n: n.partner_id and not n.without_order)
check("4 one need per bought line", len(order.order_line.filtered(lambda l: l.boss_execution == "supplier")),
      len(file.cost_ids))

# 5. Purchases without duplicates
file.action_create_rfqs()
po_lines = file.purchase_order_ids.order_line
refused("5 a second «Create RFQs» says there is nothing to order", file.action_create_rfqs)
check("5 ... and creates nothing", len(po_lines), len(file.purchase_order_ids.order_line))
check("5 one purchase order per supplier", sorted(set(supplier_needs.partner_id.ids)),
      sorted(file.purchase_order_ids.partner_id.ids))
check("5 every need with a supplier ordered exactly once", True,
      all(len(n.purchase_line_ids) == 1 for n in supplier_needs))
po = file.purchase_order_ids.filtered(lambda p: p.partner_id == msc)
po.button_confirm()
check("5 MSC order confirmed", "purchase", po.state)
check("5 purchase lines on the file's analytic account", True, all(
    l.analytic_distribution == {str(file.analytic_account_id.id): 100.0} for l in po.order_line))

# 6. Actual execution: dates and performed services
file.write({"ata": datetime(2026, 11, 10, 8, 0), "pickup_date": datetime(2026, 11, 22, 10, 0)})
dem20, dem40 = (file.cost_ids.filtered(lambda n, s=s: n.product_id.default_code == "DEM"
                                       and n.sale_line_id.boss_container_size == s) for s in ("20", "40"))
check("6 DEM waits for the containers' dates (arrival -> empty return, MSC p.18)", (False, False),
      (bool(dem20.period_end), bool(dem40.period_end)))
c20 = file.container_ids.filtered(lambda c: c.size == "20")
c40 = file.container_ids.filtered(lambda c: c.size == "40")
c20.write({"number": "DEMU2000001", "pickup_date": date(2026, 11, 13), "return_date": date(2026, 11, 18)})
c40.write({"number": "DEMU4000001", "pickup_date": date(2026, 11, 15), "return_date": date(2026, 11, 25)})
(dem20 | dem40).invalidate_recordset()
dem_rule = tariff.line_ids.filtered(lambda l: l.product_id.default_code == "DEM")
print(f"      DEM rule: {dem_rule.free_days} free, {dem_rule.free_mode}, {dem_rule.tier_mode}, "
      f"{[(b.up_to, b.unit_price) for b in dem_rule.bracket_ids]}")
check("6 DEM 20': period ATA 10/11 -> empty return 18/11", (datetime(2026, 11, 10, 8, 0), datetime(2026, 11, 18, 12, 0)),
      (dem20.period_start, dem20.period_end))
check("6 DEM 20': 9 days - 7 free = 2 x 30", 60.0, dem20.expected_amount)
check("6 DEM 40': 16 days - 7 free = 9: 5 x 30 + 4 x 60", 390.0, dem40.expected_amount)
check("6 DEM forecast recomputed with the file data", "recomputed", dem40.forecast_status)
check("6 the sale of DEM is not changed", 120.0, line(order, "DEM", "40").price_unit)
refused("6 bill with nothing performed (D-4)", po.action_create_invoice)
thc_needs = file.cost_ids.filtered(lambda n: n.product_id.default_code in ("THC", "BL", "FMI"))
thc_needs.action_mark_performed()
check("6 performed quantities on the order", sorted([1.0] * len(thc_needs)),
      sorted(po.order_line.filtered(lambda l: l.boss_cost_id in thc_needs).mapped("qty_received")))

# 7. Vendor bill (performed services only), posted; payment held until the customer is invoiced (P30)
po.action_create_invoice()
bill = po.invoice_ids[:1]
bill.write({"invoice_date": date(2026, 11, 23), "ref": f"{TAG} MSC-1"})
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                                         ("company_id", "=", env.company.id)], limit=1)
bill.invoice_line_ids.tax_ids = purchase_0
expected_bill = 2 * 900.0 + 180.0 + 240.0 + 60.0  # FMI 20' and 40' (manual) + THC 20' + THC 40' + BL
check("7 vendor bill = performed services only", expected_bill, bill.amount_untaxed)
bill.action_post()
check("7 vendor bill posted", "posted", bill.state)
refused("7 pay the bill before the customer invoice (P30)", lambda: pay_and_reconcile(bill, "bill early"))

# 8. Customer invoices: partial (THC only) then the rest
thc_alloc = file.allocation_ids.filtered(lambda a: a.product_id.default_code == "THC")
inv1 = env["account.move"].browse(env["boss.invoice.services"].create({
    "expediente_id": file.id, "allocation_ids": [Command.set(thc_alloc.ids)]}).action_create()["res_id"])
inv1.invoice_date = date(2026, 11, 24)
check("8 partial invoice = 2 THC", 560.0, inv1.amount_untaxed)
check("8 THC to a Spanish customer: exempt art. 22", True, all(
    "22" in " ".join(l.tax_ids.mapped("name")) for l in inv1.invoice_line_ids))
inv1.action_post()
rest = file.allocation_ids.filtered(lambda a: a.to_invoice_quantity > 0)
inv2 = env["account.move"].browse(env["boss.invoice.services"].create({
    "expediente_id": file.id, "allocation_ids": [Command.set(rest.ids)]}).action_create()["res_id"])
inv2.invoice_date = date(2026, 11, 25)
inv2.action_post()
file.invalidate_recordset()
check("8 everything invoiced after the second invoice", (expected_sale, 0.0),
      (round(file.amount_invoiced, 2), round(file.amount_to_invoice, 2)))

# 9. Credit note of the BL and an extra cost re-invoiced
bl_line = inv2.invoice_line_ids.filtered(lambda l: l.product_id.default_code == "BL")
refund = inv2._reverse_moves([{"ref": f"{TAG} abono BL", "date": date(2026, 11, 26), "invoice_date": date(2026, 11, 26)}])
refund.invoice_line_ids.filtered(lambda l: l.product_id.default_code != "BL").unlink()
refund.action_post()
(inv2 | refund).line_ids.filtered(lambda l: l.account_id.account_type == "asset_receivable" and not l.reconciled).reconcile()
check("9 credit note applied to the invoice it corrects", round(inv2.amount_total - refund.amount_total, 2),
      round(inv2.amount_residual, 2))
check("9 credit note = BL", 75.0, refund.amount_untaxed)
file.invalidate_recordset()
check("9 invoiced after the credit note", expected_sale - 75.0, file.amount_invoiced)
ocu = product("OCU")
extra = env["boss.expediente.cost"].create({
    "expediente_id": file.id, "product_id": ocu.id, "name": f"{TAG} ocupación de muelle extra", "uom_id": ocu.uom_id.id,
    "quantity": 1, "partner_id": msc.id, "currency_id": file.currency_id.id, "expected_unit_cost": 120.0,
    "extra_class": "approval", "reason": f"{TAG} retirada 3 días tarde"})
env["boss.rebill.wizard"].with_context(default_cost_id=extra.id).create(
    {"price_unit": 160.0, "reason": f"{TAG} el cliente acepta la ocupación extra"}).action_apply()
check("9 extra cost re-invoiced: new sale line 160 €", 160.0, extra.rebill_line_id.price_unit)
extra_alloc = file.allocation_ids.filtered(lambda a: a.sale_line_id == extra.rebill_line_id)
inv3 = env["account.move"].browse(env["boss.invoice.services"].create({
    "expediente_id": file.id, "allocation_ids": [Command.set(extra_alloc.ids)]}).action_create()["res_id"])
inv3.invoice_date = date(2026, 11, 27)
inv3.action_post()
ocu_bill = env["account.move"].with_context(boss_default_analytic={str(file.analytic_account_id.id): 100.0}).create({
    "move_type": "in_invoice", "partner_id": msc.id, "ref": f"{TAG} MSC-2 OCU", "invoice_date": date(2026, 11, 27),
    "invoice_line_ids": [Command.create({"product_id": ocu.id, "quantity": 1, "price_unit": 120.0,
                                         "tax_ids": [Command.set(purchase_0.ids)]})]})
ocu_bill.action_post()

# 10. Test payments and bank reconciliation
for move, label in ((inv1, "cobro THC"), (inv2, "cobro resto"), (inv3, "cobro OCU"), (bill, "pago MSC-1"),
                    (ocu_bill, "pago MSC-2")):
    if move.amount_residual:
        pay_and_reconcile(move, label)
    check(f"10 {label}: paid and reconciled with the bank line", "paid", move.payment_state)

# 11. Profitability
file.invalidate_recordset()
invoiced = expected_sale - 75.0 + 160.0
actual_cost = expected_bill + 120.0
check("11 invoiced (sale - credit note + re-invoiced extra)", invoiced, file.amount_invoiced)
check("11 actual cost (posted bills)", actual_cost, file.amount_cost_actual)
print(f"      file {file.name}: forecast cost {file.amount_cost_forecast}, pending {file.amount_cost_pending}, "
      f"margin final {file.amount_margin_final}, collected {file.amount_collected}, paid {file.amount_paid}")
check("11 collected = customer invoices with taxes", round(inv1.amount_total + inv2.amount_total + inv3.amount_total
                                                           - refund.amount_total, 2), round(file.amount_collected, 2))

passed, failed = results.count(True), results.count(False)
print(f"RESULT {passed} passed, {failed} failed | run {TAG} | order {order.name} | file {file.name} | "
      f"invoices {inv1.name}, {inv2.name}, {inv3.name} | credit note {refund.name} | bills {bill.name}, {ocu_bill.name}")
env.cr.commit()
if failed:
    raise SystemExit(1)
