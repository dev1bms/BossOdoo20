from odoo import fields, models


class BossAddServices(models.TransientModel):
    _name = "boss.add.services"
    _description = "Add BOSS services to a quotation"

    order_id = fields.Many2one("sale.order", required=True)
    product_ids = fields.Many2many(
        "product.product", string="Services", required=True,
        domain="[('boss_pricing_mode', '!=', False), ('sale_ok', '=', True)]")

    def _line_values(self, product):
        """Container services: one line per container size and type of the shipment (they may be priced
        and sold differently); other services: one line in their main charge basis."""
        base = {"order_id": self.order_id.id, "product_id": product.id, "product_uom_id": product.uom_id.id}
        if product.uom_id.boss_quantity_source not in ("container", "teu"):
            return [base]
        groups = sorted({(c.size, c.container_type_id) for c in self.order_id.boss_container_ids},
                        key=lambda g: (g[0], g[1].sequence))
        return [dict(base, boss_container_size=size, boss_container_type_id=ctype.id) for size, ctype in groups] or [base]

    def action_add(self):
        self.ensure_one()
        self.env["sale.order.line"].create([vals for product in self.product_ids for vals in self._line_values(product)])
        return {"type": "ir.actions.act_window_close"}
