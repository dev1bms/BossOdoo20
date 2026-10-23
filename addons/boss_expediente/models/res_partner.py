from odoo import api, fields, models


class BossPartnerRole(models.Model):
    """Logistic role of a party. Controlled values (not free tags): files and searches rely on them."""

    _name = "boss.partner.role"
    _description = "Logistic role of a contact"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint("UNIQUE(code)", "The code of a logistic role must be unique.")


class ResPartner(models.Model):
    _inherit = "res.partner"

    # One contact per party (ADR-005). Customer / supplier are the standard ranks, set at once by these switches so a
    # new party is listed in Customers or Vendors before its first document.
    boss_is_customer = fields.Boolean(
        "Customer", compute="_compute_boss_is_customer", inverse="_inverse_boss_is_customer",
        search="_search_boss_is_customer", help="Listed in Customers. Set automatically by its first sale or invoice.")
    boss_is_supplier = fields.Boolean(
        "Supplier", compute="_compute_boss_is_supplier", inverse="_inverse_boss_is_supplier",
        search="_search_boss_is_supplier", help="Listed in Vendors. Set automatically by its first purchase or bill.")
    boss_role_ids = fields.Many2many(
        "boss.partner.role", string="Logistic roles",
        help="Roles this party plays in shipments (shipper, consignee, agent, carrier, haulier...).")
    boss_eori = fields.Char("EORI", help="Economic Operators Registration and Identification number (customs).")
    boss_contact_purpose = fields.Selection(
        [("commercial", "Commercial"), ("operations", "Operations"), ("accounting", "Accounting")], "Contact for",
        help="What this person is contacted for.")
    boss_missing_data = fields.Char("Missing data", compute="_compute_boss_missing_data")

    @api.depends("customer_rank")
    def _compute_boss_is_customer(self):
        for partner in self:
            partner.boss_is_customer = partner.customer_rank > 0

    def _inverse_boss_is_customer(self):
        for partner in self:
            partner.customer_rank = max(partner.customer_rank, 1) if partner.boss_is_customer else 0

    def _search_boss_is_customer(self, operator, value):
        if operator not in ("=", "!="):
            return NotImplemented
        positive = (operator == "=") == bool(value)
        return [("customer_rank", ">" if positive else "=", 0)]

    @api.depends("supplier_rank")
    def _compute_boss_is_supplier(self):
        for partner in self:
            partner.boss_is_supplier = partner.supplier_rank > 0

    def _inverse_boss_is_supplier(self):
        for partner in self:
            partner.supplier_rank = max(partner.supplier_rank, 1) if partner.boss_is_supplier else 0

    def _search_boss_is_supplier(self, operator, value):
        if operator not in ("=", "!="):
            return NotImplemented
        positive = (operator == "=") == bool(value)
        return [("supplier_rank", ">" if positive else "=", 0)]

    def _boss_invoice_missing(self):
        """Recipient data a complete Spanish invoice to a business needs (RD 1619/2012, art. 6): tax ID and address.
        BOSS invoices businesses; a preliminary contact may lack them until its first invoice is posted."""
        self.ensure_one()
        partner = self.commercial_partner_id
        _ = self.env._
        missing = []
        if not partner.vat:
            missing.append(_("tax ID"))
        if not (partner.street and partner.city and partner.country_id):
            missing.append(_("address (street, city, country)"))
        return missing

    @api.depends("is_company", "vat", "street", "city", "country_id", "email", "customer_rank", "supplier_rank",
                 "parent_id")
    def _compute_boss_missing_data(self):
        _ = self.env._
        for partner in self:
            commercial = partner.commercial_partner_id
            missing = []
            if commercial.customer_rank or commercial.supplier_rank:
                missing = commercial._boss_invoice_missing()
                if not commercial.email and not commercial.child_ids.filtered("email"):
                    missing.append(_("email"))
            partner.boss_missing_data = ", ".join(missing) or False
