from odoo import models

from .shipment_block import scope_sentence, shipment_rows


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _boss_document_block(self):
        """Shipment block of the quotation / order document: from the file once it exists (actual data), otherwise
        from the shipment data typed on the quotation. None for an order without BOSS shipment data."""
        self.ensure_one()
        if self.boss_expediente_id:
            block = self.boss_expediente_id._boss_document_block()
            block["customer_reference"] = self.client_order_ref or block["customer_reference"]
            return block
        if not (self.boss_transport_mode or self.boss_direction or self.boss_origin_country_id
                or self.boss_destination_country_id):
            return None
        return {
            "reference": "",
            "customer_reference": self.client_order_ref or "",
            "quotation": "",
            "scope": scope_sentence(self, "boss_"),
            "columns": shipment_rows(self, "boss_"),
        }
