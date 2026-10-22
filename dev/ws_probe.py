"""Read-only: the acceptance prices as saved (no commit)."""
for line in env["boss.tariff.line"].browse([57, 58, 59]).with_context(lang="es_ES"):
    t = line.tariff_id
    print(line.id, t.name, "|", t.state, line.validity_state, "|", line.product_id.default_code, line.uom_id.name,
          line.container_size, line.container_type_ids.mapped("code"), line.method, line.basis, line.unit_size,
          line.round_up, line.unit_price, line.volumetric_factor, line.free_hours, line.free_mode, line.tier_mode,
          line.min_amount, line.document_page, [(b.up_to, b.fixed_amount, b.unit_price) for b in line.bracket_ids])
    print("   ", line.price_display)
men = env["boss.tariff.line"].search([("tariff_id", "=", 26), ("product_id.default_code", "=", "MEN")])
print("MEN", men.unit_price, men.document_page, men.tariff_id.state, men.tariff_id.approved_by_id.name)
o = env["sale.order"].browse(14)
for l in o.order_line:
    print("S00014", l.product_id.default_code, l.boss_cost_status, l.boss_cost_amount, l.price_unit)
env.cr.rollback()
