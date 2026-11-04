from odoo import fields, models


class BossHouseDocReissue(models.TransientModel):
    """Re-issue a house B/L or air waybill already issued (roadmap item 19): a new issue, with today's date and its
    reason in the history; the earlier copies stay in the file's attachments."""

    _name = "boss.house.doc.reissue"
    _description = "Re-issue a house document"

    expediente_id = fields.Many2one("boss.expediente", "File", required=True)
    reason = fields.Char("Reason", required=True, help="Written in the history of the file.")

    def action_confirm(self):
        self.ensure_one()
        return self.expediente_id._boss_reissue_house_document(self.reason)
