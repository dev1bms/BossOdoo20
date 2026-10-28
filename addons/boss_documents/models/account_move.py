from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _boss_document_file(self):
        """The file of this invoice, credit note or bill: the single file of its lines (an invoice that mixes files
        prints the file on each line instead of one block)."""
        self.ensure_one()
        files = self.invoice_line_ids.boss_expediente_id
        return files if len(files) == 1 else files.browse()

    def _boss_document_block(self):
        file = self._boss_document_file()
        if not file:
            return None
        block = file._boss_document_block()
        if self.ref:
            block["customer_reference"] = self.ref
        return block
