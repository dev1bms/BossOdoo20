"""Read-only: supplier tariffs from real documents ([MUESTRA], not demo) for Cristina's review table. Prints no
amount (real prices stay out of Git and out of the docs). Rollback at the end."""
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, lang="es_ES"))  # noqa: F821
for t in env["boss.tariff"].search([("is_demo", "=", False), ("active", "=", True)], order="partner_id, name"):
    print(f"TARIFF {t.id} | {t.partner_id.name} | {t.name} | {t.state} | {t.valid_from} -> {t.valid_to or 'open'} | "
          f"{t.currency_id.name} | doc={t.document_reference or ''} / {t.document_name or ''} | "
          f"scope={t.scope_summary} | scope_confirmed={t.scope_confirmed} | version={t.version}")
    for l in t.line_ids:
        cond = [x for x in (l.container_size and f"{l.container_size}'",
                            ",".join(l.container_type_ids.mapped("code")) if l.container_type_ids else "",
                            l.period_unit and f"period={l.period_unit}", l.tier_mode and f"tiers={l.tier_mode}",
                            l.round_up and "or fraction", l.round_undecided and "fraction UNDECIDED",
                            l.free_hours and f"free {l.free_hours}h", l.free_days and f"free {l.free_days}d",
                            l.min_per_day and "min per day", l.on_request and "on request") if x]
        print(f"   {l.product_id.default_code:8} | {l.uom_id.name} | {l.method} | p.{l.document_page or '-'} | "
              f"{'; '.join(cond)} | {l.note or ''}")
env.cr.rollback()  # noqa: F821
