from odoo import fields, models

# Incoterms whose main carriage the seller pays (C and D terms): freight «prepaid» on the house document and for the
# margin rules; with the E and F terms the buyer pays it: «collect». The usual reading of the Incoterms 2020, kept on
# each incoterm since 04/11/2026 (settings study, phase 2) so that a new or special term needs no code.
PREPAID_INCOTERMS = ("CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP")
COLLECT_INCOTERMS = ("EXW", "FCA", "FAS", "FOB")
FREIGHT_PAYMENTS = [("prepaid", "Prepaid"), ("collect", "Collect")]


class AccountIncoterms(models.Model):
    _inherit = "account.incoterms"

    boss_freight_payment = fields.Selection(
        FREIGHT_PAYMENTS, "Freight", help="Who pays the main carriage under this term: the seller (prepaid, C and D "
                                          "terms) or the buyer (collect, E and F terms). Printed on the house B/L "
                                          "and used by the minimum margin rules.")


def seed_incoterm_freight(env):
    """Set prepaid / collect on the standard incoterms that have nothing yet (install or upgrade)."""
    for codes, value in ((PREPAID_INCOTERMS, "prepaid"), (COLLECT_INCOTERMS, "collect")):
        env["account.incoterms"].with_context(active_test=False).search(
            [("code", "in", codes), ("boss_freight_payment", "=", False)]).write({"boss_freight_payment": value})
