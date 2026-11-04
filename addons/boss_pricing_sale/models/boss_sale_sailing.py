from odoo import api, fields, models


class BossSaleSailing(models.Model):
    """Sailings offered with a quotation (Odoo 17 «Schedules» of the quotation; the itinerary block of the commercial
    team's offers: POL, POD, cut-off, ETD, ETA, transit, route, vessel). Optional. The sailing the customer chooses gives
    the quotation its ETD and ETA (and so the date of the freight tariff) and goes to the file."""

    _name = "boss.sale.sailing"
    _description = "Sailing offered with a quotation"
    _order = "order_id, sequence, etd, id"

    order_id = fields.Many2one("sale.order", "Quotation", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    carrier_id = fields.Many2one("res.partner", "Carrier", domain="[('parent_id', '=', False)]")
    vessel = fields.Char("Vessel")
    voyage = fields.Char("Voyage")
    via = fields.Char("Via", help="Transshipment port or route (e.g. Singapore, Rotterdam).")
    cutoff = fields.Date("Cut-off")
    etd = fields.Date("ETD")
    eta = fields.Date("ETA")
    transit_days = fields.Integer("Transit (days)", compute="_compute_transit_days", store=True, readonly=False)
    chosen = fields.Boolean("Chosen", help="The sailing the customer books: its ETD and ETA become the quotation's and "
                                           "it goes to the file.")

    @api.depends("etd", "eta")
    def _compute_transit_days(self):
        for sailing in self:
            if sailing.etd and sailing.eta and not sailing.transit_days:
                sailing.transit_days = (sailing.eta - sailing.etd).days

    @api.model_create_multi
    def create(self, vals_list):
        sailings = super().create(vals_list)
        sailings.filtered("chosen")._boss_apply_choice()
        return sailings

    def write(self, vals):
        res = super().write(vals)
        if vals.get("chosen") or (any(f in vals for f in ("etd", "eta")) and self.filtered("chosen")):
            self.filtered("chosen")._boss_apply_choice()
        return res

    def _boss_apply_choice(self):
        """One chosen sailing per quotation; its dates become the quotation's planned dates (not on an accepted one)."""
        for sailing in self:
            order = sailing.order_id
            (order.boss_sailing_ids - sailing).filtered("chosen").write({"chosen": False})
            if order.state in ("draft", "sent"):
                values = {f: sailing[s] for f, s in (("boss_etd", "etd"), ("boss_eta", "eta")) if sailing[s]}
                if sailing.carrier_id and not order.boss_carrier_id:
                    values["boss_carrier_id"] = sailing.carrier_id.id
                if values:
                    order.write(values)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    boss_sailing_ids = fields.One2many("boss.sale.sailing", "order_id", "Sailings", copy=True)
