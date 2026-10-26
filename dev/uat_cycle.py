"""boss20_uat only (persistent UAT copy, isolated): the cases of docs/pruebas-angel.md run on the [DEMO] data and KEPT
(committed) so Belal can open every record in the UI. Idempotent: a second run only prints what exists.
    BOSS_DB=boss20_uat dev/server_shell.sh uat_cycle.py
Expected figures are computed from the [DEMO] tariffs (THC 240 €/cntr, DEM 90 €, HAN 0,20 €/kg...) before each step.
Never on boss20 (invoice sequences, posted entries)."""
from datetime import date

from odoo import Command
from odoo.exceptions import UserError, ValidationError

assert env.cr.dbname == "boss20_uat", env.cr.dbname  # noqa: F821
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES", tracking_disable=True))  # noqa: F821
IMD = env["ir.model.data"]
TAG = "[UAT] ciclo 26/10/2026"


def xid(name):
    imd = IMD.search([("module", "=", "boss_trial"), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id).exists() if imd else None


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


def expect(label, fn, error=True):
    """error=True: the step must be refused (UserError/ValidationError); error=False: it must pass."""
    try:
        with env.cr.savepoint():
            res = fn()
    except (UserError, ValidationError) as exc:
        msg = " ".join(str(exc).split())[:260]
        print(f"{'OK ' if error else 'FAIL'} {label}: ERROR «{msg}»")
        return None
    print(f"{'FAIL' if error else 'OK '} {label}: no error")
    return res


def nif(seed):
    from stdnum.es import cif  # noqa: PLC0415
    return "ES" + next(c for n in range(seed, seed + 1000) for d in "0123456789" if cif.is_valid(c := f"B{n:07d}{d}"))


def taxes(order):
    return [(l.product_id.default_code, l.boss_vat_class, l.boss_vat_status, l.tax_ids.mapped("name"))
            for l in order.order_line if not l.display_type]


def figures(file):
    return {k: round(file[k], 2) for k in (
        "amount_sale", "amount_invoiced", "amount_to_invoice", "amount_cost_actual", "amount_cost_pending",
        "amount_cost_forecast", "amount_margin_accepted", "amount_margin_forecast", "amount_margin_final",
        "amount_collected", "amount_paid", "amount_draft_invoices", "amount_draft_bills")}


def pay(move, journal):
    wiz = env["account.payment.register"].with_context(active_model="account.move", active_ids=move.ids).create(
        {"journal_id": journal.id, "payment_date": date(2026, 11, 20)})
    return wiz.action_create_payments()


if env["sale.order"].search_count([("client_order_ref", "=", TAG)]):
    print("ALREADY RUN:", [(o.name, o.state, o.boss_expediente_id.name) for o in
                           env["sale.order"].search([("client_order_ref", "=", TAG)])])
    raise SystemExit(0)

customer_es, customer_eu = xid("customer"), xid("customer_eu")
q_es, q_msc = xid("demo_q_es"), xid("demo_q_msc")
msc_file, wfs_file = xid("demo_file_msc"), xid("demo_file_wfs")
bank = env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", env.company.id)], limit=1)
print("RECORDS", q_es.name, q_es.state, "|", q_msc.name, "|", msc_file.name, "|", wfs_file.name, "| bank", bank.name)

# C1 VAT per case: ES customer 21 %, EU customer 0 % intra-EU, Canarias / Ceuta not subject, third country exempt
print("C1 ES", q_es.name, taxes(q_es))
print("C1 EU", q_msc.name, taxes(q_msc))
es = env.ref("base.es")
for label, vals in (("Canarias", {"country_id": es.id, "state_id": env.ref("base.state_es_gc").id, "vat": nif(7600000)}),
                    ("Ceuta", {"country_id": es.id, "state_id": env["res.country.state"].search(
                        [("country_id", "=", es.id), ("code", "=", "CE")], limit=1).id, "vat": nif(5100000)}),
                    ("Suiza", {"country_id": env.ref("base.ch").id, "vat": False})):
    partner = env["res.partner"].search([("name", "=", f"[DEMO] Cliente {label}")], limit=1) or env["res.partner"].create(
        dict(vals, name=f"[DEMO] Cliente {label}", is_company=True, boss_demo=True, street="Calle Ejemplo 1 [DEMO]",
             city="Ejemplo", zip="00000"))
    copy = q_es.copy({"client_order_ref": TAG, "origin": f"{TAG} C1 {label}"})
    copy.partner_id = partner
    print("C1", label, copy.name, taxes(copy))
cau = q_es.copy({"client_order_ref": TAG, "origin": f"{TAG} C1 CAU"})
env["boss.add.services"].create({"order_id": cau.id, "product_ids": [Command.set(product("CAU").ids)]}).action_add()
print("C1 CAU for ES", cau.name, [t for t in taxes(cau) if t[0] == "CAU"])
expect("C1 confirm quote with CAU (VAT pending)", cau.action_confirm)

# C2 Spanish customer without NIF: the invoice cannot be posted; with a NIF it can
customer_es.vat = False
q_es2 = q_es.copy({"client_order_ref": TAG, "origin": f"{TAG} C2"})
q_es2.action_confirm()
es_file = q_es2.boss_expediente_id
wiz = env["boss.invoice.services"].create({"expediente_id": es_file.id,
                                            "allocation_ids": [Command.set(es_file.allocation_ids.ids)]})
es_inv = env["account.move"].browse(wiz.action_create()["res_id"])
print("C2 invoice", es_file.name, [(l.product_id.default_code, l.quantity, l.tax_ids.mapped("name"))
                                   for l in es_inv.invoice_line_ids])
expect("C2 post without NIF", es_inv.action_post)
customer_es.vat = nif(1234567)
expect("C2 post with NIF", es_inv.action_post, error=False)
print("C2 state", es_inv.state, es_inv.name, es_inv.amount_untaxed, es_inv.amount_tax)

# C3 Supplier bill by performed quantity (P32): 2 x THC 40' at 240 € = 480 €, DEM 90 € not performed -> bill 480 €
po = msc_file.purchase_order_ids.filtered(lambda p: p.state in ("draft", "sent"))[:1]
print("C3 PO", po.name, po.partner_id.name, [(l.product_id.default_code, l.product_qty, l.price_unit,
                                               l.product_id.purchase_method) for l in po.order_line])
po.button_confirm()
expect("C3 bill before performed", po.action_create_invoice)
thc_needs = msc_file.cost_ids.filtered(lambda n: n.product_id.default_code == "THC")
thc_needs.action_mark_performed()
print("C3 received", [(l.product_id.default_code, l.qty_received, l.qty_to_invoice) for l in po.order_line])
bill = env["account.move"].browse(po.action_create_invoice()["res_id"])
bill.invoice_date = date(2026, 11, 10)
bill.ref = "[DEMO] MSC-0001"
print("C3 bill lines", [(l.product_id.default_code, l.quantity, l.price_unit, l.tax_ids.mapped("name"),
                         l.account_id.code) for l in bill.invoice_line_ids], "untaxed", bill.amount_untaxed)
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                                         ("company_id", "=", env.company.id)], limit=1)
bill.invoice_line_ids.tax_ids = purchase_0  # the supplier's tax is typed from its document; 0 % here
print("C3 zero-quantity lines kept on the bill (D-1):",
      [(l.product_id.default_code, l.quantity) for l in bill.invoice_line_ids if not l.quantity])

