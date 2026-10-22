"""Local copy only: ids used by dev/shots_ux.json (read only)."""
assert env.cr.dbname == "boss_test", env.cr.dbname
T = env["boss.tariff"]
print("TARIFFS", [(t.id, t.name, t.state) for t in T.search([("name", "=like", "[DEMO]%")])])
print("ALM", env.ref("boss_services.service_alm").id, "THC", env.ref("boss_services.service_thc").id)
print("WFS", env["res.partner"].search([("name", "=", "WFS [DEMO]")]).id)
print("LINES", [(l.id, l.tariff_id.name[:25], l.product_id.default_code, l.container_size) for l in env["boss.tariff.line"].search([("tariff_id.name", "=like", "[DEMO] %2026")])][:20])
print("ORDERS", [(o.id, o.name, o.state, o.partner_id.name) for o in env["sale.order"].search([])])
print("LEADS", [(l.id, l.name[:40]) for l in env["crm.lead"].search([])])
