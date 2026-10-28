"""Service groups of the file summary and the tariff date of the freight services (meeting of 27/10/2026, part 2)."""
from odoo import SUPERUSER_ID, api

from odoo.addons.boss_services.models.service_groups import assign_service_groups


def migrate(cr, version):
    assign_service_groups(api.Environment(cr, SUPERUSER_ID, {}))
