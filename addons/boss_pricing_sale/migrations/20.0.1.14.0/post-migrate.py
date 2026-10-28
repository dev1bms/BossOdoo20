"""The default «expected cost + %» rule rounds the sale price to the cent (two decimals, Ángel 27/10/2026; seen in
Chrome on 28/10: 1,984.272). Accepted quotations are frozen and keep their prices."""


def migrate(cr, version):
    cr.execute("""UPDATE product_pricelist_item SET price_round = 0.01
                   WHERE base = 'boss_line_cost' AND applied_on = '3_global' AND compute_price = 'markup'
                     AND COALESCE(price_round, 0) = 0""")
