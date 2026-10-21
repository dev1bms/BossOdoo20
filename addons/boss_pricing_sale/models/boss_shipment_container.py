from odoo import fields, models

SIZES = [("20", "20'"), ("40", "40'"), ("45", "45'")]
TEU = {"20": 1, "40": 2, "45": 2}


class BossShipmentContainer(models.Model):
    _name = "boss.shipment.container"
    _description = "Planned containers of a quotation"

    order_id = fields.Many2one("sale.order", required=True, ondelete="cascade", index=True)
    size = fields.Selection(SIZES, required=True, default="40")
    quantity = fields.Integer(required=True, default=1)

    _quantity_positive = models.Constraint("CHECK(quantity > 0)", "The number of containers must be positive.")
