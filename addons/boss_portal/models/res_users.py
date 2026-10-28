from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _boss_portal_scope(self):
        """(role, customer) of an active portal user as granted by BOSS, else (False, empty partner)."""
        self.ensure_one()
        user = self.sudo()
        nothing = (False, self.env["res.partner"])
        if not user.active or not user.share or user._is_public():
            return nothing
        partner = user.partner_id
        if not partner.boss_portal_scope_id:
            return nothing
        return partner.boss_portal_role, partner.boss_portal_scope_id

    def _boss_portal_can(self, action, customer):
        """Whether this portal user may do `action` («track», «prices», «accept», «book») for `customer`."""
        self.ensure_one()
        role, scope = self._boss_portal_scope()
        if not role or not customer or scope != customer.commercial_partner_id:
            return False
        allowed = {"track": ("tracking", "commercial", "approver"), "prices": ("commercial", "approver"),
                   "accept": ("approver",), "book": ("approver",)}
        return role in allowed[action]
