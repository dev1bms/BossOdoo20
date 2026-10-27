from odoo import api, fields, models

from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES

from .boss_shipment_route import BUSINESSES, traffic_code


class SaleOrderTemplate(models.Model):
    """A quotation template is a BOSS case (air import FOB, sea import FCL...): besides its services it says the
    direction, mode, load type, incoterm and whose client, and a quotation made from it starts with them (ADR-006)."""
    _inherit = "sale.order.template"

    boss_business = fields.Selection(BUSINESSES, "Business of")
    boss_direction = fields.Selection(DIRECTIONS, "Direction")
    boss_transport_mode = fields.Selection(TRANSPORT_MODES, "Transport mode")
    boss_load_type = fields.Selection(LOAD_TYPES, "Load type")
    boss_incoterm_id = fields.Many2one("account.incoterms", "Incoterm")
    boss_traffic_code = fields.Char("Traffic", compute="_compute_boss_traffic_code")

    @api.depends("boss_direction", "boss_transport_mode", "boss_business")
    def _compute_boss_traffic_code(self):
        for template in self:
            template.boss_traffic_code = traffic_code(template.boss_direction, template.boss_transport_mode,
                                                      template.boss_business)
