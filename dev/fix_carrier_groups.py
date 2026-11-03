"""Roadmap item 9 (boss20, commits): a commercial carrier named by legal entities (boss_carrier_group_id, e.g.
Mediterranean Shipping Company (MSC)) is a company, so the «Main carrier» field, limited to companies, offers it when
«MSC» is typed. Idempotent; prints the groups it changes.
    dev/server_shell.sh fix_carrier_groups.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
Partner = env["res.partner"]  # noqa: F821
groups = Partner.search([("boss_carrier_group_id", "!=", False)]).boss_carrier_group_id
for group in groups.filtered(lambda p: not p.is_company):
    group.is_company = True
    print("CARRIER GROUP now a company:", group.id, group.name)
env.cr.commit()  # noqa: F821
print("DONE", len(groups), "carrier groups")
