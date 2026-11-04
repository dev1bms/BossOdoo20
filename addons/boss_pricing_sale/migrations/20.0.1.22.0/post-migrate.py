"""Settings study of 04/11/2026, phase 2: prepaid / collect was a list of incoterm codes in the code; it is a field of
each incoterm now, seeded once here."""
from odoo import SUPERUSER_ID, api

from odoo.addons.boss_pricing_sale.models.account_incoterms import seed_incoterm_freight


def migrate(cr, version):
    seed_incoterm_freight(api.Environment(cr, SUPERUSER_ID, {}))
