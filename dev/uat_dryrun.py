"""Local copy only (boss_test, isolated): dry run of the cases of docs/pruebas-angel.md on the [DEMO] data, to check the
expected results of the sheet. Everything happens in ONE transaction that is rolled back at the end: nothing stays,
nothing is sent. Never on boss20."""
from odoo import Command
from odoo.exceptions import UserError, ValidationError

assert env.cr.dbname == "boss_test", env.cr.dbname  # noqa: F821
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES", tracking_disable=True))  # noqa: F821
IMD = env["ir.model.data"]


def xid(name):
    imd = IMD.search([("module", "=", "boss_trial"), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id).exists() if imd else None


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


def expect_error(label, fn):
    try:
        with env.cr.savepoint():
            fn()
        print(f"{label}: NO ERROR")
    except (UserError, ValidationError) as exc:
        print(f"{label}: ERROR «{' '.join(str(exc).split())[:300]}»")


def nif(seed):
    """A fictitious CIF with a valid check digit (the Spanish localization checks the format)."""
    from stdnum.es import cif  # noqa: PLC0415
    return "ES" + next(c for n in range(seed, seed + 1000) for d in "0123456789"
                       if cif.is_valid(c := f"B{n:07d}{d}"))


def taxes(order):
    return [(l.product_id.default_code, l.boss_vat_class, l.boss_vat_status, l.tax_ids.mapped("name"))
            for l in order.order_line if not l.display_type]


def figures(file):
    return {k: file[k] for k in ("amount_sale", "amount_invoiced", "amount_to_invoice", "amount_cost_actual",
                                 "amount_cost_pending", "amount_cost_forecast", "amount_margin_accepted",
                                 "amount_margin_forecast", "amount_margin_final", "amount_paid",
                                 "amount_draft_invoices", "amount_draft_bills")}


customer_es, customer_eu = xid("customer"), xid("customer_eu")
q_es, q_msc = xid("demo_q_es"), xid("demo_q_msc")
msc_file, wfs_file = xid("demo_file_msc"), xid("demo_file_wfs")
print("RECORDS", "ES quote", q_es.name, q_es.state, "| MSC quote", q_msc.name, "| MSC file", msc_file.name,
      "| WFS file", wfs_file.name, wfs_file.sale_order_ids.mapped("name"), "| split",
      xid("demo_file_split_a").name, xid("demo_file_split_b").name, "| own", xid("demo_file_own").name)
print("CUSTOMERS", customer_es.name, customer_es.country_id.code, customer_es.state_id.code, "vat", customer_es.vat,
      "|", customer_eu.name, customer_eu.vat)

# C1 VAT per case
print("C1 ES", q_es.name, taxes(q_es))
print("C1 EU", q_msc.name, taxes(q_msc))
es = env.ref("base.es")
for label, vals in (("CAN", {"country_id": es.id, "state_id": env.ref("base.state_es_gc").id, "vat": nif(7600000)}),
                    ("CEUTA", {"country_id": es.id, "state_id": env["res.country.state"].search(
                        [("country_id", "=", es.id), ("code", "=", "CE")], limit=1).id, "vat": nif(5100000)}),
                    ("TER", {"country_id": env.ref("base.ch").id, "vat": False})):
    partner = env["res.partner"].create(dict(vals, name=f"[DEMO] Cliente {label}", is_company=True, boss_demo=True,
                                             street="Calle Ejemplo 1 [DEMO]", city="Ejemplo", zip="00000"))
    copy = q_es.copy()
    copy.partner_id = partner
    print("C1", label, copy.name, taxes(copy))
cau = q_es.copy()
env["boss.add.services"].create({"order_id": cau.id, "product_ids": [Command.set(product("CAU").ids)]}).action_add()
print("C1 CAU for ES", cau.name, [t for t in taxes(cau) if t[0] == "CAU"])
expect_error("C1 confirm quote with CAU (VAT pending)", cau.action_confirm)

# C2 Spanish customer without NIF: invoice cannot be posted; with a NIF it can
q_es2 = q_es.copy()
q_es2.action_confirm()
es_file = q_es2.boss_expediente_id
wiz = env["boss.invoice.services"].create({"expediente_id": es_file.id,
                                            "allocation_ids": [Command.set(es_file.allocation_ids.ids)]})
es_inv = env["account.move"].browse(wiz.action_create()["res_id"])
print("C2 invoice", es_file.name, [(l.product_id.default_code, l.quantity, l.tax_ids.mapped("name"))
                                   for l in es_inv.invoice_line_ids])
expect_error("C2 post without NIF", es_inv.action_post)
customer_es.vat = nif(1234567)
expect_error("C2 post with NIF", es_inv.action_post)
print("C2 state", es_inv.state, es_inv.name)

# C3 Supplier bill by performed quantity (P32)
po = msc_file.purchase_order_ids.filtered(lambda p: p.state in ("draft", "sent"))[:1]
print("C3 PO", po.name, po.partner_id.name, [(l.product_id.default_code, l.product_qty, l.qty_received,
                                               l.product_id.purchase_method) for l in po.order_line])
po.button_confirm()
expect_error("C3 bill before performed", po.action_create_invoice)
thc_needs = msc_file.cost_ids.filtered(lambda n: n.product_id.default_code == "THC")
thc_needs.action_mark_performed()
print("C3 received", [(l.product_id.default_code, l.qty_received, l.qty_to_invoice) for l in po.order_line])
bill = env["account.move"].browse(po.action_create_invoice()["res_id"])
bill.invoice_date = bill.invoice_date or bill.date or __import__("datetime").date(2026, 11, 10)
bill.ref = "[DEMO] MSC-0001"
print("C3 bill lines", [(l.product_id.default_code, l.quantity, l.price_unit, l.tax_ids.mapped("name"),
                         l.account_id.code) for l in bill.invoice_line_ids])
expect_error("C3 post bill without tax", bill.action_post)
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                                         ("company_id", "=", env.company.id)], limit=1)
bill.invoice_line_ids.tax_ids = purchase_0
print("C3 purchase tax used for the dry run", purchase_0.name)
bill.invoice_line_ids.filtered(lambda l: not l.quantity).unlink()  # workaround: zero lines would block the payment
print("C3 bill without zero lines", [(l.product_id.default_code, l.quantity) for l in bill.invoice_line_ids])
print("C3 bills of the order", [(m.id, m.state, [(l.product_id.default_code, l.quantity) for l in m.invoice_line_ids])
                                for m in po.invoice_ids])

