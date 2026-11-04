"""Group the legal entities of each shipping line, as MSC already is (Ángel 27/10/2026, ADR-009: the quotation names the
commercial carrier, its tariffs are those of any of its entities). The lines whose entities Odoo 17 keeps as separate
companies (read on Odoo 17 production, 04/11/2026: CMA CGM France and Ibérica, Maersk Line and Maersk Logistics Spain,
COSCO Spain and China, OOCL Spain and Hong Kong, two HMM agencies). Entities not in boss20 yet join the group when they
are created. A line with one entity (Hapag-Lloyd, ONE, Yang Ming, Evergreen) needs no group. Idempotent; an entity that
already has a group keeps it.
    dev/server_shell.sh load_carrier_groups.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
Partner = env["res.partner"].with_context(active_test=False)  # noqa: F821
GROUPS = {
    "CMA CGM": ["CMA CGM FRANCE", "CMA CGM IBERICA, S.A.U."],
    "Maersk": ["MAERSK LINE", "MAERSK  LOGISTICS & SERVICES SPAIN, S.L.U."],
    "COSCO Shipping Lines": ["COSCO SHIPPING LINES SPAIN S.A."],
    "OOCL (Orient Overseas Container Line)": ["OOCL - ORIENT OVERSEAS CONTAINER LINE (SPAIN) SL"],
    "HMM": ["HMM SPAIN SL - VALENCIA", "MARITIME AGENCY HMM SPAIN SL"],
}
for group_name, entities in GROUPS.items():
    group = Partner.search([("name", "=", group_name), ("parent_id", "=", False)], limit=1) or Partner.create(
        {"name": group_name, "is_company": True})
    for name in entities:
        entity = Partner.search([("name", "=", name), ("parent_id", "=", False)], limit=1)
        if not entity:
            print(f"MISSING {name}")
        elif entity.boss_carrier_group_id and entity.boss_carrier_group_id != group:
            print(f"KEPT {name}: already in {entity.boss_carrier_group_id.name}")
        elif not entity.boss_carrier_group_id:
            entity.boss_carrier_group_id = group
            print(f"GROUPED {name} -> {group_name}")
    print(f"GROUP {group.id} {group_name}: {len(Partner.search([('boss_carrier_group_id', '=', group.id)]))} entities")
env.cr.commit()  # noqa: F821
