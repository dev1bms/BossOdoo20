"""Read-only: every price of the tariffs from real documents (not demo), as the tariff workspace shows it (price,
calculation, scope, example), to check each one against its supplier document. Prints amounts: run it only into
.research/ (outside Git). Rollback at the end.
    dev/server_shell.sh tariff_lines_dump.py > .research/tariff_lines_<date>.txt"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, lang="es_ES"))  # noqa: F821
for t in env["boss.tariff"].search([("is_demo", "=", False)], order="partner_id, name"):
    print(f"\nT{t.id} {t.name} | {t.state} | {t.valid_from} -> {t.valid_to or 'open'} | {t.currency_id.name} | "
          f"carrier={t.carrier_id.name or '-'} | customer={t.customer_id.name or '-'} | {t.scope_summary}")
    print(f"   doc: {t.document_name} | {t.document_reference} | note: {t.note or ''}")
    for l in t.line_ids:
        brackets = "; ".join(f"<= {b.up_to or 'inf'}: fixed {b.fixed_amount} unit {b.unit_price}" for b in l.bracket_ids)
        print(f"   L{l.id} {l.product_id.default_code} | uom={l.uom_id.name} | {l.method}/{l.basis} | "
              f"size={l.container_size or '-'} types={','.join(l.container_type_ids.mapped('code')) or '-'} | "
              f"unit_price={l.unit_price} unit_size={l.unit_size} round_up={l.round_up} | min={l.min_amount} "
              f"max={l.max_amount} | free_days={l.free_days} free_hours={l.free_hours} period={l.period_unit} "
              f"tier={l.tier_mode} | rate={l.rate} base={l.percent_base} | vol={l.volumetric_factor} | "
              f"brackets=[{brackets}] | p.{l.document_page or '-'} | {l.note or ''}")
        print(f"      price: {l.price_display} | calc: {l.calc_display}")
env.cr.rollback()
