import secrets

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import consteq

STATE_LABELS = {"open": "Booked", "in_transit": "In transit", "delivered": "Delivered", "closed": "Delivered",
                "cancel": "Cancelled"}


class BossExpediente(models.Model):
    _inherit = "boss.expediente"

    # What the customer sees of a file is chosen by BOSS: published events and documents, and a tracking link that
    # can be revoked (ADR-010). Nothing else of the file is sent to the browser (see _boss_portal_values).
    portal_tracking_token = fields.Char("Tracking link token", copy=False, readonly=True, index="btree_not_null",
                                        groups="base.group_user")
    portal_tracking_url = fields.Char("Tracking link", compute="_compute_portal_tracking_url", groups="base.group_user")
    portal_attachment_ids = fields.Many2many(
        "ir.attachment", "boss_expediente_portal_attachment_rel", "expediente_id", "attachment_id",
        string="Documents published to the customer", copy=False,
        domain="[('res_model', '=', 'boss.expediente'), ('res_id', '=', id)]",
        help="Only these documents reach the customer's portal (never the whole chatter). A master document may "
        "contain other customers' data: publish it only when it is this customer's.")

    @api.depends("portal_tracking_token")
    def _compute_portal_tracking_url(self):
        for file in self:  # Odoo 20: get_base_url() (ir.config_parameter has get_str, no get_param)
            file.portal_tracking_url = f"{file.get_base_url()}/boss/track/{file.portal_tracking_token}" \
                if file.portal_tracking_token else False

    @api.constrains("portal_attachment_ids")
    def _check_portal_attachments(self):
        for file in self:
            alien = file.portal_attachment_ids.filtered(
                lambda a: a.res_model != "boss.expediente" or a.res_id != file.id)
            if alien:
                raise ValidationError(self.env._("%(file)s can only publish its own documents (%(names)s).",
                                                 file=file.name, names=", ".join(alien.mapped("name"))))

    def action_boss_share_tracking(self):
        """A new link each time: an earlier one stops working."""
        for file in self:
            file.portal_tracking_token = secrets.token_urlsafe(24)
            file.message_post(body=self.env._("Tracking link created (an earlier link no longer works)."))

    def action_boss_revoke_tracking(self):
        for file in self.filtered("portal_tracking_token"):
            file.portal_tracking_token = False
            file.message_post(body=self.env._("Tracking link revoked."))

    @api.model
    def _boss_find_by_tracking_token(self, token):
        if not token or len(token) < 20:
            return self.browse()
        file = self.sudo().search([("portal_tracking_token", "=", token), ("state", "!=", "cancel")], limit=1)
        return file if file and consteq(file.portal_tracking_token, token) else self.browse()

    def _boss_portal_values(self, level):
        """The whitelist of what leaves BOSS for a shipment. `level`: «account» (the customer's own portal) or
        «public» (tracking link: no parties, no references of other documents, no container numbers, no
        documents). Estimated and actual dates are kept apart; an unknown value is None, never a guess."""
        self.ensure_one()
        file = self.sudo()

        def port(record):
            return {"code": record.code, "name": record.name} if record else None

        def date(value):
            return fields.Date.to_date(value) if value else None

        containers = {}
        for container in file.container_ids:
            key = f"{container.size}' {container.container_type_id.code or ''}".strip()
            containers[key] = containers.get(key, 0) + 1
        events = file.event_ids.filtered("portal_published").sorted("date", reverse=True)
        values = {
            "reference": file.name,
            "state": STATE_LABELS.get(file.state, file.state),
            "transport_mode": dict(file._fields["transport_mode"]._description_selection(self.env)).get(
                file.transport_mode) if file.transport_mode else None,
            "load_type": dict(file._fields["load_type"]._description_selection(self.env)).get(
                file.load_type) if file.load_type else None,
            "origin_port": port(file.origin_port_id), "destination_port": port(file.destination_port_id),
            "origin_country": file.origin_country_id.name or None,
            "destination_country": file.destination_country_id.name or None,
            "etd": date(file.etd), "eta": date(file.eta),
            "atd": file.atd or None, "ata": file.ata or None, "delivered": file.delivery_date or None,
            "containers": sorted(containers.items()),
            "events": [{"date": e.date, "kind": e.kind, "text": e.portal_text} for e in events],
            "last_update": events[:1].date or None,
        }
        if level == "account":
            order = file.sale_order_ids.filtered(lambda o: o.state == "sale").sorted("date_order")[:1]
            values.update({
                "id": file.id,
                "customer_reference": order.client_order_ref or None,
                "carrier": file.carrier_id._boss_carrier_family().name if file.carrier_id else None,
                "vessel": file.vessel or None, "voyage": file.voyage or None,
                "house_reference": file.hbl_ref or file.hawb_ref or None,
                "container_numbers": [{"number": c.number, "size": c.size, "type": c.container_type_id.code or ""}
                                      for c in file.container_ids if c.number],
                "documents": [{"id": a.id, "name": a.name} for a in file.portal_attachment_ids],
            })
        return values


class BossExpedienteEvent(models.Model):
    _inherit = "boss.expediente.event"

    # An event reaches the customer only when BOSS publishes it, with a text written for the customer; the internal
    # note never leaves BOSS and events recorded before this module stay internal (ADR-010).
    portal_published = fields.Boolean("Published to the customer", copy=False)
    portal_text = fields.Char("Text for the customer", help="What the customer reads. The internal note is never shown.")

    @api.constrains("portal_published", "portal_text")
    def _check_portal_text(self):
        for event in self.filtered("portal_published"):
            if not (event.portal_text or "").strip():
                raise ValidationError(self.env._("Write the text for the customer before publishing «%s».", event.name))
