"""20.0.1.2.0: lines re-invoiced from an extra cost before the flag existed are services added after acceptance."""


def migrate(cr, version):
    cr.execute("""
        UPDATE sale_order_line SET boss_added_after_acceptance = TRUE
         WHERE id IN (SELECT rebill_line_id FROM boss_expediente_cost WHERE rebill_line_id IS NOT NULL)
    """)
