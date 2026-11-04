from . import models

from .models.service_groups import assign_service_groups, seed_service_attributes


def _boss_post_init(env):
    assign_service_groups(env)
    seed_service_attributes(env)
