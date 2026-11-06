from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class BossInvoiceServices(models.TransientModel):
    """Invoice some services of a file now and the rest later (milestones). Each invoice line gets the quantity of this
    file (a sale line may be shared by several files) and the file's analytic account. Quantities can still be reduced
    on the draft invoice for a partial invoice; credit notes are the standard ones."""

    _name = "boss.invoice.services"
    _description = "Invoice selected services"

    expediente_id = fields.Many2one("boss.expediente", "File", required=True)
    allocation_ids = fields.Many2many(
        "boss.expediente.allocation", string="Services to invoice", required=True,
        domain="[('expediente_id', '=', expediente_id), ('order_id.state', '=', 'sale')]")

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        file = self.env["boss.expediente"].browse(values.get("expediente_id"))
        if file and "allocation_ids" in fields_list:
            todo = file.allocation_ids.filtered(lambda a: a.order_id.state == "sale" and a.to_invoice_quantity > 0)
            values["allocation_ids"] = [Command.set(todo.ids)]
        return values

    def action_create(self):
        self.ensure_one()
        allocations = self.allocation_ids.filtered(lambda a: a.to_invoice_quantity > 0)
        if not allocations:
            raise UserError(self.env._("Nothing to invoice in %s.", self.expediente_id.name))
        file = self.expediente_id
        return file._boss_moves_action(file._boss_invoice_allocations(allocations))
