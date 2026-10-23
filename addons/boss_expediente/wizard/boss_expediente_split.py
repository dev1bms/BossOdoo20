from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class BossExpedienteSplit(models.TransientModel):
    """Part of the accepted services of a file goes to another file (new or existing, same customer): one accepted
    quotation may feed several files (owner decision 26/08/2026). Quantities move, they are never duplicated: the
    accepted totals stay the same and so do the sale prices."""

    _name = "boss.expediente.split"
    _description = "Move accepted services to another file"

    expediente_id = fields.Many2one("boss.expediente", "From file", required=True)
    target_id = fields.Many2one(
        "boss.expediente", "To file", help="Empty: a new file with the same customer, parties and route.",
        domain="[('id', '!=', expediente_id), ('state', 'not in', ('closed', 'cancel')), "
               "('financial_closed', '=', False)]")
    line_ids = fields.One2many("boss.expediente.split.line", "wizard_id", "Services")

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        file = self.env["boss.expediente"].browse(values.get("expediente_id"))
        if file and "line_ids" in fields_list:
            values["line_ids"] = [Command.create({"allocation_id": a.id, "quantity": 0.0})
                                  for a in file.allocation_ids.filtered(lambda a: a.order_id.state == "sale")]
        return values

    def action_split(self):
        self.ensure_one()
        source = self.expediente_id
        moves = self.line_ids.filtered(lambda l: l.quantity > 0)
        if not moves:
            raise UserError(self.env._("Type the quantity to move of at least one service."))
        target = self.target_id
        if target and target.partner_id.commercial_partner_id != source.partner_id.commercial_partner_id:
            raise UserError(self.env._("Both files must have the same customer."))
        target = target or self.env["boss.expediente"].create(source._boss_copy_values())
        (source | target)._boss_lock()
        sale_lines = moves.allocation_id.sale_line_id
        summary = ", ".join(f"{m.product_id.default_code or m.product_id.name} {m.quantity:g}" for m in moves)
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        Allocation = self.env["boss.expediente.allocation"]
        for move in moves:
            allocation, quantity = move.allocation_id, move.quantity  # the move line goes when its part is emptied
            line = allocation.sale_line_id
            if float_compare(quantity, allocation.quantity, precision_digits=digits) > 0:
                raise UserError(self.env._("%(service)s: only %(qty)s in %(file)s.", service=line.product_id.display_name,
                                           qty=allocation.quantity, file=source.name))
            share = quantity / allocation.quantity
            need = source.cost_ids.filtered(lambda n, line=line: n.sale_line_id == line and n.kind == "sale")
            if need:
                keep = need.quantity * (1 - share)
                ordered = sum(need._boss_active_lines().mapped("product_qty"))
                if float_compare(ordered, keep, precision_digits=digits) > 0:
                    raise UserError(self.env._(
                        "%(service)s is already ordered for %(ordered)s in %(file)s: cancel or reduce the purchase "
                        "order before moving part of it.", service=need.display_name, ordered=ordered,
                        file=source.name))
            target_part = target.allocation_ids.filtered(lambda a, line=line: a.sale_line_id == line)
            remaining = allocation.quantity - quantity
            if float_compare(remaining, 0.0, precision_digits=digits) > 0:
                allocation.quantity = remaining
            else:
                allocation.unlink()
            if target_part:
                target_part.quantity += quantity
            else:
                Allocation.create({"expediente_id": target.id, "sale_line_id": line.id, "quantity": quantity})
            if need:
                moved = need.quantity * share
                accepted = need.accepted_amount_company * share
                left = need.quantity - moved
                need.write({"quantity": left, "accepted_amount_company": need.accepted_amount_company - accepted,
                            "closed": float_compare(left, 0.0, precision_digits=digits) <= 0})
                twin = target.cost_ids.filtered(lambda n, line=line: n.sale_line_id == line and n.kind == "sale")
                if twin:
                    twin.write({"quantity": twin.quantity + moved,
                                "accepted_amount_company": twin.accepted_amount_company + accepted})
                else:
                    need.copy({"expediente_id": target.id, "quantity": moved, "accepted_amount_company": accepted,
                               "closed": False,
                               "accepted_unit_cost": need.accepted_unit_cost,
                               "accepted_cost_kind": need.accepted_cost_kind, "tariff_line_id": need.tariff_line_id.id,
                               "expected_date": need.expected_date})
        sale_lines._boss_sync_file_analytic()
        body = self.env._("Services moved from %(origin)s to %(target)s: %(lines)s", origin=source.name,
                          target=target.name, lines=summary)
        for file in source | target:
            file.message_post(body=body)
        return {"type": "ir.actions.act_window", "res_model": "boss.expediente", "view_mode": "form",
                "views": [(False, "form")], "res_id": target.id}


class BossExpedienteSplitLine(models.TransientModel):
    _name = "boss.expediente.split.line"
    _description = "Service to move to another file"

    wizard_id = fields.Many2one("boss.expediente.split", required=True, ondelete="cascade")
    allocation_id = fields.Many2one("boss.expediente.allocation", required=True, readonly=True)
    order_id = fields.Many2one(related="allocation_id.order_id")
    product_id = fields.Many2one(related="allocation_id.product_id")
    uom_id = fields.Many2one(related="allocation_id.uom_id")
    available = fields.Float(related="allocation_id.quantity", string="In this file")
    quantity = fields.Float("To move", digits="Product Unit")
