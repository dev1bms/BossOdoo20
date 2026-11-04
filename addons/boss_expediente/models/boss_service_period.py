from odoo import api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES
from odoo.addons.boss_pricing.models.boss_tariff_line import PERIOD_EVENTS

# Period of the time-based services when the supplier price does not state its own events (Cristina, 25/09/2026, and
# the carrier tariffs): the seed of the lines on each service (settings study of 04/11/2026, phase 2); afterwards
# maintained on the service, never here. (code, direction, load type or None): (start, end); (None, None) = no period.
DEFAULT_PERIOD_EVENTS = {
    ("ALM", "import", "lcl"): ("emptying", "pickup"),
    ("ALM", "export", "lcl"): (None, None),
    ("ALM", "import", None): ("noa_or_ata", "pickup"),
    ("ALM", "export", None): ("foh", "departure"),
    ("DEM", "import", None): ("ata", "container_empty_return"),
    ("DEM", "export", None): ("container_gate_in", "departure"),
    ("OCU", "import", None): ("ata", "container_full_out"),
    ("OCU", "export", None): ("container_gate_in", "departure"),
    ("DET", "export", None): ("container_empty_out", "container_gate_in"),
}


class BossServicePeriod(models.Model):
    """Default period of a time-based service (storage, demurrage, port storage, detention) in a direction and,
    optionally, a load type: the events that start and end it when the supplier price states none. A line with no
    events means «no period» (the cost is typed)."""
    _name = "boss.service.period"
    _description = "Default period of a time-based service"
    _order = "product_tmpl_id, direction, load_type, id"

    product_tmpl_id = fields.Many2one("product.template", "Service", required=True, ondelete="cascade", index=True)
    direction = fields.Selection(DIRECTIONS, required=True)
    load_type = fields.Selection(LOAD_TYPES, "Load type", help="Empty: any load type of that direction.")
    start_event = fields.Selection(PERIOD_EVENTS, "The period starts at")
    end_event = fields.Selection(PERIOD_EVENTS, "The period ends at")

    _one_per_case = models.Constraint("UNIQUE(product_tmpl_id, direction, load_type)",
                                      "One default period per service, direction and load type.")

    @api.constrains("start_event", "end_event")
    def _check_events(self):
        """Both events or none («no period»): a period with a start and no end cannot be computed."""
        for line in self:
            if bool(line.start_event) != bool(line.end_event):
                raise ValidationError(self.env._(
                    "%(service)s, %(direction)s: give the period both its start and its end, or leave both empty for "
                    "«no period».", service=line.product_tmpl_id.display_name,
                    direction=dict(line._fields["direction"]._description_selection(self.env)).get(line.direction)))

    @api.constrains("product_tmpl_id", "direction", "load_type")
    def _check_one_any_load_type(self):
        """The database cannot refuse two «any load type» lines of a direction (empty values are all different)."""
        for line in self.filtered(lambda p: not p.load_type):
            if line.product_tmpl_id.boss_period_ids.filtered(
                    lambda p: p != line and p.direction == line.direction and not p.load_type):
                raise ValidationError(self.env._("One default period per service, direction and load type."))


class ProductTemplate(models.Model):
    _inherit = "product.template"

    boss_period_ids = fields.One2many("boss.service.period", "product_tmpl_id", "Default periods",
                                      help="For a time-based service: when its period starts and ends in each "
                                           "direction, unless the supplier price states its own events.")

    def _boss_default_period(self, direction, load_type):
        """(start, end, found): the line of this direction and load type, else of the direction alone."""
        self.ensure_one()
        lines = self.boss_period_ids.filtered(lambda p: p.direction == direction)
        line = lines.filtered(lambda p: p.load_type == load_type)[:1] or lines.filtered(lambda p: not p.load_type)[:1]
        if not (line.start_event and line.end_event):  # half a period (older data) is no period
            return (False, False, bool(line))
        return (line.start_event, line.end_event, True)


def seed_service_periods(env):
    """Give the time-based services their default periods once (install or upgrade): a service that already has
    lines keeps them."""
    Period = env["boss.service.period"]
    for (code, direction, load_type), (start, end) in DEFAULT_PERIOD_EVENTS.items():
        template = env["product.template"].with_context(active_test=False).search([("default_code", "=", code)], limit=1)
        if not template or template.boss_period_ids:
            continue
        for (c, d, lt), (s, e) in DEFAULT_PERIOD_EVENTS.items():
            if c == code:
                Period.create({"product_tmpl_id": template.id, "direction": d, "load_type": lt or False,
                               "start_event": s or False, "end_event": e or False})

