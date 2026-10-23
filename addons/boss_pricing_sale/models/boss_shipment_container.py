from odoo import fields, models

from odoo.addons.boss_pricing.models.boss_container_type import CONTAINER_SIZES

TEU = {"20": 1, "40": 2, "45": 2}


def shipment_quantity(source, containers, gross_kg, volume_m3, pallets, awb_kg, size=False, ctype=False):
    """Quantity of a charge basis taken from shipment data (quotation or file), or None when it is entered on the
    line. containers: [(size, container type, quantity)]. One function for every screen (ADR-003/005)."""
    rows = [(s, t, q) for s, t, q in containers if (not size or s == size) and (not ctype or t == ctype)]
    values = {
        "shipment": 1.0,
        "container": float(sum(q for _s, _t, q in rows)),
        "teu": float(sum(q * TEU[s] for s, _t, q in rows)),
        "gross_kg": gross_kg,
        "gross_ton": gross_kg / 1000,
        "volume_m3": volume_m3,
        "wm": max(gross_kg / 1000, volume_m3),
        "pallets": float(pallets),
        "awb_kg": awb_kg or None,  # empty: the quantity stays the one typed on the line
    }
    return values.get(source)


class BossShipmentContainer(models.Model):
    _name = "boss.shipment.container"
    _description = "Planned containers of a quotation"

    order_id = fields.Many2one("sale.order", required=True, ondelete="cascade", index=True)
    size = fields.Selection(CONTAINER_SIZES, required=True, default="40")
    container_type_id = fields.Many2one("boss.container.type", "Type", required=True,
                                        default=lambda self: self.env.ref("boss_pricing.container_type_dv",
                                                                          raise_if_not_found=False))
    quantity = fields.Integer(required=True, default=1)

    _quantity_positive = models.Constraint("CHECK(quantity > 0)", "The number of containers must be positive.")
