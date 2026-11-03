from odoo import models
from odoo.exceptions import UserError

from .shipment_block import scope_sentence, shipment_rows


class BossExpediente(models.Model):
    _inherit = "boss.expediente"

    def _boss_document_block(self):
        """Data of the shipment block of a document of this file (ADR-011)."""
        self.ensure_one()
        order = self._boss_document_order()
        return {
            "reference": self.name,
            "customer_reference": order.client_order_ref if order else "",
            "quotation": order.name if order else "",
            "scope": scope_sentence(self),
            "columns": shipment_rows(self, "", file=self),
        }

    def _boss_document_order(self):
        """The accepted quotation of the file (the first one when several)."""
        orders = self.sale_order_ids.filtered(lambda o: o.state == "sale") or self.sale_order_ids
        return orders[:1]

    # --- transport order (OT) to the haulier (roadmap item 5) ----------------------------------------------------

    def _boss_transport_order_problems(self):
        """What stops the transport order: the haulier it goes to, and on a sea import delivered by BOSS the house B/L
        released or a sea waybill (Cristina, «Nuevo Odoo» › OPS- exptes A73: «before delivering, the operator confirms
        that the HBL is released or SWB»)."""
        self.ensure_one()
        _ = self.env._
        problems = [] if self.haulier_id else [_("choose the haulier (References and dates › Other parties)")]
        if (self.direction == "import" and self.transport_mode == "sea" and self.scope_delivery
                and self.hbl_release not in ("released", "swb")):
            problems.append(_("the house B/L is not released nor a sea waybill (References and dates)"))
        return problems

    def action_print_transport_order(self):
        """The transport order PDF for the haulier: the shipment block of the supplier documents (no customer price or
        reference), the containers and the pickup and delivery. Printed, never sent from here."""
        self.ensure_one()
        problems = self._boss_transport_order_problems()
        if problems:
            raise UserError(self.env._("No transport order for %(file)s yet: %(problems)s.", file=self.name,
                                       problems="; ".join(problems)))
        return self.env.ref("boss_documents.action_report_transport_order").report_action(self)

    def _boss_transport_order_block(self):
        """The shipment block as a supplier sees it (purchase order): operational data only."""
        block = self._boss_document_block()
        block.update(customer_reference="", quotation="")
        return block
