from odoo import api, models
from odoo.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    # Standard pricelists hold agreed sale prices of BOSS services, with two guards (spike T2b, T3):
    # a price says its charge basis, and two prices for the same case never overlap silently.
    @api.constrains("product_tmpl_id", "product_id", "uom_id", "pricelist_id", "min_quantity",
                    "date_start", "date_end")
    def _check_boss_service_prices(self):
        for item in self:
            template = item.product_id.product_tmpl_id or item.product_tmpl_id
            if not template.boss_pricing_mode:
                continue
            if not item.uom_id:
                raise ValidationError(self.env._(
                    "A price of %s must say its charge basis (container 40', B/L, kg...).",
                    template.display_name))
            same = self.search([
                ("id", "!=", item.id), ("pricelist_id", "=", item.pricelist_id.id),
                ("product_tmpl_id", "=", template.id), ("product_id", "=", item.product_id.id),
                ("uom_id", "=", item.uom_id.id), ("min_quantity", "=", item.min_quantity),
            ])
            for other in same:
                starts_before_end = not other.date_end or not item.date_start or item.date_start <= other.date_end
                ends_after_start = not other.date_start or not item.date_end or item.date_end >= other.date_start
                if starts_before_end and ends_after_start:
                    raise ValidationError(self.env._(
                        "Two prices of %(service)s per %(uom)s overlap in %(pricelist)s: keep one, or "
                        "make their dates consecutive.", service=template.display_name,
                        uom=item.uom_id.name, pricelist=item.pricelist_id.name))
