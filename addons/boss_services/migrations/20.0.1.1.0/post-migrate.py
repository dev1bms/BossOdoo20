"""Air chargeable kg takes the AWB weight of the shipment (the unit records are noupdate)."""


def migrate(cr, version):
    cr.execute("""
        UPDATE uom_uom SET boss_quantity_source = 'awb_kg'
         WHERE id = (SELECT res_id FROM ir_model_data WHERE module = 'boss_services' AND name = 'uom_kg_air')
    """)
