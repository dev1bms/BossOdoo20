"""Settings study of 04/11/2026, phase 2: the default periods of the time-based services (ALM, DEM, OCU, DET) were a
table in the code; they are lines on each service now, seeded once here."""
from odoo import SUPERUSER_ID, api

from odoo.addons.boss_expediente.models.boss_service_period import seed_service_periods


def migrate(cr, version):
    seed_service_periods(api.Environment(cr, SUPERUSER_ID, {}))
