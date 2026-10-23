"""Time-based prices with a franchise in hours count periods of 24 hours (airport handlers, «por 24 horas»); the
others keep calendar days, the default of the new field."""


def migrate(cr, version):
    cr.execute("UPDATE boss_tariff_line SET period_unit = '24h' WHERE method = 'time' AND COALESCE(free_hours, 0) > 0")
