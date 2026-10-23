from odoo import fields, models


class BossShipmentContainer(models.Model):
    """Planned containers of a quotation, or of an opportunity before its quotation exists."""

    _inherit = "boss.shipment.container"

    order_id = fields.Many2one(required=False)
    lead_id = fields.Many2one("crm.lead", ondelete="cascade", index="btree_not_null")

    _order_or_lead = models.Constraint("CHECK(order_id IS NOT NULL OR lead_id IS NOT NULL)",
                                       "Planned containers belong to a quotation or an opportunity.")
