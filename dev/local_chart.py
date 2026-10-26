"""Local copy only (boss_test): Spanish chart PGC PYMEs on the fictitious company, so the VAT table and the [DEMO]
quotations work like on boss20 without BOSS master data."""
assert env.cr.dbname in ("boss_test", "boss_uat"), env.cr.dbname
company = env.ref("base.main_company")
company.write({"name": "Empresa Ejemplo S.L. [DEMO]", "country_id": env.ref("base.es").id,
               "currency_id": env.ref("base.EUR").id})
if company.chart_template != "es_pymes":
    env["account.chart.template"].try_loading("es_pymes", company, install_demo=False)
env.cr.commit()
print("chart", company.chart_template)
