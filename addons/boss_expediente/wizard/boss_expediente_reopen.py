from odoo import fields, models


class BossExpedienteReopen(models.TransientModel):
    """Reopen the operations of a closed or cancelled file (Odoo 17: managers only, «Open (Operative Close)»): the
    reason is written in the history of each file."""

    _name = "boss.expediente.reopen"
    _description = "Reopen a file"

    expediente_ids = fields.Many2many("boss.expediente", string="Files", required=True)
    reason = fields.Char("Reason", required=True, help="Written in the history of the file.")

    def action_confirm(self):
        self.ensure_one()
        self.expediente_ids._boss_reopen(self.reason)
        return {"type": "ir.actions.act_window_close"}
