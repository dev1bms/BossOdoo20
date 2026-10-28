from markupsafe import Markup

from odoo import fields, models
from odoo.exceptions import UserError

BOOKING_STATES = [("requested", "Requested by the customer"), ("handled", "Handled by BOSS")]
MAX_CONTAINERS_PER_LINE = 99


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Booking request of a rate quotation, sent from the portal by an authorised representative (ADR-010). It is a
    # request reviewed by BOSS: it never confirms the quotation, opens a file, invoices or asks for a payment.
    boss_booking_state = fields.Selection(BOOKING_STATES, "Booking request", copy=False, readonly=True, tracking=True)
    boss_booking_requested_on = fields.Datetime("Booking requested on", copy=False, readonly=True)
    boss_booking_requested_by = fields.Many2one("res.users", "Booking requested by", copy=False, readonly=True)
    boss_booking_summary = fields.Text("Booking requested", copy=False, readonly=True)
    boss_booking_lines = fields.Json("Booking request lines", copy=False, readonly=True, groups="base.group_user")

    # --- who may accept, sign or pay from the portal -----------------------------------------------------------------

    def _boss_portal_viewer_allowed(self):
        """In a portal request (the controller sets the viewer), only an internal user or an authorised
        representative of this customer may sign, accept or pay; a token link or another role only views."""
        self.ensure_one()
        uid = self.env.context.get("boss_portal_viewer_uid")
        if uid is None:
            return True  # back-office or code: the standard rules apply
        viewer = self.env["res.users"].sudo().browse(uid)
        if viewer.exists() and not viewer.share:
            return True
        return bool(viewer.exists()) and viewer._boss_portal_can("accept", self.partner_id)

    def _has_to_be_signed(self):
        # a rate quotation is a list of unit rates: there is nothing to sign until the shipment is known
        return super()._has_to_be_signed() and not self.boss_rate_quotation and self._boss_portal_viewer_allowed()

    def _has_to_be_paid(self):
        return super()._has_to_be_paid() and not self.boss_rate_quotation and self._boss_portal_viewer_allowed()

    def _get_name_portal_content_view(self):
        if self.boss_rate_quotation:
            return "boss_portal.sale_order_portal_content_rate"
        return super()._get_name_portal_content_view()

    def _find_mail_template(self):
        """A rate quotation is sent with its own e-mail: no amount, only the rates are ready (ADR-010)."""
        if self.boss_rate_quotation and self.state != "sale" and not self.env.context.get("proforma"):
            template = self.env.ref("boss_portal.email_template_rate_quotation", raise_if_not_found=False)
            if template:
                return template
        return super()._find_mail_template()

    # --- booking request -----------------------------------------------------------------------------------------------

    def _boss_booking_lines_available(self):
        """The rates a customer can book: per-container services with their size (20' DV, 40' HC...)."""
        self.ensure_one()
        return self.order_line.filtered(
            lambda l: not l.display_type and l.product_id.boss_pricing_mode and l.boss_container_size
            and l.product_uom_id.boss_quantity_source in ("container", "teu"))

    def _boss_booking_blockers(self, user):
        """Why `user` cannot request a booking of this quotation now (empty list: he can)."""
        self.ensure_one()
        _ = self.env._
        problems = []
        if not user._boss_portal_can("book", self.partner_id):
            problems.append(_("Only an authorised representative of %s can request a booking.",
                              self.partner_id.commercial_partner_id.name))
        if not self.boss_rate_quotation or self.state not in ("draft", "sent"):
            problems.append(_("This quotation is not an open rate quotation."))
        if self.validity_date and self.validity_date < fields.Date.context_today(self):
            problems.append(_("The rates expired on %s: ask BOSS for new rates.", self.validity_date))
        if self.boss_booking_state == "requested":
            problems.append(_("A booking request is already pending BOSS review."))
        if not self._boss_booking_lines_available():
            problems.append(_("This quotation has no per-container rate to book."))
        return problems

    def _boss_portal_request_booking(self, user, quantities, note=""):
        """Record a booking request from the portal: `quantities` = {sale line id: number of containers}. Checked
        here, never trusted from the browser: the lines must belong to this quotation and be bookable rates; the
        price, currency and taxes are those of the quotation and cannot be sent. Notifies the salesperson."""
        self.ensure_one()
        _ = self.env._
        problems = self._boss_booking_blockers(user)
        if problems:
            raise UserError("\n".join(problems))
        lines = self._boss_booking_lines_available()
        chosen = []
        for line_id, quantity in quantities.items():
            line = lines.filtered(lambda l, i=line_id: l.id == i)
            if not line:
                raise UserError(_("The selection does not match the rates of this quotation."))
            if not isinstance(quantity, int) or quantity < 0 or quantity > MAX_CONTAINERS_PER_LINE:
                raise UserError(_("Enter a whole number of containers between 0 and %s.", MAX_CONTAINERS_PER_LINE))
            if quantity:
                chosen.append((line, quantity))
        if not chosen:
            raise UserError(_("Enter the number of containers of at least one rate."))
        note = (note or "").strip()[:500]
        rows = [{"line_id": line.id, "product": line.product_id.default_code or line.product_id.name,
                 "size": line.boss_container_size, "type": line.boss_container_type_id.code or "",
                 "quantity": quantity} for line, quantity in chosen]
        summary = "\n".join(f"{r['quantity']} x {r['size']}' {r['type']}: {r['product']}".replace("  ", " ")
                            for r in rows)
        if note:
            summary += "\n" + _("Customer note: %s", note)
        self.write({"boss_booking_state": "requested", "boss_booking_requested_on": fields.Datetime.now(),
                    "boss_booking_requested_by": user.id, "boss_booking_summary": summary,
                    "boss_booking_lines": rows})
        body = Markup("<p>%s</p><pre>%s</pre>") % (
            _("Booking request from the portal by %s (to review: containers, then accept the quotation with them).",
              user.partner_id.name), summary)
        self.message_post(body=body, author_id=user.partner_id.id, subtype_xmlid="mail.mt_note")
        self.activity_schedule("mail.mail_activity_data_todo", user_id=(self.user_id or self.env.user).id,
                               summary=_("Booking request from %s", user.partner_id.name), note=summary)
        return rows

    def action_boss_booking_handled(self):
        self.filtered(lambda o: o.boss_booking_state == "requested").write({"boss_booking_state": "handled"})

    def action_confirm(self):
        res = super().action_confirm()
        self.filtered(lambda o: o.boss_booking_state == "requested").write({"boss_booking_state": "handled"})
        return res
