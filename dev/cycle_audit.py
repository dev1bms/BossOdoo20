"""Read-only audit of the sale -> invoice and purchase -> vendor bill cycle on boss20 / the local copy (odoo shell).
Nothing is created, confirmed, posted or written (rollback at the end)."""
assert env.cr.dbname in ("boss20", "boss_test", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, lang="es_ES"))  # noqa: F821
M = env["ir.module.module"]
mods = M.search([("name", "in", ["sale", "sale_management", "sale_margin", "sale_crm", "purchase", "sale_purchase",
                                  "account", "account_accountant", "l10n_es", "analytic", "sale_project",
                                  "purchase_stock", "stock"])])
print("MODULES", sorted((m.name, m.state) for m in mods))
print("MODELS purchase.order:", "purchase.order" in env, "| purchase_line on account.move.line:",
      "purchase_line_id" in env["account.move.line"]._fields)
P = env["product.template"].search([("boss_pricing_mode", "!=", False)])
by_mode = {}
for p in P:
    by_mode.setdefault(p.boss_pricing_mode, []).append(p)
for mode, ps in by_mode.items():
    s = ps[0]
    print("MODE", mode, len(ps), "| e.g.", s.default_code, "| type", s.type, "| sale_ok", s.sale_ok, "| purchase_ok",
          s.purchase_ok, "| invoice_policy", s.invoice_policy, "| service_to_purchase",
          getattr(s, "service_to_purchase", "n/a"), "| sellers", len(s.seller_ids), "| standard_price", s.standard_price,
          "| taxes", s.taxes_id.mapped("name"), "| supplier_taxes", s.supplier_taxes_id.mapped("name"))
print("PURCHASE_OK services", len(P.filtered("purchase_ok")), "of", len(P), "| with supplierinfo",
      len(P.filtered("seller_ids")))
SO = env["sale.order"]
print("ORDERS by state", {s: SO.search_count([("state", "=", s)]) for s in ("draft", "sent", "sale", "cancel")})
print("INVOICES customer", env["account.move"].search_count([("move_type", "in", ("out_invoice", "out_refund"))]),
      "| vendor bills", env["account.move"].search_count([("move_type", "in", ("in_invoice", "in_refund"))]),
      "| purchase orders", env["purchase.order"].search_count([]) if "purchase.order" in env else "no model")
for o in SO.search([("state", "=", "sale")]):
    print("CONFIRMED", o.id, o.name, o.partner_id.name, "| invoice_status", o.invoice_status, "| invoices",
          o.invoice_ids.mapped("name"), "| frozen", o.boss_pricing_frozen, "| snapshots", len(o.boss_snapshot_ids),
          "| purchase", o.purchase_order_count if "purchase_order_count" in o._fields else "n/a")
    for l in o.order_line:
        print("   ", l.product_id.default_code, l.product_id.boss_pricing_mode, "| qty", l.product_uom_qty,
              l.product_uom_id.name, "| supplier", l.boss_supplier_id.name or "-", "| cost", l.boss_cost_status,
              l.boss_cost_amount, (l.boss_cost_currency_id.name or ""), "| unit cost", l.purchase_price,
              "| sale", l.price_unit, "| margin", round(l.margin, 2), "| to invoice", l.qty_to_invoice,
              "| invoiced", l.qty_invoiced, "| taxes", l.tax_ids.mapped("name"), "| vat", l.boss_vat_class,
              l.boss_vat_status, "| tariff line", l.boss_tariff_line_id.id or "-",
              "| purchase lines", len(l.purchase_line_ids) if "purchase_line_ids" in l._fields else "n/a")
own = env["sale.order.line"].search([("product_id.boss_pricing_mode", "=", "own")])
print("OWN-FEE LINES", [(l.order_id.name, l.order_id.state, l.product_id.default_code, l.boss_cost_status,
                         l.purchase_price, l.price_unit, l.boss_sale_status) for l in own])
J = env["account.journal"]
print("JOURNALS", [(j.code, j.type) for j in J.search([("type", "in", ("sale", "purchase"))])])
print("FISCAL POSITIONS", env["account.fiscal.position"].search_count([]),
      "| VAT table rows", [(r.vat_class, r.customer_zone, r.service_kind, r.tax_id.name) for r in env["boss.vat.tax"].search([])])
print("PRODUCT INCOME/EXPENSE ACCOUNTS", P[:1].property_account_income_id.code, P[:1].property_account_expense_id.code,
      "| categ", P[:1].categ_id.name, P[:1].categ_id.property_account_income_categ_id.code,
      P[:1].categ_id.property_account_expense_categ_id.code)
print("ANALYTIC plans", env["account.analytic.plan"].search_count([]) if "account.analytic.plan" in env else "n/a",
      "| accounts", env["account.analytic.account"].search_count([]) if "account.analytic.account" in env else "n/a")
env.cr.rollback()
