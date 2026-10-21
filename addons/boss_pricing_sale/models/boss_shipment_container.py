from odoo import fields, models

from odoo.addons.boss_pricing.models.boss_container_type import CONTAINER_SIZES

TEU = {"20": 1, "40": 2, "45": 2}


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
