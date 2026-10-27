"""ADR-006: existing quotations get their origin/destination and ETD/ETA from the pricing inputs they already had
(Spanish port, country abroad, planned date). Plain SQL: the pricing inputs do not change, so no cost is recomputed
and accepted quotations stay exactly as accepted. Draft quotations get the storage estimate «0 days, indicated»."""
from odoo import SUPERUSER_ID, api

ROUTE = """
    UPDATE {table} t
       SET boss_{spain}_port_id = t.boss_port_id,
           boss_{spain}_country_id = COALESCE((SELECT country_id FROM boss_port WHERE id = t.boss_port_id),
                                              (SELECT id FROM res_country WHERE code = 'ES')),
           boss_{abroad}_country_id = t.boss_country_id
     WHERE t.boss_direction = %s
       AND t.boss_origin_country_id IS NULL AND t.boss_origin_port_id IS NULL
       AND t.boss_destination_country_id IS NULL AND t.boss_destination_port_id IS NULL
       AND (t.boss_port_id IS NOT NULL OR t.boss_country_id IS NOT NULL)
"""
DATES = """
    UPDATE {table}
       SET boss_eta = CASE WHEN boss_direction = 'export' THEN boss_eta ELSE boss_planned_date END,
           boss_etd = CASE WHEN boss_direction = 'export' THEN boss_planned_date ELSE boss_etd END
     WHERE boss_planned_date IS NOT NULL AND boss_etd IS NULL AND boss_eta IS NULL
"""


def migrate_route(cr, table):
    cr.execute(ROUTE.format(table=table, spain="destination", abroad="origin"), ["import"])
    cr.execute(ROUTE.format(table=table, spain="origin", abroad="destination"), ["export"])
    cr.execute(DATES.format(table=table))


def migrate(cr, version):
    migrate_route(cr, "sale_order")
    env = api.Environment(cr, SUPERUSER_ID, {"tracking_disable": True})
    drafts = env["sale.order"].search([("state", "in", ("draft", "sent")), ("boss_storage_days_known", "=", False)])
    drafts.write({"boss_storage_days_known": True})
