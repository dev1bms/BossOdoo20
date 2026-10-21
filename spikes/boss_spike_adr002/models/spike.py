"""Smallest possible extension to test "shipment cost + %" on standard pricelists.

The cost lives on the sale line (one value per offer), never on product.standard_price.
"""
from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[("boss_shipment_cost", "Shipment cost")],
        ondelete={"boss_shipment_cost": "set default"},
    )

    def _compute_base_price(self, product, quantity, uom, **kwargs):
        if self.base == "boss_shipment_cost":
            return self.env.context.get("boss_shipment_cost", 0.0)
        return super()._compute_base_price(product, quantity, uom, **kwargs)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    boss_cost_unit = fields.Float("Shipment cost per unit")

    @api.depends("boss_cost_unit")
    def _compute_price_unit(self):
        return super()._compute_price_unit()

    def _get_pricelist_price(self):
        return super(
            SaleOrderLine, self.with_context(boss_shipment_cost=self.boss_cost_unit)
        )._get_pricelist_price()
