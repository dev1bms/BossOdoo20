from . import models
from . import wizard

from .models.boss_service_period import seed_service_periods


def _boss_post_init(env):
    """BOSS services already installed are billed on performed quantities too (approved 23/10/2026, P32); the
    time-based services get their default periods."""
    env.cr.execute("UPDATE product_template SET purchase_method = 'receive' WHERE boss_pricing_mode IS NOT NULL")
    seed_service_periods(env)
