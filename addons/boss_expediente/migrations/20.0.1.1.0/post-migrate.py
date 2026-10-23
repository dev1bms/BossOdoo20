"""20.0.1.1.0: days of time-based services and the date of their expected cost on services to buy; accepted lines of
existing files become their allocation (each line wholly in the file of its order)."""


def migrate(cr, version):
    cr.execute("""
        UPDATE boss_expediente_cost c
           SET days = l.boss_days
          FROM sale_order_line l, product_product p, product_template t
         WHERE l.id = c.sale_line_id AND p.id = c.product_id AND t.id = p.product_tmpl_id
           AND t.boss_cost_method = 'time'
    """)
    cr.execute("UPDATE boss_expediente_cost SET expected_date = create_date WHERE expected_date IS NULL")
    cr.execute("""
        INSERT INTO boss_expediente_allocation (expediente_id, sale_line_id, order_id, company_id, quantity,
                                                create_uid, write_uid, create_date, write_date)
        SELECT o.boss_expediente_id, l.id, o.id, e.company_id, l.product_uom_qty, 1, 1, now(), now()
          FROM sale_order_line l
          JOIN sale_order o ON o.id = l.order_id
          JOIN boss_expediente e ON e.id = o.boss_expediente_id
         WHERE o.state = 'sale' AND l.display_type IS NULL AND NOT coalesce(l.is_downpayment, false)
           AND l.product_uom_qty > 0
           AND NOT EXISTS (SELECT 1 FROM boss_expediente_allocation a
                            WHERE a.expediente_id = o.boss_expediente_id AND a.sale_line_id = l.id)
    """)
