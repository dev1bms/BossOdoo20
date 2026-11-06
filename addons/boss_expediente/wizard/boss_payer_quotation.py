from odoo import api, fields, models


class BossPayerQuotation(models.TransientModel):
    """A quotation of this file to another payer (go-live tracker P4-09, F0-C56 «one sale order per payer», F0-C57
    «prepaid/collect decides who is invoiced the freight»): the consignee, the shipper, the agent abroad or the notify
    party of the file gets its own quotation, accepted and invoiced on its own, with its own VAT zone and currency.
    The file keeps one orderer (its customer) and sums the sales of every payer."""

    _name = "boss.payer.quotation"
    _description = "Quotation to another payer of the file"

    expediente_id = fields.Many2one("boss.expediente", "File", required=True)
    payer_id = fields.Many2one("res.partner", "Payer", required=True,
                               domain="[('id', 'in', allowed_payer_ids)]")
    allowed_payer_ids = fields.Many2many("res.partner", compute="_compute_allowed_payer_ids")
    pricelist_id = fields.Many2one("product.pricelist", "Price list",
                                   help="Empty: the payer's own price list (a USD list for an agent paid in dollars).")
    hint = fields.Char(compute="_compute_hint")

    @api.depends("expediente_id")
    def _compute_allowed_payer_ids(self):
        for wizard in self:
            file = wizard.expediente_id
            wizard.allowed_payer_ids = file._boss_payer_partners() if file else self.env["res.partner"]

    @api.depends("expediente_id")
    def _compute_hint(self):
        for wizard in self:
            file = wizard.expediente_id
            payment = file.incoterm_id.boss_freight_payment
            if payment == "collect":
                wizard.hint = self.env._("Freight collect (%s): the freight is invoiced to the payer at destination "
                                         "(consignee or agent).", file.incoterm_id.code)
            elif payment == "prepaid":
                wizard.hint = self.env._("Freight prepaid (%s): the freight is invoiced to the orderer; other services "
                                         "may go to another payer.", file.incoterm_id.code)
            else:
                wizard.hint = False

    def action_confirm(self):
        self.ensure_one()
        return self.expediente_id._boss_quotation_action(self.payer_id, self.pricelist_id)
