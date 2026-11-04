"""Check of the settings data on boss20 (read only, rolled back): the service attributes, the default periods and the
incoterm freight seeded by the settings phase 2 match their seeds, every BOSS service and incoterm is still there, and
the company settings hold the values of before (phases 1 and 3). Codes and statuses only.
    dev/uat_run.sh check_settings_data.py boss20"""
from odoo.addons.boss_expediente.models.boss_service_period import DEFAULT_PERIOD_EVENTS
from odoo.addons.boss_pricing_sale.models.account_incoterms import COLLECT_INCOTERMS, PREPAID_INCOTERMS
from odoo.addons.boss_services.models.service_groups import CUSTOMS_VALUE_CHARGES, SUPPLIER_ROLES

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, active_test=False, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


Template = env["product.template"]
services = Template.search([("boss_pricing_mode", "!=", False)])
active = services.filtered("active")
codes = active.mapped("default_code")
print(f"INFO {len(active)} active BOSS services, {len(services) - len(active)} archived")
check("1 every active BOSS service has a code, and each code is used once", (0, []),
      (len(active.filtered(lambda s: not s.default_code)), sorted({c for c in codes if c and codes.count(c) > 1})))
check("2 every seeded code still exists as an active service", [],
      sorted(c for c in {*SUPPLIER_ROLES, *CUSTOMS_VALUE_CHARGES, *(k[0] for k in DEFAULT_PERIOD_EVENTS)} if c not in codes))
check("3 «Bought from» = the seed on the seeded services, «any supplier» on the others", [],
      sorted(s.default_code for s in active if s.boss_supplier_role != SUPPLIER_ROLES.get(s.default_code, "any")))
check("4 «Counts for the customs value as» = the seed, empty on the others", [],
      sorted(s.default_code for s in active if (s.boss_customs_value_charge or False)
             != CUSTOMS_VALUE_CHARGES.get(s.default_code, False)))
periods = {(p.product_tmpl_id.default_code, p.direction, p.load_type or None): (p.start_event or None, p.end_event or None)
           for p in env["boss.service.period"].search([("product_tmpl_id.active", "=", True)])}
check("5 the default periods are the seeded ones, no line lost or added", DEFAULT_PERIOD_EVENTS, periods)
check("6 every time-based service has default periods", [],
      sorted(s.default_code for s in active.filtered(lambda s: s.boss_cost_method == "time") if not s.boss_period_ids))
incoterms = env["account.incoterms"].search([])
check("7 the 11 Incoterms 2020 are there and active", (11, True),
      (len(incoterms.filtered(lambda i: i.code in PREPAID_INCOTERMS + COLLECT_INCOTERMS)), all(incoterms.mapped("active"))))
check("8 incoterm freight: C and D prepaid, E and F collect", [],
      sorted(i.code for i in incoterms if i.boss_freight_payment != (
          "prepaid" if i.code in PREPAID_INCOTERMS else "collect" if i.code in COLLECT_INCOTERMS else False)))
company = env.company
check("9 phase 1 values = the constants of before", (30, 7, 167, 333, 1000, 7, "chargeable", True, 3),
      (company.boss_tariff_expiring_days, company.boss_spot_rate_validity_days, company.boss_volumetric_air,
       company.boss_volumetric_road, company.boss_volumetric_sea, company.boss_close_days_after_delivery,
       company.boss_default_allocation_basis, company.boss_invoice_operation_date, company.boss_hbl_originals))
check("10 phase 3 levels = the behaviour of before (leaving warns, delivering and closing required)",
      ("warn",) * 4 + ("block",) * 8,
      tuple(company[f] for f in ("boss_cond_transit_atd", "boss_cond_transit_booking", "boss_cond_transit_master",
                                 "boss_cond_transit_containers", "boss_cond_delivered_ata",
                                 "boss_cond_delivered_discharge", "boss_cond_delivered_release",
                                 "boss_cond_delivered_pickup", "boss_cond_delivered_delivery",
                                 "boss_cond_delivered_hbl", "boss_cond_close_invoiced", "boss_cond_close_margin")))
writers = env["ir.access"].search([("model_id.model", "=", "res.config.settings"), ("for_write", "=", True)])
check("11 Settings are saved by administrators only; the Settings menu is for administrators",
      (["base.group_system"], ["base.group_erp_manager", "base.group_system"]),
      (sorted(writers.group_id.get_external_id().values()),
       sorted(env.ref("base.menu_administration").group_ids.get_external_id().values())))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
