from . import models
from . import wizard


def _boss_post_init(env):
    """BOSS services already installed are billed on performed quantities too (approved 23/10/2026, P32)."""
    env.cr.execute("UPDATE product_template SET purchase_method = 'receive' WHERE boss_pricing_mode IS NOT NULL")