# C4 Payment of the supplier bill waits for the customer invoice (P30)
print("C4 warning", bill.boss_bill_warning)
expect_error("C4 post bill (customer invoice still draft)", bill.action_post)
print("C4 bill state", bill.state, bill.name)
expect_error("C4 pay bill before customer invoice", bill.action_register_payment)

# C5 Customer invoice of selected services (milestone) and then the payment
thc_inv = msc_file.invoice_ids.filtered(lambda m: m.state == "draft")
print("C5 draft invoice", [(l.product_id.default_code, l.quantity, l.tax_ids.mapped("name"), l.account_id.code)
                           for l in thc_inv.invoice_line_ids], thc_inv.amount_untaxed)
expect_error("C5 post customer invoice", thc_inv.action_post)
print("C5 invoice", thc_inv.name, thc_inv.state)
expect_error("C5 pay bill after customer invoice (zero lines removed)", bill.action_register_payment)
bill2 = env["account.move"].browse(po.action_create_invoice()["res_id"])
print("C5 second bill", [(l.product_id.default_code, l.quantity) for l in bill2.invoice_line_ids])
bill2.invoice_line_ids.filtered(lambda l: not l.quantity).unlink()
print("C5 second bill without zero lines", [(l.product_id.default_code, l.quantity) for l in bill2.invoice_line_ids],
      "| warning", bill2.boss_bill_warning)

# C6 Partial invoice (part of a quantity) and credit note
han = wfs_file.allocation_ids.filtered(lambda a: a.product_id.default_code == "HAN")
print("C6 HAN before", han.quantity, han.invoiced_quantity, han.to_invoice_quantity)
wiz = env["boss.invoice.services"].create({"expediente_id": wfs_file.id, "allocation_ids": [Command.set(han.ids)]})
part = env["account.move"].browse(wiz.action_create()["res_id"])
part.invoice_line_ids.filtered(lambda l: l.product_id.default_code == "HAN").quantity = 300
part.action_post()
han.invalidate_recordset()
print("C6 HAN after 300 kg", part.name, han.invoiced_quantity, han.to_invoice_quantity, "| file",
      figures(wfs_file)["amount_invoiced"], figures(wfs_file)["amount_to_invoice"])
refund = thc_inv._reverse_moves([{"ref": "[DEMO] Abono THC"}])
refund.action_post()
print("C6 credit note", refund.name, refund.amount_untaxed, "| MSC file invoiced", msc_file.amount_invoiced)

# C7 Amounts paid on behalf: bill without purchase order, account 419000
ara = msc_file.cost_ids.filtered(lambda n: n.product_id.default_code == "ARA")
print("C7 need", ara.state, ara.without_order, ara.partner_id.name, ara.expected_unit_cost)
def ara_bill_create():
    return env["account.move"].with_context(boss_default_analytic={str(msc_file.analytic_account_id.id): 100.0}).create({
    "move_type": "in_invoice", "partner_id": ara.partner_id.id, "ref": "[DEMO] DUA 26ES00000000001",
    "invoice_date": __import__("datetime").date(2026, 11, 3),
    "invoice_line_ids": [Command.create({"product_id": product("ARA").id, "quantity": 1, "price_unit": 350.0})]})


expect_error("C7 create ARA bill on 419000", ara_bill_create)
ara_bill = env["account.move"]
print("C7 bill line", [(l.product_id.default_code, l.account_id.code, l.tax_ids.mapped("name"),
                        l.analytic_distribution) for l in ara_bill.invoice_line_ids])
ara.invalidate_recordset()
print("C7 need after bill", ara.state)
alloc = msc_file.allocation_ids.filtered(lambda a: a.product_id.default_code == "ARA")
wiz = env["boss.invoice.services"].create({"expediente_id": msc_file.id, "allocation_ids": [Command.set(alloc.ids)]})
expect_error("C7 customer invoice of ARA on 419000", wiz.action_create)

# C8 Profitability
print("C8 MSC file", msc_file.name, figures(msc_file))
print("C8 complete?", msc_file.completeness if "completeness" in msc_file._fields else "n/a")
env.cr.rollback()
print("ROLLED BACK")
