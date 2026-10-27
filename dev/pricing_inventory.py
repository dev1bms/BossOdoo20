"""Read-only inventory of what prices a quotation on boss20: supplier tariffs (all, archived too) with their use by
quotations and files, customer pricelists with their rules and use, quotation templates, services and carriers'
handlers. Prints no amount (real prices stay out of Git). Rollback at the end.
    dev/server_shell.sh pricing_inventory.py"""
from collections import Counter

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, lang="es_ES", active_test=False))  # noqa: F821
SOL, Cost = env["sale.order.line"], env["boss.expediente.cost"]

print("== SERVICES", env["product.product"].search_count([("boss_pricing_mode", "!=", False)]), "with pricing mode")
print("== TARIFFS")
for t in env["boss.tariff"].search([], order="is_demo, partner_id, name"):
    lines = t.line_ids
    used = SOL.search([("boss_tariff_line_id", "in", lines.ids)])
    used_files = Cost.search_count([("tariff_line_id", "in", lines.ids)])
    print(f"T{t.id} | {'DEMO' if t.is_demo else 'real'} | {'active' if t.active else 'ARCHIVED'} | {t.state} | "
          f"{t.partner_id.name} | {t.name} | {t.valid_from} -> {t.valid_to or 'open'} | {t.currency_id.name} | "
          f"doc={'yes' if t.document else 'NO'} {t.document_name or ''} | ref={t.document_reference or ''} | "
          f"scope={t.scope_summary} | lines={len(lines)} "
          f"[{', '.join(sorted(set(lines.product_id.mapped('default_code'))))}] | "
          f"used by {len(used)} quotation lines ({', '.join(sorted(set(used.order_id.mapped('name'))))}) and "
          f"{used_files} file services")
print("== PRICELISTS")
for p in env["product.pricelist"].search([]):
    orders = env["sale.order"].search([("pricelist_id", "=", p.id)])
    partners = len(env["res.partner"].search([("customer_rank", ">", 0)]).filtered(lambda r: r.property_product_pricelist == p))
    print(f"PL{p.id} | {'active' if p.active else 'ARCHIVED'} | {p.name} | {p.currency_id.name} | "
          f"{len(p.item_ids)} rules | default of {partners} partners | {len(orders)} orders "
          f"({Counter(orders.mapped('state'))})")
    for i in p.item_ids:
        print(f"   rule {i.id} | {i.applied_on} | {i.product_tmpl_id.default_code or i.categ_id.name or 'all'} | "
              f"compute={i.compute_price} base={i.base} | {i.date_start or ''} -> {i.date_end or ''}")
print("== TEMPLATES")
for t in env["sale.order.template"].search([]):
    n = env["sale.order"].search_count([("sale_order_template_id", "=", t.id)])
    print(f"QT{t.id} | {'active' if t.active else 'ARCHIVED'} | {t.name} | "
          f"{[l.product_id.default_code for l in t.sale_order_template_line_ids]} | used by {n} orders | "
          f"note={'yes' if t.note else 'no'}")
print("== ORDERS")
for o in env["sale.order"].search([], order="id"):
    print(f"{o.name} | {o.state} | {o.partner_id.name} | {o.origin or ''} | {o.pricelist_id.name} | "
          f"template={o.sale_order_template_id.name or ''} | files={','.join(o.boss_expediente_ids.mapped('name'))}")
print("== PARTNERS marked demo", env["res.partner"].search_count([("boss_is_demo", "=", True)])
      if "boss_is_demo" in env["res.partner"]._fields else "(no demo flag on partners)")
env.cr.rollback()
