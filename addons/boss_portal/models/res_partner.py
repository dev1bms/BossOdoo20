from odoo import api, fields, models
from odoo.exceptions import AccessError

# What a customer contact may do in the portal, granted by BOSS on the contact (ADR-010). Having a portal account,
# being a follower, the shipper, the consignee or another contact of the same company grants nothing by itself.
PORTAL_ROLES = [
    ("tracking", "Shipment tracking"),
    ("commercial", "Commercial: quotations, prices and invoices"),
    ("approver", "Authorised representative: accepts quotations, requests bookings"),
]
PORTAL_FIELDS = ("boss_portal_role", "boss_portal_customer_id")


class ResPartner(models.Model):
    _inherit = "res.partner"

    boss_portal_role = fields.Selection(
        PORTAL_ROLES, "BOSS portal role", copy=False, tracking=True,
        help="Granted by a BOSS sales manager. Tracking: My Shipments, published events and documents. Commercial: "
        "also the quotations, selling prices and invoices of the customer. Authorised representative: also accepts "
        "quotations and requests bookings. Empty: the portal account sees nothing of BOSS.")
    boss_portal_customer_id = fields.Many2one(
        "res.partner", "BOSS portal customer", copy=False, tracking=True, domain="[('is_company', '=', True)]",
        help="The legal entity whose records this contact sees. It must be the contact's own company: a contact of "
        "another company, or of a group company, gets nothing until BOSS decides how groups are handled.")
    # One stored value per kind of access, read by the access restrictions of the portal (security/ir.access.csv).
    boss_portal_scope_id = fields.Many2one(
        "res.partner", "Portal scope (any role)", compute="_compute_boss_portal_scope", store=True, index=True)
    boss_portal_sales_scope_id = fields.Many2one(
        "res.partner", "Portal scope (prices)", compute="_compute_boss_portal_scope", store=True, index=True)

    @api.depends("boss_portal_role", "boss_portal_customer_id", "commercial_partner_id")
    def _compute_boss_portal_scope(self):
        for partner in self:
            customer = partner.boss_portal_customer_id
            valid = partner.boss_portal_role and customer and partner.commercial_partner_id == customer
            partner.boss_portal_scope_id = customer if valid else False
            partner.boss_portal_sales_scope_id = (
                customer if valid and partner.boss_portal_role in ("commercial", "approver") else False)

    def _boss_check_portal_manager(self, vals):
        if set(vals) & set(PORTAL_FIELDS) and not self.env.su and not self.env.user.has_group(
                "sales_team.group_sale_manager"):
            raise AccessError(self.env._("Only a BOSS sales manager grants or changes portal roles."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._boss_check_portal_manager(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._boss_check_portal_manager(vals)
        return super().write(vals)
