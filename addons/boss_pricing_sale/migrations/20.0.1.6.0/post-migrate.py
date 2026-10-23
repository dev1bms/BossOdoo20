"""Who executes each existing line (ADR-005). Accepted lines keep stored values, so the new column is filled here
from the service, then the cost kind is computed from it."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute("""
        UPDATE sale_order_line l
           SET boss_execution = CASE WHEN t.boss_pricing_mode = 'own' THEN 'boss' ELSE 'supplier' END
          FROM product_product p JOIN product_template t ON t.id = p.product_tmpl_id
         WHERE p.id = l.product_id AND t.boss_pricing_mode IS NOT NULL AND l.display_type IS NULL
    """)
    env = api.Environment(cr, SUPERUSER_ID, {})
    lines = env["sale.order.line"].search([("boss_execution", "!=", False)])
    env.add_to_compute(lines._fields["boss_cost_kind"], lines)
    lines._recompute_recordset(["boss_cost_kind"])
