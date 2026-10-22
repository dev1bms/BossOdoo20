from odoo import api, fields, models

ZONES = [
    ("any", "Any customer zone"),
    ("PRO", "PRO - mainland Spain and Balearics"),
    ("CAN", "CAN - Canary Islands"),
    ("COM", "COM - rest of the EU"),
    ("TER", "TER - third countries"),
]
SERVICE_KINDS = [("any", "Any service"), ("paid_on_behalf", "Paid on behalf"), ("other", "Other services")]


class BossVatTax(models.Model):
    """Odoo tax of each BOSS VAT case (ADR-004). Ángel's rules give the class of a line (NS / EX / NR); the tax
    also depends on the customer zone (EU, third country...) and on whether the amount is paid on behalf. A case
    without a row stays 'VAT pending': the quotation is not sent or accepted until it is decided."""

    _name = "boss.vat.tax"
    _description = "Odoo tax of a BOSS VAT case"
    _order = "vat_class, customer_zone, service_kind"

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    vat_class = fields.Selection([("NS", "NS - not subject"), ("EX", "EX - exempt"), ("NR", "NR - carries VAT")],
                                 "VAT class", required=True)
    customer_zone = fields.Selection(ZONES, required=True, default="any")
    service_kind = fields.Selection(SERVICE_KINDS, "Services", required=True, default="any")
    tax_id = fields.Many2one("account.tax", "Odoo tax", required=True, check_company=True,
                             domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]")
    source = fields.Char(help="Where the rule comes from: decision, minutes, Odoo 17 configuration.")

    _case_unique = models.Constraint(
        "UNIQUE(company_id, vat_class, customer_zone, service_kind)",
        "There is already a tax for this VAT class, customer zone and kind of service.")

    @api.model
    def _boss_find(self, company, vat_class, customer_zone, paid_on_behalf):
        """The most specific row for the case, or an empty recordset (VAT pending)."""
        kind = "paid_on_behalf" if paid_on_behalf else "other"
        rows = self.sudo().search([
            ("company_id", "=", company.id), ("vat_class", "=", vat_class),
            ("customer_zone", "in", ["any"] + ([customer_zone] if customer_zone else [])),
            ("service_kind", "in", ["any", kind]),
        ])
        return rows.sorted(lambda r: (r.service_kind == "any", r.customer_zone == "any"))[:1]

    def _boss_refresh_quotations(self, companies):
        """Open quotations follow a change of the table at once; accepted (frozen) ones never change."""
        lines = self.env["sale.order.line"].sudo().search([
            ("company_id", "in", companies.ids), ("boss_price_frozen", "=", False),
            ("order_id.state", "in", ("draft", "sent")), ("product_id.boss_pricing_mode", "!=", False),
        ])
        lines._boss_recompute_vat()

    @api.model_create_multi
    def create(self, vals_list):
        rows = super().create(vals_list)
        self._boss_refresh_quotations(rows.company_id)
        return rows

    def write(self, vals):
        companies = self.company_id
        res = super().write(vals)
        self._boss_refresh_quotations(companies | self.company_id)
        return res

    def unlink(self):
        companies = self.company_id
        res = super().unlink()
        self._boss_refresh_quotations(companies)
        return res
