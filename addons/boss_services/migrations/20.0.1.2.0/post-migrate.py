"""Paid-on-behalf services (Odoo 17 concepts of type TAX: ARA, IVA, PLA, DUM); product records are noupdate."""


def migrate(cr, version):
    cr.execute("""
        UPDATE product_template SET boss_paid_on_behalf = TRUE
         WHERE id IN (SELECT res_id FROM ir_model_data
                       WHERE module = 'boss_services' AND name IN ('service_ara', 'service_pla', 'service_iva', 'service_dum'))
    """)
