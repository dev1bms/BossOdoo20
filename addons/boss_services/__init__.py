from . import models

from .models.service_groups import assign_service_groups


def _boss_post_init(env):
    assign_service_groups(env)
