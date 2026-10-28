from odoo import fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    boss_expediente_id = fields.Many2one("boss.expediente", "File", index="btree_not_null", copy=False,
                                         tracking=True)

    def action_create_invoice(self):
        """Odoo 20 copies every line on the bill, quantity 0 when the service is not performed yet: an order of a
        file with nothing performed would give a bill of zeros. Say so instead (seen on boss20_uat, 26/10/2026)."""
        for order in self.filtered("boss_expediente_id"):
            if not any(l.qty_to_invoice for l in order.order_line if not l.display_type):
                raise UserError(self.env._(
                    "%s: no service of this order is marked as performed yet, there is nothing to bill. Mark the "
                    "performed services on the file first.", order.display_name))
        return super().action_create_invoice()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    boss_cost_id = fields.Many2one("boss.expediente.cost", "Service of the file", index="btree_not_null", copy=False,
                                   readonly=True)

    def _prepare_account_move_line(self, move=False):
        """The bill line of a file's purchase carries the file, like the customer invoice lines of the file."""
        vals = super()._prepare_account_move_line(move)
        file = self.boss_cost_id.expediente_id or self.order_id.boss_expediente_id
        if file:
            vals["boss_expediente_id"] = file.id
        return vals

    def _compute_price_unit_and_date_planned_and_name(self):
        """The price of a file's service comes from the BOSS supplier price (or the person who edits it), never from
        product supplier info or the product cost: keep it when quantity, unit or supplier change."""
        boss = self.filtered("boss_cost_id")
        kept = {line: (line.price_unit, line.technical_price_unit, line.discount) for line in boss}
        super()._compute_price_unit_and_date_planned_and_name()
        for line, (price, technical, discount) in kept.items():
            line.price_unit, line.technical_price_unit, line.discount = price, technical, discount
