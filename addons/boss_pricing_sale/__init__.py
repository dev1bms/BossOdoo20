from . import models
from . import wizard

from .models.account_incoterms import seed_incoterm_freight


def _boss_post_init(env):
    seed_incoterm_freight(env)
