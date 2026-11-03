from odoo import api, fields, models


class BossOperatorAssignment(models.Model):
    """Who operates the files of a customer for a traffic (IMB, IAB, EMB…): the operator proposed as responsible when
    the file opens. The Odoo 17 practice (model «Operative Assign»: customer × traffic → operative, 414 rows on
    03/11/2026; F0-C23 in docs/decisiones-f0.md), maintained here; the responsible can always be changed on the file."""

    _name = "boss.operator.assignment"
    _description = "Operator of a customer for a traffic"
    _order = "partner_id, traffic_code"

    partner_id = fields.Many2one("res.partner", "Customer", required=True, index=True, ondelete="cascade",
                                 domain=[("is_company", "=", True)])
    traffic_code = fields.Char("Traffic", required=True, size=3,
                               help="Direction, mode and whose client: IMB, IAB, EMB, EAB, IMA… (as on the file).")
    user_id = fields.Many2one("res.users", "Operator", required=True, ondelete="cascade",
                              domain=[("share", "=", False)])
    source = fields.Char(help="Where the assignment comes from (Odoo 17 «Operative Assign», a manager…).")
    active = fields.Boolean(default=True)

    _unique = models.Constraint("UNIQUE(partner_id, traffic_code)",
                                "This customer already has an operator for this traffic.")

    @api.model
    def _operator_for(self, partner, traffic_code):
        """The operator of a customer for a traffic, or no user when none is recorded."""
        if not partner or not traffic_code:
            return self.env["res.users"]
        return self.search([("partner_id", "=", partner.commercial_partner_id.id),
                            ("traffic_code", "=", traffic_code)], limit=1).user_id
