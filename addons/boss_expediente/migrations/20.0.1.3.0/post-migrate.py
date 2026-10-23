"""20.0.1.3.0 (decisions approved 23/10/2026): BOSS services billed on performed quantities (P32)."""


def migrate(cr, version):
    cr.execute("UPDATE product_template SET purchase_method = 'receive' WHERE boss_pricing_mode IS NOT NULL")
