"""LOCAL copy only (boss_test): accept the [DEMO] EU-customer quotation for the guide screenshots, with the BOSS VAT
table set by dev/setup_vat_mapping.py (every VAT case of an EU customer is decided)."""
env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname == "boss_test", "local copy only"
imd = env["ir.model.data"].search([("module", "=", "boss_trial"), ("name", "=", "lead_eu")], limit=1)
order = env["sale.order"].search([("opportunity_id", "=", imd.res_id)], limit=1)
order.with_user(env.ref("base.user_admin")).action_confirm()
env.cr.commit()
print("ACCEPTED", order.id, order.name, order.state, order.boss_pricing_frozen, order.order_line.tax_ids.mapped("name"))
