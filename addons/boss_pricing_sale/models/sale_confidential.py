from odoo import fields, models

# BOSS buying side of a quotation: internal users only (ADR-010). A customer (portal user) may read his quotation and
# its lines through the standard access rules, but never what BOSS pays, to whom, how the sale price was built or the
# margin: field groups make the ORM refuse these fields to non-internal users on read, search, RPC, export and reports,
# whatever screen asks. purchase_price, margin and margin_percent are already internal in sale_margin.
INTERNAL = "base.group_user"


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    boss_supplier_id = fields.Many2one(groups=INTERNAL)
    boss_execution = fields.Selection(groups=INTERNAL)
    boss_cost_kind = fields.Selection(groups=INTERNAL)
    boss_unknown_cost_reason = fields.Char(groups=INTERNAL)
    boss_cost_on_request = fields.Boolean(groups=INTERNAL)
    boss_cost_status = fields.Selection(groups=INTERNAL)
    boss_cost_amount = fields.Monetary(groups=INTERNAL)
    boss_cost_currency_id = fields.Many2one(groups=INTERNAL)
    boss_tariff_line_id = fields.Many2one(groups=INTERNAL)
    boss_cost_candidate_ids = fields.Many2many(groups=INTERNAL)
    boss_cost_missing = fields.Char(groups=INTERNAL)
    boss_cost_steps = fields.Json(groups=INTERNAL)
    boss_cost_is_estimate = fields.Boolean(groups=INTERNAL)
    boss_cost_explanation = fields.Text(groups=INTERNAL)
    boss_manual_cost = fields.Monetary(groups=INTERNAL)
    boss_manual_cost_note = fields.Char(groups=INTERNAL)
    boss_sale_status = fields.Selection(groups=INTERNAL)
    boss_sale_explanation = fields.Text(groups=INTERNAL)
    boss_markup = fields.Float(groups=INTERNAL)
    boss_vat_trace = fields.Char(groups=INTERNAL)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    boss_haulier_id = fields.Many2one(groups=INTERNAL)
    boss_snapshot_ids = fields.One2many(groups=INTERNAL)
    boss_pricing_alert = fields.Text(groups=INTERNAL)
