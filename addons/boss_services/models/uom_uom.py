from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    # ADR-002: a charge basis is an independent unit; its quantity comes from the shipment
    # inputs named here, never from a conversion between units.
    boss_quantity_source = fields.Selection(
        [
            ("container", "Containers (of the line's size and type)"),
            ("teu", "TEU of the containers"),
            ("shipment", "One per shipment"),
            ("gross_kg", "Gross weight (kg)"),
            ("gross_ton", "Gross weight (tonnes)"),
            ("volume_m3", "Volume (m³)"),
            ("wm", "W/M: larger of tonnes and m³"),
            ("pallets", "Pallets"),
            ("awb_kg", "Chargeable weight of the air waybill (entered on the line when empty)"),
            ("chargeable_kg", "Chargeable weight: higher of gross weight and volume × factor of the shipment's mode "
                              "(air 167, road 333, sea 1000 kg/m³)"),
            ("chargeable_air_kg", "Chargeable weight, air (higher of gross and volume × 167 kg/m³)"),
            ("chargeable_road_kg", "Chargeable weight, road (higher of gross and volume × 333 kg/m³)"),
            ("chargeable_sea_kg", "Chargeable weight, sea (higher of gross and volume × 1000 kg/m³)"),
            ("input", "Entered on the line"),
        ],
        string="BOSS quantity",
        help="Where the quantity of a quotation line in this charge basis comes from. "
        "Empty: not a BOSS charge basis.",
    )
