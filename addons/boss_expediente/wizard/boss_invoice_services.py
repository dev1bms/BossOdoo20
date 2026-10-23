from odoo import Command, api, fields, models


class BossInvoiceServices(models.TransientModel):
    """Invoice some services of a file now and the rest later (milestones). Quantities can still be reduced on the
    draft invoice for a partial invoice; credit notes are the standard ones."""

    _name = "boss.invoice.services"
    _description = "Invoice selected services"

    expediente_id = fields.Many2one("boss.expediente", "File")
    order_ids = fields.Many2many("sale.order", string="Orders", required=True)
    line_ids = fields.Many2many(
        "sale.order.line", string="Services to invoice", required=True,
        domain="[('order_id', 'in', order_ids), ('qty_to_invoice', '>', 0), ('display_type', '=', False)]")

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        file = self.env["boss.expediente"].browse(values.get("expediente_id"))
        orders = file.sale_order_ids.filtered(lambda o: o.state == "sale")
        if file and "order_ids" in fields_list:
            values["order_ids"] = [Command.set(orders.ids)]
        if file and "line_ids" in fields_list:
            lines = orders.order_line.filtered(lambda l: l.qty_to_invoice > 0 and not l.display_type)
            values["line_ids"] = [Command.set(lines.ids)]
        return values

    def action_create(self):
        self.ensure_one()
        orders = self.line_ids.order_id
        moves = orders.with_context(boss_invoice_line_ids=self.line_ids.ids)._create_invoices()
        if len(moves) == 1:
            return {"type": "ir.actions.act_window", "res_model": "account.move", "view_mode": "form",
                    "views": [(False, "form")], "res_id": moves.id}
        return {"type": "ir.actions.act_window", "res_model": "account.move", "view_mode": "list,form",
                "views": [(False, "list"), (False, "form")], "domain": [("id", "in", moves.ids)],
                "name": self.env._("Customer invoices")}
