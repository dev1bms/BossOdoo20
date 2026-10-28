"""Vendor bill lines created from a file's purchase before 20.0.1.14.0 did not carry the file: set it from the purchase
line (its service of the file, else the order's file). Idempotent: only lines without a file are touched."""


def migrate(cr, version):
    cr.execute("""
        UPDATE account_move_line aml
           SET boss_expediente_id = COALESCE(cost.expediente_id, po.boss_expediente_id)
          FROM purchase_order_line pol
          JOIN purchase_order po ON po.id = pol.order_id
          LEFT JOIN boss_expediente_cost cost ON cost.id = pol.boss_cost_id
         WHERE aml.purchase_line_id = pol.id
           AND aml.boss_expediente_id IS NULL
           AND COALESCE(cost.expediente_id, po.boss_expediente_id) IS NOT NULL
    """)
