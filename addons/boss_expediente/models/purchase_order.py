from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    boss_expediente_id = fields.Many2one("boss.expediente", "File", index="btree_not_null", copy=False,
                                         tracking=True)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    boss_cost_id = fields.Many2one("boss.expediente.cost", "Service of the file", index="btree_not_null", copy=False,
                                   readonly=True)

    def _compute_price_unit_and_date_planned_and_name(self):
        """The price of a file's service comes from the BOSS supplier price (or the person who edits it), never from
        product supplier info or the product cost: keep it when quantity, unit or supplier change."""
        boss = self.filtered("boss_cost_id")
        kept = {line: (line.price_unit, line.technical_price_unit, line.discount) for line in boss}
        super()._compute_price_unit_and_date_planned_and_name()
        for line, (price, technical, discount) in kept.items():
            line.price_unit, line.technical_price_unit, line.discount = price, technical, discount
