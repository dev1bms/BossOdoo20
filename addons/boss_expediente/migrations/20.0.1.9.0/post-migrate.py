"""ADR-006: opportunities and files get origin/destination from the pricing inputs they already had (Spanish port,
country abroad; opportunities also ETD/ETA from the planned date). Plain SQL: those inputs do not change."""

ROUTE = """
    UPDATE {table} t
       SET {p}{spain}_port_id = t.{p}port_id,
           {p}{spain}_country_id = COALESCE((SELECT country_id FROM boss_port WHERE id = t.{p}port_id),
                                            (SELECT id FROM res_country WHERE code = 'ES')),
           {p}{abroad}_country_id = t.{p}country_id
     WHERE t.{p}direction = %s
       AND t.{p}origin_country_id IS NULL AND t.{p}origin_port_id IS NULL
       AND t.{p}destination_country_id IS NULL AND t.{p}destination_port_id IS NULL
       AND (t.{p}port_id IS NOT NULL OR t.{p}country_id IS NOT NULL)
"""
LEAD_DATES = """
    UPDATE crm_lead
       SET boss_eta = CASE WHEN boss_direction = 'export' THEN boss_eta ELSE boss_planned_date END,
           boss_etd = CASE WHEN boss_direction = 'export' THEN boss_planned_date ELSE boss_etd END
     WHERE boss_planned_date IS NOT NULL AND boss_etd IS NULL AND boss_eta IS NULL
"""


def migrate(cr, version):
    for table, prefix in (("crm_lead", "boss_"), ("boss_expediente", "")):
        cr.execute(ROUTE.format(table=table, p=prefix, spain="destination", abroad="origin"), ["import"])
        cr.execute(ROUTE.format(table=table, p=prefix, spain="origin", abroad="destination"), ["export"])
    cr.execute(LEAD_DATES)
