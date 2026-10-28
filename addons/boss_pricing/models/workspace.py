from odoo import api, fields, models
from odoo.exceptions import UserError

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
    boss_ws_readiness = fields.Selection(READINESS, "Readiness", compute="_compute_boss_ws",
                                         search="_search_boss_ws_readiness")

    def _search_boss_ws_readiness(self, operator, value):
        """Filter on the computed readiness (it depends on today's validity, so it is never stored)."""
        if operator not in ("in", "="):
            return NotImplemented
        wanted = {value} if operator == "=" else set(value)
        services = self.search([("boss_pricing_mode", "!=", False)])
        return [("id", "in", services.filtered(lambda t: t.boss_ws_readiness in wanted).ids)]

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

    def action_boss_ws_new_price(self):
        """Add a supplier price to this existing service (never a new product)."""
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "boss.tariff.line", "view_mode": "form",
                "views": [(self.env.ref("boss_pricing.boss_tariff_line_view_form").id, "form")], "target": "current",
                "name": self.env._("New supplier price"),
                "context": {"boss_ws": 1, "default_product_id": self.product_variant_id.id}}

    def action_boss_ws_open(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "product.template", "res_id": self.id,
                "view_mode": "form", "views": [(False, "form")], "target": "current"}

    def action_boss_ws_guide(self):
        url = self.env["ir.config_parameter"].sudo().get_str(
            "boss_pricing.guide_url", "https://doc.bosscontinental.com/new/#/")
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}


class ResPartner(models.Model):
    _inherit = "res.partner"

    boss_tariff_ids = fields.One2many("boss.tariff", "partner_id", "Supplier tariffs")
    boss_demo = fields.Boolean(
        "Demo customer", help="Training or demonstration customer: only this kind of customer can be priced with "
        "demo tariffs. Real customers never are.")
    boss_ws_tariff_count = fields.Integer("Tariffs", compute="_compute_boss_ws")
    boss_ws_price_count = fields.Integer("Supplier prices", compute="_compute_boss_ws")
    boss_ws_pending_count = fields.Integer("Prices to approve", compute="_compute_boss_ws")
    boss_ws_outdated_count = fields.Integer("Expired or expiring", compute="_compute_boss_ws")
    boss_ws_service_count = fields.Integer("Services", compute="_compute_boss_ws")
    # One commercial carrier, several legal entities (MSC Spain, MSC Switzerland, MSC USA... each with its own tax
    # id and bills): the quotation names the carrier, the tariffs and bills keep the legal entity (Ángel and Belal,
    # meeting of 27/10/2026). Tariffs match on the family: the carrier itself and every legal entity that is part of it.
    boss_carrier_group_id = fields.Many2one(
        "res.partner", "Part of carrier", domain="[('is_company', '=', True), ('id', '!=', id)]", index="btree_not_null",
        help="Commercial carrier this legal entity belongs to (e.g. MSC Spain → Mediterranean Shipping Company). A "
        "quotation naming the carrier is priced by the tariffs of all its entities; purchases and bills keep this entity.")

    def _boss_carrier_family(self):
        """The commercial carrier a partner stands for: its group, else its own company."""
        self.ensure_one()
        return self.boss_carrier_group_id or self.commercial_partner_id

    def _boss_carrier_family_ids(self):
        """Every partner of the same carrier family (the carrier and its legal entities)."""
        family = self._boss_carrier_family()
        return (family | self.search([("boss_carrier_group_id", "=", family.id)])).ids


    def write(self, vals):
        # A demo customer can be priced with demo tariffs: only a tariff approver decides who is one.
        if "boss_demo" in vals and not self.env.su and not self.env.user.has_group("boss_pricing.group_tariff_approver"):
            raise UserError(self.env._("Only a tariff approver can mark or unmark a demo customer."))
        return super().write(vals)

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

    def action_boss_ws_new_tariff(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "boss.tariff", "view_mode": "form",
                "views": [(False, "form")], "target": "current", "name": self.env._("New supplier tariff"),
                "context": {"default_partner_id": self.id}}

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
