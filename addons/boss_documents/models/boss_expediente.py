from odoo import models

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
