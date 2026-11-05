from odoo import api, fields, models

from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES

from .boss_expediente import STATES


class BossMarginReport(models.Model):
    """Margin of every file, by responsible, salesperson, customer, traffic and month (Cristina CR-O11: estimated and
    real gross profit per user, customer and traffic). One row per file with the figures of the file (the same
    documents and rules); the rows of the files in progress are recomputed when the report opens, the row of a file is
    fixed at its financial close (and recomputed if it is reopened)."""

    _name = "boss.margin.report"
    _description = "Margin by file"
    _order = "key_date desc, id desc"
    _rec_name = "expediente_id"

    expediente_id = fields.Many2one("boss.expediente", "File", required=True, index=True, ondelete="cascade")
    company_id = fields.Many2one("res.company", required=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    user_id = fields.Many2one("res.users", "Responsible")
    salesman_id = fields.Many2one("res.users", "Salesperson")
    partner_id = fields.Many2one("res.partner", "Customer")
    traffic_code = fields.Char("Traffic")
    direction = fields.Selection(DIRECTIONS)
    transport_mode = fields.Selection(TRANSPORT_MODES, "Transport mode")
    load_type = fields.Selection(LOAD_TYPES, "Load type")
    key_date = fields.Date("Important date", help="Arrival of an import, departure of the others (actual, else planned).")
    state = fields.Selection(STATES, "Status")
    financial_closed = fields.Boolean("Financially closed")
    amount_sale = fields.Monetary("Agreed sale")
    amount_invoiced = fields.Monetary("Invoiced")
    amount_cost_forecast = fields.Monetary("Forecast cost")
    amount_cost_actual = fields.Monetary("Actual cost")
    amount_margin_forecast = fields.Monetary("Forecast margin")
    amount_margin_final = fields.Monetary("Final margin")
    margin_final = fields.Boolean("Margin final")
    refreshed_on = fields.Datetime("Figures of")

    @api.model
    def _boss_values(self, file):
        actual = (file.ata if file.direction == "import" else file.atd)
        planned = file.eta if file.direction == "import" else file.etd
        order = file.sale_order_ids.filtered(lambda o: o.state == "sale")[:1]
        # A master's shared costs are already counted in each house's share (amount_master_cost): the master's row
        # shows its costs net of what it passed to its houses, so the rows add up to the consolidated margin
        # (go-live tracker P2-17, audit 05/11/2026: the report counted the shared costs twice).
        houses = file.house_ids.filtered(lambda h: h.state != "cancel")
        passed, passed_actual = sum(houses.mapped("amount_master_cost")), sum(houses.mapped("amount_master_cost_actual"))
        return {
            "expediente_id": file.id, "company_id": file.company_id.id, "user_id": file.user_id.id,
            "salesman_id": order.user_id.id, "partner_id": file.partner_id.id, "traffic_code": file.traffic_code,
            "direction": file.direction, "transport_mode": file.transport_mode, "load_type": file.load_type,
            "key_date": fields.Date.to_date(actual) if actual else planned, "state": file.state,
            "financial_closed": file.financial_closed, "amount_sale": file.amount_sale,
            "amount_invoiced": file.amount_invoiced, "amount_cost_forecast": file.amount_cost_forecast - passed,
            "amount_cost_actual": file.amount_cost_actual - passed_actual,
            "amount_margin_forecast": file.amount_margin_forecast + passed,
            "amount_margin_final": file.amount_margin_final + passed_actual, "margin_final": file.margin_final,
            "refreshed_on": fields.Datetime.now(),
        }

    @api.model
    def _boss_refresh(self, files=None):
        """Rows of the given files, or of every file not closed financially (the closed ones keep their row)."""
        File = self.env["boss.expediente"].sudo()
        files = files.sudo() if files is not None else File.search([("financial_closed", "=", False)])
        Report = self.sudo()
        Report.search(["|", ("expediente_id", "in", files.ids), ("expediente_id.state", "=", "cancel")]).unlink()
        Report.create([self._boss_values(file) for file in files.filtered(lambda f: f.state != "cancel")])

    @api.model
    def action_open_report(self):
        """The report with today's figures of the files in progress (menu)."""
        self._boss_refresh()
        return self.env["ir.actions.act_window"]._for_xml_id("boss_expediente.boss_margin_report_action")
