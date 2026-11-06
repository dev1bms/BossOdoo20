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
    boss_customs_mode = fields.Selection(
        [("boss", "BOSS clears (its customs broker)"), ("customer", "Customer's own broker"), ("none", "No customs")],
        "Customs handled by", default="boss",
        help="How this customer's declarations are presented; copied to each new file (P4-08).")
    boss_invoice_grouping = fields.Selection(
        [("file", "One invoice per file"), ("grouped", "Several files on one invoice (periodic)")],
        "Customer invoicing", default="file",
        help="One invoice per file by default (F0-C59). «Several files on one invoice»: the customer receives a "
             "periodic invoice that groups its files (as Leroy Merlin in Odoo 17): the files are invoiced together "
             "from the list of files (Actions › Invoice files together), one section per file.")
    boss_customs_authorisation = fields.Char(
        "Customs authorisation", help="Reference of the customs representation authorisation given to BOSS's broker "
                                      "(or the customer's own authorised economic operator status).")
    boss_mobile = fields.Char("Mobile", help="Mobile phone kept apart from the phone (Odoo 20 has one phone field; migrated from the Odoo 17 mobile, F2).")
    boss_contact_purpose = fields.Selection(
        [("commercial", "Commercial"), ("operations", "Operations"), ("accounting", "Accounting")], "Contact for",
        help="What this person is contacted for.")
    boss_missing_data = fields.Char("Missing data", compute="_compute_boss_missing_data")
    boss_rating_ids = fields.One2many("boss.expediente.rating", "partner_id", "File ratings")
    boss_rating_avg = fields.Float(
        "Rating", digits=(3, 1), compute="_compute_boss_rating", store=True,
        help="Average of the ratings (0-10) given on its files, as customer or supplier (F0-C66).")
    boss_rating_count = fields.Integer("Ratings", compute="_compute_boss_rating", store=True)

    @api.depends("boss_rating_ids.rating")
    def _compute_boss_rating(self):
        for partner in self:
            values = [int(r.rating) for r in partner.boss_rating_ids if r.rating]
            partner.boss_rating_count = len(values)
            partner.boss_rating_avg = sum(values) / len(values) if values else 0.0

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

    def _boss_has_invoice_identification(self):
        """A customer in Spain (or without country) is identified by its NIF or another identification document, as
        the Spanish localization reads it; Odoo 17 refused to invoice such a customer without NIF. Foreign customers
        are not checked here: an EU business customer without VAT number already leaves the VAT pending."""
        self.ensure_one()
        partner = self.commercial_partner_id
        if partner.country_id and partner.country_id.code != "ES":
            return True
        if hasattr(partner, "_l10n_es_has_identification"):
            return partner._l10n_es_has_identification()
        return bool(partner.vat)

    def _boss_invoice_missing(self):
        """What a complete invoice to this customer lacks: identification (blocks posting in Spain) and address
        (shown, not blocking: no decision requires it)."""
        self.ensure_one()
        partner = self.commercial_partner_id
        _ = self.env._
        missing = []
        if not partner._boss_has_invoice_identification():
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
