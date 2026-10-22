"""Isolate the demonstration data on boss20 / the local copy (odoo shell). Idempotent.

- Tariffs named «[DEMO] …» become demo tariffs (they then price demo customers only, never a real customer).
- Customers named «[DEMO] …» and the trial customers become demo customers.
- Open quotations (draft/sent, not frozen) are re-priced, like after a tariff approval. Accepted quotations keep
  their frozen prices and history.
Real tariffs ([MUESTRA] and others) and real customers are not touched.
"""
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, lang="es_ES"))  # noqa: F821
Tariff, Partner = env["boss.tariff"].with_context(active_test=False), env["res.partner"].with_context(active_test=False)
demo_tariffs = Tariff.search([("name", "=like", "[DEMO]%"), ("is_demo", "=", False)])
demo_tariffs._workflow_write({"is_demo": True})  # approved ones too: evidence unchanged, only their audience
customers = Partner.search([("name", "=like", "[DEMO]%"), ("boss_demo", "=", False), ("is_company", "=", True),
                            ("sale_order_ids", "!=", False)])  # customers only (demo suppliers stay as they are)
customers |= env["ir.model.data"].search([("module", "=", "boss_trial"), ("model", "=", "res.partner"),
                                           ("name", "in", ("customer", "customer_eu"))]).mapped(
    lambda d: Partner.browse(d.res_id)).filtered(lambda p: not p.boss_demo)
customers.write({"boss_demo": True})
orders = env["sale.order"].search([("state", "in", ("draft", "sent")), ("boss_pricing_frozen", "=", False)])
before = {(l.id): (l.boss_cost_status, l.boss_cost_amount) for l in orders.order_line}
orders.action_boss_update_costs()
changed = [(l.order_id.name, l.product_id.default_code, before[l.id], (l.boss_cost_status, l.boss_cost_amount))
           for l in orders.order_line if before.get(l.id) != (l.boss_cost_status, l.boss_cost_amount)]
print("demo tariffs:", demo_tariffs.mapped("name"))
print("demo customers:", customers.mapped("name"))
print("open quotations re-priced:", orders.mapped("name"), "changed lines:", changed)
real = env["sale.order.line"].search([("order_id.partner_id.commercial_partner_id.boss_demo", "=", False),
                                      ("boss_tariff_line_id.tariff_id.is_demo", "=", True),
                                      ("order_id.boss_pricing_frozen", "=", False)])
print("real-customer lines still priced by a demo tariff:", real.mapped(lambda l: (l.order_id.name, l.product_id.default_code)))
env.cr.commit()
