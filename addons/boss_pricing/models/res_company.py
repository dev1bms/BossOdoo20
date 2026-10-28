from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Governance switches of the supplier prices (Ángel, meeting of 27/10/2026, part 2). Both are company policy
    # shown in Sales › Settings; the defaults follow what was said in the meeting and can be changed there.
    boss_tariff_document_required = fields.Boolean(
        "Supplier document required to send a tariff for approval", default=True,
        help="Every price is traceable to the supplier's document (ADR-002). Ángel asked whether attaching it must "
        "be compulsory (to confirm with Cristina): switch it off to send and approve tariffs without the file.")
    boss_spot_rate_auto_approve = fields.Boolean(
        "Freight rates entered from a quotation are approved on entry", default=True,
        help="A weekly freight rate typed from the quotation (ocean or air freight, valid for days) is approved at "
        "once by the person who enters it, so an urgent quotation never waits for an approver in another time zone "
        "(Ángel, 27/10/2026). Off: the rate waits for a tariff approver like any other supplier price.")
