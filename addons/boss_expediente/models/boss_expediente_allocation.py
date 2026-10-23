from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

from .boss_expediente import SALE_GROUPS


class BossExpedienteAllocation(models.Model):
    """Part of an accepted sale line that belongs to a file. One accepted quotation may feed several files (owner
    decision 26/08/2026): each file gets part or all of the accepted quantities, and the parts never exceed them."""

    _name = "boss.expediente.allocation"
    _description = "Part of an accepted sale line in a shipment file"
    _order = "expediente_id, sale_line_id"

    expediente_id = fields.Many2one("boss.expediente", "File", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="expediente_id.company_id", store=True)
    sale_line_id = fields.Many2one("sale.order.line", "Sale line", required=True, ondelete="restrict", index=True)
    order_id = fields.Many2one(related="sale_line_id.order_id", store=True, index=True)
    product_id = fields.Many2one(related="sale_line_id.product_id")
    uom_id = fields.Many2one(related="sale_line_id.product_uom_id", string="Unit")
    accepted_quantity = fields.Float(related="sale_line_id.product_uom_qty", string="Accepted quantity")
    quantity = fields.Float("Quantity in this file", digits="Product Unit", required=True)
    currency_id = fields.Many2one(related="sale_line_id.currency_id")
    amount = fields.Monetary("Sale in this file", compute="_compute_amount", currency_field="currency_id",
                             groups=SALE_GROUPS,
                             help="Untaxed sale of the line in proportion to the quantity of this file.")

    invoiced_quantity = fields.Float("Invoiced in this file", digits="Product Unit",
                                     compute="_compute_invoiced_quantity", compute_sudo=True)
    to_invoice_quantity = fields.Float("To invoice in this file", digits="Product Unit",
                                       compute="_compute_invoiced_quantity", compute_sudo=True)

    _file_line_unique = models.Constraint("UNIQUE(expediente_id, sale_line_id)",
                                          "A sale line has one part per file.")

    @api.depends("quantity", "sale_line_id.price_subtotal", "sale_line_id.product_uom_qty")
    def _compute_amount(self):
        for allocation in self:
            line = allocation.sale_line_id
            allocation.amount = line.price_subtotal * allocation.quantity / line.product_uom_qty \
                if line.product_uom_qty else 0.0

    @api.depends("quantity", "sale_line_id.qty_to_invoice", "sale_line_id.boss_allocation_ids",
                 "sale_line_id.invoice_lines.quantity", "sale_line_id.invoice_lines.parent_state",
                 "sale_line_id.invoice_lines.boss_expediente_id")
    def _compute_invoiced_quantity(self):
        """Invoice lines (draft or posted, credit notes deducted) of the sale line made for this file; when the line
        is in one file only, all its invoice lines are of that file."""
        for allocation in self:
            line = allocation.sale_line_id
            single = len(line.boss_allocation_ids) == 1
            items = line.invoice_lines.filtered(
                lambda l: l.parent_state != "cancel"
                and (l.boss_expediente_id == allocation.expediente_id or (single and not l.boss_expediente_id)))
            invoiced = sum(-l.quantity if l.move_id.move_type == "out_refund" else l.quantity for l in items)
            allocation.invoiced_quantity = invoiced
            allocation.to_invoice_quantity = max(min(allocation.quantity - invoiced, line.qty_to_invoice), 0.0)

    @api.constrains("quantity", "sale_line_id")
    def _check_quantity(self):
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        for line in self.sale_line_id:
            parts = self.search([("sale_line_id", "=", line.id)])
            if any(float_compare(p.quantity, 0.0, precision_digits=digits) <= 0 for p in parts):
                raise ValidationError(self.env._("The quantity of a file must be positive."))
            if float_compare(sum(parts.mapped("quantity")), line.product_uom_qty, precision_digits=digits) > 0:
                raise ValidationError(self.env._(
                    "%(service)s of %(order)s: the files would get %(files)s, more than the %(accepted)s accepted.",
                    service=line.product_id.display_name, order=line.order_id.name,
                    files=sum(parts.mapped("quantity")), accepted=line.product_uom_qty))