# C4 The supplier bill is posted, but its payment waits for the customer invoice (P30)
print("C4 warning", bill.boss_bill_warning)
expect("C4 post bill (customer invoice still draft)", bill.action_post, error=False)
print("C4 bill", bill.name, bill.state)
expect("C4 pay bill before the customer invoice", lambda: pay(bill, bank))

# C5 Customer invoice of the selected services (milestone), then the bill can be paid; zero lines do not block (D-1)
thc_inv = msc_file.invoice_ids.filtered(lambda m: m.state == "draft")[:1]
print("C5 draft invoice", [(l.product_id.default_code, l.quantity, l.price_unit, l.tax_ids.mapped("name"),
                            l.account_id.code) for l in thc_inv.invoice_line_ids], thc_inv.amount_untaxed)
thc_inv.invoice_date = date(2026, 11, 12)
expect("C5 post customer invoice", thc_inv.action_post, error=False)
print("C5 invoice", thc_inv.name, thc_inv.state, thc_inv.amount_total)
expect("C5 pay the bill after the customer invoice (zero lines kept)", lambda: pay(bill, bank), error=False)
print("C5 bill payment state", bill.payment_state)
expect("C5 collect the customer invoice", lambda: pay(thc_inv, bank), error=False)
print("C5 invoice payment state", thc_inv.payment_state)

