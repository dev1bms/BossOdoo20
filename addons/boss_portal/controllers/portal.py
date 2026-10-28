from urllib.parse import quote

from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.http import request

from odoo.addons.sale.controllers.portal import CustomerPortal


class BossCustomerPortal(CustomerPortal):
    """BOSS customer portal (ADR-010). Every page checks the user's role and customer first, then reads the records
    as superuser and sends only the whitelisted values of _boss_portal_values: never a record or a read() result."""

    # --- who is asking -------------------------------------------------------------------------------------------------

    def _boss_scope(self):
        user = request.env.user
        return user._boss_portal_scope() if user.share else (False, request.env["res.partner"])

    def _boss_files_domain(self, customer):
        return [("partner_id", "=", customer.id), ("state", "!=", "cancel")] if customer else [("id", "=", 0)]

    def _boss_file_or_404(self, file_id):
        role, customer = self._boss_scope()
        if not role:
            raise request.not_found()
        file = request.env["boss.expediente"].sudo().search(
            [("id", "=", file_id)] + self._boss_files_domain(customer), limit=1)
        if not file:
            raise request.not_found()
        return file

    # --- portal home -------------------------------------------------------------------------------------------------

    def _prepare_portal_counter_values(self, counter):
        if counter == "boss_shipment_count":
            role, customer = self._boss_scope()
            return "boss.expediente", self._boss_files_domain(customer if role else None), "sudo"
        return super()._prepare_portal_counter_values(counter)

    # --- quotations: who may sign, accept or pay ---------------------------------------------------------------------

    def _document_check_access(self, model_name, document_id, access_token=None):
        document_sudo = super()._document_check_access(model_name, document_id, access_token=access_token)
        if model_name == "sale.order":
            # the order knows who is looking: a token link or a role other than authorised representative only views
            document_sudo = document_sudo.with_context(boss_portal_viewer_uid=request.env.uid)
        return document_sudo

    @http.route("/my/orders/<int:order_id>/transaction", type="jsonrpc", auth="public")
    def portal_order_transaction(self, order_id, access_token, **kwargs):
        try:
            order_sudo = self._document_check_access("sale.order", order_id, access_token)
        except MissingError:
            raise
        except AccessError:
            raise ValidationError(request.env._("The access token is invalid.")) from None
        if order_sudo.boss_rate_quotation or not order_sudo._boss_portal_viewer_allowed():
            raise ValidationError(request.env._(
                "This order cannot be paid from here: an authorised representative of the customer pays it."))
        return super().portal_order_transaction(order_id, access_token, **kwargs)

    @http.route(["/my/orders/<int:order_id>/boss_booking"], type="http", auth="user", methods=["POST"], website=True)
    def boss_booking_request(self, order_id, **post):
        order = request.env["sale.order"].sudo().browse(order_id).exists()
        if not order or not request.env.user._boss_portal_can("track", order.partner_id):
            raise request.not_found()
        quantities = {}
        try:
            for key, value in post.items():
                if key.startswith("qty_") and str(value).strip():
                    quantities[int(key[4:])] = int(str(value).strip())
            order._boss_portal_request_booking(request.env.user, quantities, post.get("note", ""))
        except (ValueError, UserError) as error:
            message = str(error) if isinstance(error, UserError) else request.env._("Enter whole numbers.")
            return request.redirect(order.get_portal_url(query_string="&boss_booking_error=" + quote(message[:300])))
        return request.redirect(order.get_portal_url(query_string="&boss_booking=sent"))

    # --- My Shipments --------------------------------------------------------------------------------------------------

    @http.route(["/my/shipments"], type="http", auth="user", website=True)
    def boss_my_shipments(self, **kw):
        role, customer = self._boss_scope()
        files = request.env["boss.expediente"].sudo().search(
            self._boss_files_domain(customer if role else None), order="create_date desc", limit=200)
        values = self._prepare_portal_layout_values()
        values.update({"page_name": "boss_shipments", "shipments": [f._boss_portal_values("account") for f in files],
                       "boss_role": role})
        return request.render("boss_portal.portal_my_shipments", values)

    @http.route(["/my/shipments/<int:file_id>"], type="http", auth="user", website=True)
    def boss_my_shipment(self, file_id, **kw):
        file = self._boss_file_or_404(file_id)
        values = self._prepare_portal_layout_values()
        values.update({"page_name": "boss_shipment", "shipment": file._boss_portal_values("account")})
        return request.render("boss_portal.portal_my_shipment", values)

    @http.route(["/my/shipments/<int:file_id>/documents/<int:attachment_id>"], type="http", auth="user")
    def boss_my_shipment_document(self, file_id, attachment_id, **kw):
        file = self._boss_file_or_404(file_id)
        attachment = file.portal_attachment_ids.filtered(lambda a: a.id == attachment_id)
        if not attachment or attachment.res_model != "boss.expediente" or attachment.res_id != file.id:
            raise request.not_found()
        return request.env["ir.binary"]._get_stream_from(attachment.sudo()).get_response(as_attachment=True)

    # --- tracking link (no login) ------------------------------------------------------------------------------------

    @http.route(["/boss/track/<string:token>"], type="http", auth="public", website=True, sitemap=False)
    def boss_track(self, token, **kw):
        file = request.env["boss.expediente"]._boss_find_by_tracking_token(token)
        if not file:
            raise request.not_found()
        return request.render("boss_portal.portal_public_tracking", {"shipment": file._boss_portal_values("public")})
