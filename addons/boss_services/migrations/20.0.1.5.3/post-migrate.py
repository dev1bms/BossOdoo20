"""FTT (international road freight) counts for the customs value as freight: on a TER->PRO import its price is in the
import VAT base, so the sale is exempt (Art. 64 LIVA; Cristina, 04/11/2026). Only FTT, and only if still empty."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["product.template"].with_context(active_test=False).search(
        [("default_code", "=", "FTT"), ("boss_customs_value_charge", "=", False)]).write(
        {"boss_customs_value_charge": "freight"})
