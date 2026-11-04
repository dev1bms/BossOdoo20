"""Plan after the meeting with Ángel (04/11/2026), phase B: FCL ocean freight is bought from the main carrier of the
shipment; the services that still say «any supplier» get the new seed once (a choice made on a service is kept)."""
from odoo import SUPERUSER_ID, api

from odoo.addons.boss_services.models.service_groups import seed_service_attributes


def migrate(cr, version):
    seed_service_attributes(api.Environment(cr, SUPERUSER_ID, {}))