# C6 Partial invoice (300 of 500 kg of HAN) and a credit note of the THC invoice
han = wfs_file.allocation_ids.filtered(lambda a: a.product_id.default_code == "HAN")
print("C6 HAN before", han.quantity, han.invoiced_quantity, han.to_invoice_quantity)
wiz = env["boss.invoice.services"].create({"expediente_id": wfs_file.id, "allocation_ids": [Command.set(han.ids)]})
part = env["account.move"].browse(wiz.action_create()["res_id"])
part.invoice_line_ids.filtered(lambda l: l.product_id.default_code == "HAN").quantity = 300
part.invoice_date = date(2026, 11, 12)
part.action_post()
han.invalidate_recordset()
print("C6 HAN after 300 kg", part.name, han.invoiced_quantity, han.to_invoice_quantity, "| file invoiced",
      figures(wfs_file)["amount_invoiced"], "to invoice", figures(wfs_file)["amount_to_invoice"])
refund = thc_inv._reverse_moves([{"ref": "[DEMO] Abono THC", "date": date(2026, 11, 13)}])
refund.action_post()
msc_file.invalidate_recordset()
print("C6 credit note", refund.name, refund.amount_untaxed, "| MSC file invoiced", msc_file.amount_invoiced)

# C7 Amounts paid on behalf (ARA): bill without purchase order on 419004, customer line on 419002 (D-2 applied)
ara = msc_file.cost_ids.filtered(lambda n: n.product_id.default_code == "ARA")
print("C7 need", ara.state, ara.without_order, ara.partner_id.name, ara.expected_unit_cost)


def ara_bill_create():
    return env["account.move"].with_context(boss_default_analytic={str(msc_file.analytic_account_id.id): 100.0}).create({
        "move_type": "in_invoice", "partner_id": ara.partner_id.id, "ref": "[DEMO] DUA 26ES00000000001",
        "invoice_date": date(2026, 11, 3),
        "invoice_line_ids": [Command.create({"product_id": product("ARA").id, "quantity": 1, "price_unit": 350.0})]})


ara_bill = expect("C7 create the ARA bill (account of the service, D-2)", ara_bill_create, error=False)
if ara_bill:
    print("C7 bill line", [(l.product_id.default_code, l.account_id.code, l.tax_ids.mapped("name"),
                            l.analytic_distribution) for l in ara_bill.invoice_line_ids])
    ara_bill.invoice_line_ids.tax_ids = purchase_0
    expect("C7 post the ARA bill", ara_bill.action_post, error=False)
    ara.invalidate_recordset()
    print("C7 need after bill", ara.state)
    alloc = msc_file.allocation_ids.filtered(lambda a: a.product_id.default_code == "ARA")
    wiz = env["boss.invoice.services"].create({"expediente_id": msc_file.id, "allocation_ids": [Command.set(alloc.ids)]})
    ara_inv = expect("C7 customer invoice of the ARA", lambda: env["account.move"].browse(wiz.action_create()["res_id"]),
                     error=False)
    if ara_inv:
        print("C7 customer line", [(l.product_id.default_code, l.account_id.code, l.tax_ids.mapped("name"))
                                   for l in ara_inv.invoice_line_ids])

# C8 Profitability
msc_file.invalidate_recordset()
print("C8 MSC file", msc_file.name, figures(msc_file))
print("C8 to do:", " | ".join((msc_file.completeness or "").splitlines()))
print("C8 WFS file", wfs_file.name, figures(wfs_file))
env.cr.commit()
print("COMMITTED on boss20_uat")
