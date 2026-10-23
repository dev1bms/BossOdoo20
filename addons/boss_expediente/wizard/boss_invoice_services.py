from odoo import Command, api, fields, models
from odoo.exceptions import UserError

from ..models.boss_expediente import with_accounts


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
        quantities = {a.id: a.to_invoice_quantity for a in allocations}  # before the new invoice lines count
        lines = allocations.sale_line_id
        moves = lines.order_id.with_context(boss_invoice_line_ids=lines.ids)._create_invoices()
        plan = self.env.ref("boss_expediente.analytic_plan_files")
        for item in moves.invoice_line_ids.filtered(lambda l: l.sale_line_ids & lines):
            allocation = allocations.filtered(lambda a: a.sale_line_id in item.sale_line_ids)[:1]
            present = self.env["account.analytic.account"].browse(
                {int(k) for c in (item.analytic_distribution or {}) for k in c.split(",") if k.strip()}).exists()
            item.write({
                "quantity": quantities[allocation.id],
                "boss_expediente_id": file.id,
                "analytic_distribution": with_accounts(item.analytic_distribution, {file.analytic_account_id.id: 100.0},
                                                       present.filtered(lambda a: a.plan_id == plan)
                                                       | file.analytic_account_id),
            })
        if len(moves) == 1:
            return {"type": "ir.actions.act_window", "res_model": "account.move", "view_mode": "form",
                    "views": [(False, "form")], "res_id": moves.id}
        return {"type": "ir.actions.act_window", "res_model": "account.move", "view_mode": "list,form",
                "views": [(False, "list"), (False, "form")], "domain": [("id", "in", moves.ids)],
                "name": self.env._("Customer invoices")}
