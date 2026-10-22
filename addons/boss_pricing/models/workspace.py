from odoo import api, fields, models

# Workspace «Tarifas y proveedores»: summaries on the standard service product and contact (no parallel
# catalogue, no supplier model). Counts follow the record rules of the reader (company, access).

READINESS = [("not_priced", "Not priced from tariffs"), ("no_price", "No supplier price"),
             ("pending", "Prices waiting for approval"), ("outdated", "Prices expired"), ("ready", "Priced")]


def _line_counts(lines):
    states = lines.mapped("validity_state")
    return {"current": sum(s in ("current", "expiring") for s in states),
            "pending": sum(s in ("draft", "to_approve") for s in states),
            "outdated": sum(s in ("expiring", "expired") for s in states)}


class ProductTemplate(models.Model):
    _inherit = "product.template"

    boss_ws_supplier_ids = fields.Many2many("res.partner", string="Suppliers", compute="_compute_boss_ws")
    boss_ws_price_count = fields.Integer("Supplier prices", compute="_compute_boss_ws")
    boss_ws_current_count = fields.Integer("Valid prices", compute="_compute_boss_ws")
    boss_ws_pending_count = fields.Integer("Prices to approve", compute="_compute_boss_ws")
    boss_ws_methods = fields.Char("Calculations", compute="_compute_boss_ws",
                                  help="Calculation used by each supplier (it can differ between suppliers).")
    boss_ws_readiness = fields.Selection(READINESS, "Readiness", compute="_compute_boss_ws")

    @api.depends_context("company", "lang")
    def _compute_boss_ws(self):
        Line = self.env["boss.tariff.line"]
        if not Line.has_access("read"):
            self.update({"boss_ws_supplier_ids": False, "boss_ws_price_count": 0, "boss_ws_current_count": 0,
                         "boss_ws_pending_count": 0, "boss_ws_methods": False, "boss_ws_readiness": False})
            return
        lines = Line.search([("product_id.product_tmpl_id", "in", self.ids), ("tariff_active", "=", True)])
        methods = dict(Line._fields["method"]._description_selection(self.env))
        for template in self:
            mine = lines.filtered(lambda ln: ln.product_id.product_tmpl_id == template)
            counts = _line_counts(mine)
            template.boss_ws_supplier_ids = mine.partner_id
            template.boss_ws_price_count = len(mine)
            template.boss_ws_current_count = counts["current"]
            template.boss_ws_pending_count = counts["pending"]
            template.boss_ws_methods = ", ".join(sorted({methods.get(m, m) for m in mine.mapped("method")})) or False
            if template.boss_pricing_mode != "tariff":
                readiness = "not_priced"
            elif counts["current"]:
                readiness = "ready"
            elif counts["pending"]:
                readiness = "pending"
            elif mine:
                readiness = "outdated"
            else:
                readiness = "no_price"
            template.boss_ws_readiness = readiness

    def action_boss_ws_prices(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("boss_pricing.boss_tariff_line_ws_action")
        action["domain"] = [("product_id.product_tmpl_id", "=", self.id)]
        action["context"] = {"search_default_ws_current": 1, "search_default_ws_pending": 1}
        action["name"] = self.display_name
        return action

    def action_boss_ws_open(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "product.template", "res_id": self.id,
                "view_mode": "form", "views": [(False, "form")], "target": "current"}

    def action_boss_ws_guide(self):
        url = self.env["ir.config_parameter"].sudo().get_param(
            "boss_pricing.guide_url", "https://doc.bosscontinental.com/new/#/")
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}


class ResPartner(models.Model):
    _inherit = "res.partner"

    boss_tariff_ids = fields.One2many("boss.tariff", "partner_id", "Supplier tariffs")
    boss_ws_tariff_count = fields.Integer("Tariffs", compute="_compute_boss_ws")
    boss_ws_price_count = fields.Integer("Supplier prices", compute="_compute_boss_ws")
    boss_ws_pending_count = fields.Integer("Prices to approve", compute="_compute_boss_ws")
    boss_ws_outdated_count = fields.Integer("Expired or expiring", compute="_compute_boss_ws")
    boss_ws_service_count = fields.Integer("Services", compute="_compute_boss_ws")

    @api.depends_context("company")
    def _compute_boss_ws(self):
        if not self.env["boss.tariff"].has_access("read"):
            self.update({"boss_ws_tariff_count": 0, "boss_ws_price_count": 0, "boss_ws_pending_count": 0,
                         "boss_ws_outdated_count": 0, "boss_ws_service_count": 0})
            return
        tariffs = self.env["boss.tariff"].search([("partner_id", "in", self.ids)])
        lines = self.env["boss.tariff.line"].search([("tariff_id", "in", tariffs.ids)])
        for partner in self:
            mine = lines.filtered(lambda ln: ln.partner_id == partner)
            counts = _line_counts(mine)
            partner.boss_ws_tariff_count = len(tariffs.filtered(lambda t: t.partner_id == partner))
            partner.boss_ws_price_count = len(mine)
            partner.boss_ws_pending_count = counts["pending"]
            partner.boss_ws_outdated_count = counts["outdated"]
            partner.boss_ws_service_count = len(mine.product_id)

    def action_boss_ws_prices(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("boss_pricing.boss_tariff_line_ws_action")
        action["domain"] = [("partner_id", "=", self.id)]
        action["context"] = {"search_default_ws_current": 1, "search_default_ws_pending": 1}
        action["name"] = self.display_name
        return action

    def action_boss_ws_tariffs(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("boss_pricing.boss_tariff_action")
        action.update(domain=[("partner_id", "=", self.id)], name=self.display_name,
                      context={"default_partner_id": self.id})
        return action

    def action_boss_ws_open(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "res.partner", "res_id": self.id,
                "view_mode": "form", "views": [(False, "form")], "target": "current"}
