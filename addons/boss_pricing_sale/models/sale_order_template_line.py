from odoo import models


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    def _prepare_order_line_values(self, fiscal_position, currency):
        """A quotation template lists the services that always apply to a case (air import FOB...). Their quantity
        is counted from the shipment (containers, AWB kg...) like a service added with «Add services», not taken
        from the template line (which can only say 1)."""
        vals = super()._prepare_order_line_values(fiscal_position, currency)
        if self.product_uom_id.boss_quantity_source not in (False, "input"):
            vals.pop("product_uom_qty", None)
        return vals
