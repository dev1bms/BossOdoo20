from odoo import fields, models

from ..models.sale_order_line import CONTAINER_SOURCES


class BossAddServices(models.TransientModel):
    _name = "boss.add.services"
    _description = "Add BOSS services to a quotation"

    order_id = fields.Many2one("sale.order", required=True)
    product_ids = fields.Many2many(
        "product.product", string="Services", required=True,
        domain="[('boss_pricing_mode', '!=', False), ('sale_ok', '=', True)]")

    def _charge_bases(self, product):
        """One line per container size present in the shipment, otherwise the service's main unit."""
        bases = product.product_tmpl_id._boss_charge_bases()
        sized = bases.filtered(lambda u: u.boss_quantity_source in CONTAINER_SOURCES)
        present = sized.filtered(lambda u: self.order_id._boss_quantity(u.boss_quantity_source))
        return present or product.uom_id

    def action_add(self):
        self.ensure_one()
        self.env["sale.order.line"].create([
            {"order_id": self.order_id.id, "product_id": product.id, "product_uom_id": uom.id}
            for product in self.product_ids for uom in self._charge_bases(product)
        ])
        return {"type": "ir.actions.act_window_close"}
