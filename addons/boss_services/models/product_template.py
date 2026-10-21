from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # A BOSS service is a standard service product (ADR-001); these fields only describe how it
    # is priced. The supplier price itself lives in boss_pricing tariffs.
    boss_pricing_mode = fields.Selection(
        [
            ("tariff", "Supplier tariff"),
            ("manual", "Manual amount"),
            ("own", "BOSS own fee (no cost)"),
            ("pending", "Pending business decision"),
        ],
        string="Cost source",
        help="Supplier tariff: the cost is computed from approved supplier tariffs.\n"
        "Manual amount: a person enters the cost of each shipment (freight offer, amount paid "
        "on behalf of the customer...).\n"
        "BOSS own fee: no supplier cost.\n"
        "Pending business decision: the service exists but is not priced until the open "
        "question is answered.",
    )
    boss_cost_method = fields.Selection(
        [
            ("per_unit", "Price per unit"),
            ("max_of_bases", "Larger of several bases"),
            ("tiers", "Brackets"),
            ("route_tiers", "Route and brackets"),
            ("time", "Time with free period"),
            ("percent", "Percentage of a base"),
            ("manual", "Manual amount"),
            ("none", "No cost"),
        ],
        string="Calculation method",
        help="How supplier prices of this service are usually computed. A supplier price "
        "line may use another method if the supplier document says so.",
    )
    boss_open_question = fields.Char(
        "Open question",
        help="Reference of the open business question (docs/preguntas-abiertas.md) that "
        "affects this service.",
    )
    boss_vat_class = fields.Selection(
        [("NS", "NS - not subject"), ("EX", "EX - exempt"), ("NR", "NR - normal rules")],
        string="VAT class",
        help="Base VAT class of the service (Ángel's VAT rules, 31/08/2026). NS and EX never carry VAT; "
        "NR follows the origin/destination and customer rules. The Odoo tax used for each class is a "
        "company setting.")
    boss_legacy_codes = fields.Char("Former codes", help="Odoo 17 codes now priced as this service.")
    boss_replaced_by_id = fields.Many2one(
        "product.template", "Replaced by", help="Former service kept for history; quote the new one.")
    boss_o17_concept_id = fields.Integer(
        "Odoo 17 concept ID", help="Identity of the Odoo 17 concept (x_concept) for migration."
    )
    boss_o17_concept_code = fields.Char("Odoo 17 concept code")

    def _boss_charge_bases(self):
        """Units a BOSS service can be priced and sold in: its unit and its other units."""
        self.ensure_one()
        return self.uom_id | self.uom_ids
