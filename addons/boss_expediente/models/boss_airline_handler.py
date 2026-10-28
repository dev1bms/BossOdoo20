from odoo import api, fields, models

# Air services bought from the handler of the airline at the airport (Hoja1 B9/C9: airline and handler on the file,
# paired with each other and with the airport).
HANDLER_SERVICE_CODES = ("HAN", "ALM", "AWB", "ETX", "X-R")


class BossAirlineHandler(models.Model):
    """Which handler serves an airline at an airport. Loaded from the Odoo 17 configuration «HandlingConfig» (read
    on 26/10/2026: 48 rows, 47 active loaded: MAD 30, BCN 13, AGP 2, VLC 1, BIO 1) and maintained here. One airline may have a different
    handler per airport, and an airport may list several handlers for the same airline: then the file shows the
    options instead of choosing one."""

    _name = "boss.airline.handler"
    _description = "Handler of an airline at an airport"
    _order = "airport_id, airline_id"

    airline_id = fields.Many2one("res.partner", "Airline", required=True, index=True, ondelete="restrict")
    airline_code = fields.Char("Airline code (AWB prefix)", help="Three-digit IATA prefix of the airline's AWBs.")
    airport_id = fields.Many2one("boss.port", "Airport", required=True, domain=[("kind", "=", "air")],
                                 ondelete="restrict")
    handler_id = fields.Many2one("res.partner", "Handler", required=True, index=True, ondelete="restrict")
    source = fields.Char(help="Where the relation comes from (Odoo 17 configuration, supplier notice, Cristina...).")
    active = fields.Boolean(default=True)

    _unique = models.Constraint("UNIQUE(airline_id, airport_id, handler_id)",
                                "This handler is already set for the airline at this airport.")

    @api.model
    def _handlers_for(self, airline, airport):
        """Handlers known for an airline at an airport (empty when none is recorded)."""
        if not airline or not airport:
            return self.env["res.partner"]
        return self.search([("airline_id", "in", airline._boss_carrier_family_ids()), ("airport_id", "=", airport.id)]
                           ).handler_id
