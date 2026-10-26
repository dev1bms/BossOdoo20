"""Read-only: [DEMO] records named in the accounting test sheet (docs/pruebas-angel.md), on boss20 or the local copy.
Rollback at the end."""
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, lang="es_ES"))  # noqa: F821
print("DB", env.cr.dbname, "| company", env.company.name, env.company.boss_bill_before_invoice,  # noqa: F821
      env.company.boss_fx_policy)
for p in env["res.partner"].search([("boss_demo", "=", True)]):  # noqa: F821
    print("CUSTOMER", p.id, p.name, "|", p.country_id.code, p.state_id.code or "", "| vat", bool(p.vat),
          "| street", bool(p.street))
for o in env["sale.order"].search([], order="name"):  # noqa: F821
    print("ORDER", o.name, o.state, "|", o.partner_id.name, "| files", o.boss_expediente_ids.mapped("name"),
          "| untaxed", o.amount_untaxed, "| tax", o.amount_tax, "| currency", o.currency_id.name)
    for l in o.order_line.filtered(lambda l: not l.display_type):
        print("    ", l.product_id.default_code, l.product_uom_qty, "| vat", l.boss_vat_class, l.boss_vat_status,
              l.tax_ids.mapped("name"), "| exec", l.boss_execution, "| inv", l.qty_invoiced, l.invoice_status)
for f in env["boss.expediente"].search([], order="name"):  # noqa: F821
    print("FILE", f.name, "|", f.partner_id.name, "| orders", f.sale_order_ids.mapped("name"),
          "| POs", f.purchase_order_ids.mapped(lambda p: f"{p.name}:{p.state}:{p.partner_id.name}"),
          "| invoices", f.invoice_ids.mapped(lambda m: f"{m.name or m.id}:{m.state}"))
    for c in f.cost_ids:
        print("    need", c.product_id.default_code, c.partner_id.name, c.state, "| po", c.purchase_line_ids.order_id.mapped("name"),
              "| without_order", c.without_order)
for m in env["account.move"].search([]):  # noqa: F821
    print("MOVE", m.id, m.name, m.move_type, m.state, m.partner_id.name, m.amount_untaxed,
          [(l.product_id.default_code, l.quantity, l.tax_ids.mapped("name"), l.account_id.code)
           for l in m.invoice_line_ids])
for po in env["purchase.order"].search([]):  # noqa: F821
    print("PO", po.name, po.state, po.partner_id.name, po.currency_id.name,
          [(l.product_id.default_code, l.product_qty, l.qty_received, l.product_id.purchase_method) for l in po.order_line])
env.cr.rollback()  # noqa: F821
FIGS = ("amount_sale", "amount_sale_accepted", "amount_sale_added", "amount_cost_accepted", "amount_committed",
        "amount_cost_actual", "amount_cost_pending", "amount_cost_forecast", "amount_margin_accepted",
        "amount_margin_forecast", "amount_margin_final", "amount_invoiced", "amount_to_invoice", "amount_paid",
        "amount_draft_invoices", "amount_draft_rfqs", "amount_draft_bills")
for f in env["boss.expediente"].search([], order="name"):  # noqa: F821
    print("FIGS", f.name, {k: f[k] for k in FIGS if k in f._fields})
for code in ("ARA", "IVA", "PLA", "DUM", "THC"):
    t = env["product.template"].search([("default_code", "=", code)], limit=1)  # noqa: F821
    print("ACCOUNTS", code, t.property_account_income_id.code, t.property_account_expense_id.code,
          t.categ_id.property_account_income_categ_id.code, t.categ_id.property_account_expense_categ_id.code,
          t.purchase_method, t.boss_paid_on_behalf)
env.cr.rollback()  # noqa: F821
