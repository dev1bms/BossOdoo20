"""Company setup of the BOSS Odoo 20 environment (odoo shell; boss20 or the local boss_test copy).

Data file /tmp/boss/company.json (private, outside Git): BOSS master data as configured in Odoo 17 production
(legal name, CIF, address, EUR, chart es_pymes). Technical setup only:
- company data, currency EUR, Spanish chart PGC PYMEs 2008 (only while no accounting entry exists);
- pricelists enabled with one general EUR pricelist (no prices: sale prices are agreed per customer);
- Spanish (main) and English (second) languages, Madrid time zone.
NOT done here: the BOSS VAT table (dev/setup_vat_mapping.py, only the cases the sources settle); until then
quotations show 'VAT pending' and cannot be sent or confirmed. Idempotent.
"""
import json
import os

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname
# Server: dev/server_shell.sh mounts the file at /tmp/boss; local copy: samples-private is mounted at /mnt/samples.
path = next(p for p in ("/tmp/boss/company.json", "/mnt/samples/company.json") if os.path.isfile(p))
data = json.load(open(path, encoding="utf-8"))
company = env.ref("base.main_company")
eur = env.ref("base.EUR")
eur.active = True
spain = env.ref("base.es")
company.write({
    "name": data["name"], "vat": data["vat"], "street": data["street"], "city": data["city"], "zip": data["zip"],
    "country_id": spain.id,
    "state_id": env["res.country.state"].search([("country_id", "=", spain.id), ("code", "=", data["state_code"])]).id,
    "phone": data["phone"], "email": data["email"], "website": data["website"],
    "tax_calculation_rounding_method": data["tax_calculation_rounding_method"],
    "fiscalyear_last_day": data["fiscalyear_last_day"], "fiscalyear_last_month": data["fiscalyear_last_month"],
})
if company.currency_id != eur:
    company.currency_id = eur
if company.chart_template != data["chart_template"]:
    # Switching the chart deletes the previous chart's accounts/taxes/journals: only before any entry.
    assert not company._existing_accounting(), "accounting entries exist: chart not switched"
    env["account.chart.template"].try_loading(data["chart_template"], company, install_demo=False)
env.cr.commit()

env = env(context=dict(env.context, active_test=False))
settings = env["res.config.settings"].create({"group_product_pricelist": True})
settings.execute()
pricelists = env["product.pricelist"].search([("company_id", "in", (False, company.id))])
general = pricelists.filtered(lambda p: p.currency_id == eur)[:1] or env["product.pricelist"].create(
    {"name": "Tarifa general (EUR)", "currency_id": eur.id, "company_id": company.id})
general.write({"name": "Tarifa general (EUR)", "active": True, "sequence": 1})
(pricelists - general).filtered("active").action_archive()

for code in ("es_ES", "en_US"):
    lang = env["res.lang"].with_context(active_test=False).search([("code", "=", code)])
    if not lang.active:
        env["base.language.install"].create({"lang_ids": [(6, 0, lang.ids)], "overwrite": False}).lang_install()
company.partner_id.write({"lang": "es_ES", "tz": "Europe/Madrid"})
env["res.users"].search([("share", "=", False)]).write({"tz": "Europe/Madrid"})
env.cr.commit()
taxes = env["account.tax"].search([("company_id", "=", company.id), ("type_tax_use", "=", "sale")])
print("COMPANY", company.name, company.vat, company.currency_id.name, company.country_id.code, company.chart_template,
      "| sale taxes:", len(taxes), "| pricelists:", env["product.pricelist"].search([]).mapped("name"),
      "| BOSS VAT table rows:", env["boss.vat.tax"].search_count([("company_id", "=", company.id)]))
