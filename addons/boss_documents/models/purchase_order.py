from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _boss_document_file(self):
        self.ensure_one()
        files = self.boss_expediente_id or self.order_line.boss_cost_id.expediente_id
        return files if len(files) == 1 else files.browse()

    def _boss_document_block(self):
        """The supplier gets the operational data of the file (route, references, containers, cargo), never the
        customer's prices nor the customer reference."""
        file = self._boss_document_file()
        if not file:
            return None
        block = file._boss_document_block()
        block["customer_reference"] = ""
        block["quotation"] = ""
        return block
