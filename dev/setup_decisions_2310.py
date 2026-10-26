"""Configuration of the decisions approved by Belal on 23/10/2026 (proposals P03, P18, P30, P40, P41, P29, P42) on
boss20 or the local copy (odoo shell). Idempotent. The VAT rows of P17 are in dev/setup_vat_mapping.py.

- P03: supplier costs in another currency converted with Odoo's rate of the quotation date, frozen on acceptance.
- P30: a supplier bill of a file service is posted on time; its payment waits for the customer invoice.
- P18/P37 (part): amounts paid on behalf (ARA, IVA, PLA, DUM) on account 419000, as in Odoo 17.
- P40, P41, P29, P42: readings of the real WFS documents ([MUESTRA], waiting for approval): periods of 24 hours,
  per 100 kg or fraction, tiers by day number, minimum per stay. The tariffs stay waiting for approval (P19).
"""
assert env.cr.dbname in ("boss20", "boss_test", "boss_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
company = env.ref("base.main_company")

company.write({"boss_fx_policy": "rate_quotation", "boss_bill_before_invoice": "block_payment"})
print("company", company.boss_fx_policy, company.boss_bill_before_invoice)

account = env["account.account"].with_company(company).search([("code", "=", "419000")], limit=1)
assert account, "account 419000 missing"
on_behalf = env["product.template"].with_company(company).search([("boss_paid_on_behalf", "=", True)])
on_behalf.write({"property_account_income_id": account.id, "property_account_expense_id": account.id})
print("paid on behalf on", account.code, on_behalf.mapped("default_code"))

lines = env["boss.tariff.line"].search([
    ("product_id.default_code", "=", "ALM"), ("tariff_id.partner_id.name", "=like", "WFS%"),
    ("tariff_id.is_demo", "=", False)])
lines.write({"period_unit": "24h", "tier_mode": "positional", "round_up": True, "round_undecided": False,
             "min_per_day": False})
for line in lines:
    print("WFS ALM", line.tariff_id.name, line.tariff_id.state, line.period_unit, line.tier_mode, line.round_up)
env.cr.commit()
