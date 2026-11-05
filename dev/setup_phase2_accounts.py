"""Accounting configuration of boss20 as in Odoo 17 (go-live tracker P2-09; documented defaults P37, A01 and the
Odoo 17 data read on 05/11/2026, applied by Belal's rule «apply what is documented»; Ángel reviews one invoice and one
bill per family afterwards). Commits. Idempotent.

- Income / expense account per BOSS service category, as the Odoo 17 product categories:
  Freight 705004/607400 · Inland transport 705001/607100 · Local charges 705003/607300 · Customs 705002/607200 ·
  Storage 705008/607700 · Insurance and courier 705007/607600 · Profit share 705005/607401. Duties paid on behalf keep
  their 419 accounts per product (dev/setup_suplidos_accounts.py). 607800 for accruals (F0-A36).
- Suppliers on 400000 and customers on 430000 by default (Odoo 17: MSC España and every partner).
- Purchase VAT by default from the VAT class of the service (A01, same criterion as Odoo 17): NR -> 21 % S,
  EX -> 0 % S, NS (paid on behalf) -> 0 % EXEMPT OP. The fiscal position of a foreign supplier (standard l10n_es by
  country) replaces them on the bill.
    dev/server_shell.sh setup_phase2_accounts.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
company = env.company
Account = env["account.account"].with_company(company)
Tax = env["account.tax"].with_company(company)


def account(code, name, kind):
    acc = Account.search([("code", "=", code), ("company_ids", "in", company.id)], limit=1)
    if not acc:
        acc = Account.create({"code": code, "name": name, "account_type": kind, "company_ids": [(4, company.id)]})
        print(f"OUT account {code} {name} created")
    return acc


CATEGORIES = {  # category name (en) -> (income, expense)
    "Freight": ("705004", "Flete", "607400", "Gastos por flete"),
    "Inland transport": ("705001", "Flete terrestre", "607100", "Flete terrestre"),
    "Local charges": ("705003", "Servicios locales", "607300", "Gastos locales"),
    "Customs": ("705002", "Servicios de aduana", "607200", "Gastos aduana"),
    "Storage and warehouse": ("705008", "Almacén", "607700", "Almacén"),
    "Insurance and courier": ("705007", "Seguro y courrier", "607600", "Seguro y courrier"),
    "Profit share": ("705005", "Profit share", "607401", "Profit share"),
}
for name, (inc, inc_name, exp, exp_name) in CATEGORIES.items():
    categ = env["product.category"].with_context(lang="en_US").search([("name", "=", name)], limit=1)
    assert categ, name
    income, expense = account(inc, inc_name, "income"), account(exp, exp_name, "expense")
    categ.with_company(company).write({"property_account_income_categ_id": income.id,
                                       "property_account_expense_categ_id": expense.id})
    print(f"OUT category «{name}»: {inc} / {exp}")
account("607800", "Compras pendientes de recibir factura", "expense")

payable = Account.search([("code", "=", "400000"), ("company_ids", "in", company.id)], limit=1)
receivable = Account.search([("code", "=", "430000"), ("company_ids", "in", company.id)], limit=1)
assert payable and receivable, (payable, receivable)
assert payable.account_type == "liability_payable" and receivable.account_type == "asset_receivable"
Default = env["ir.default"]
Default.set("res.partner", "property_account_payable_id", payable.id, company_id=company.id)
Default.set("res.partner", "property_account_receivable_id", receivable.id, company_id=company.id)
partners = env["res.partner"].with_company(company).search([("is_company", "=", True), ("parent_id", "=", False)])
moved = partners.filtered(lambda p: p.property_account_payable_id.code != "400000")
moved.write({"property_account_payable_id": payable.id})
print(f"OUT suppliers payable 400000 by default; {len(moved)} partners moved from "
      f"{', '.join(sorted(set(moved.mapped('property_account_payable_id.code')) - {'400000'}) or ['-'])}")
moved_r = partners.filtered(lambda p: p.property_account_receivable_id.code != "430000")
moved_r.write({"property_account_receivable_id": receivable.id})
print(f"OUT customers receivable 430000 by default; {len(moved_r)} partners moved")

PURCHASE = {"NR": ("21% S", 21.0), "EX": ("0% S", 0.0), "NS": ("0% EXEMPT OP", 0.0)}
taxes = {}
for cls, (name, amount) in PURCHASE.items():
    tax = Tax.with_context(lang="en_US").search([("name", "=", name), ("type_tax_use", "=", "purchase"),
                                                 ("amount", "=", amount), ("company_id", "=", company.id)], limit=1)
    assert tax, name
    taxes[cls] = tax
services = env["product.template"].with_company(company).search([("boss_pricing_mode", "!=", False)])
for cls, tax in taxes.items():
    group = services.filtered(lambda t: t.boss_vat_class == cls)
    group.write({"supplier_taxes_id": [(6, 0, tax.ids)]})
    print(f"OUT purchase VAT {cls} -> «{tax.name}» on {len(group)} services")
env.cr.commit()  # noqa: F821
