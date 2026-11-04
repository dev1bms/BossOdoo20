"""Settings study of 04/11/2026, phase 2: the services bought from the handler or the haulier and the charges of the
customs value were lists in the code; they are attributes of the service now, seeded once here."""
from odoo import SUPERUSER_ID, api

from odoo.addons.boss_services.models.service_groups import seed_service_attributes


def migrate(cr, version):
    seed_service_attributes(api.Environment(cr, SUPERUSER_ID, {}))
