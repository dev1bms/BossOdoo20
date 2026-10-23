from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends("boss_pricing_mode")
    def _compute_purchase_method(self):
        """BOSS services are billed by the supplier once performed: bill control on received (performed) quantities,
        the service marked «Performed» on the file (approved 23/10/2026, P32). Other products keep Odoo's rule."""
        boss = self.filtered("boss_pricing_mode")
        super(ProductTemplate, self - boss)._compute_purchase_method()
        boss.purchase_method = "receive"
