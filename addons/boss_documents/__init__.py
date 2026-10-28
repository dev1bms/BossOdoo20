from . import models
from .models.document_layout import apply_boss_layout


def _boss_post_init(env):
    """Give every company without a document layout the BOSS one (ADR-011). A layout already chosen is kept."""
    apply_boss_layout(env["res.company"].search([]))
