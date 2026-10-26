"""Accounts of the amounts paid on behalf of the customer (ARA, IVA, PLA, DUM), as Odoo 17 production books them
(odoo shell; local copy boss_test now; boss20 ONLY after Ángel approves the map, decision W04-2 of 26/10/2026).

Odoo 17 (read 26/10/2026): 419000 is the standard payable account; the paid-on-behalf concepts use their own
sub-accounts of current liabilities, by concept and side (charged to the customer / borne with the supplier):
  419001 SUPLIDOS IVA REPERCUTIDO IMPORT        419003 SUPLIDOS IVA SOPORTADO IMPORT
  419002 SUPLIDOS ARANCELES REPERCUTIDOS IMPORT 419004 SUPLIDOS ARANCELES SOPORTADOS IMPORT
  419005 ANTI DUMPING
  419006 IMPUESTO SOBRE PLASTICO NO REUTILIZABLE REPERCUTIDO  419007 ... SOPORTADO
The product -> account map below is the proposal for Ángel (docs/cuentas-suplidos.md); it is not his decision yet.
Idempotent."""
assert env.cr.dbname in ("boss20", "boss_test", "boss20_uat"), env.cr.dbname  # noqa: F821
import sys  # noqa: E402

if env.cr.dbname == "boss20" and "--apply-on-boss20" not in sys.argv:  # noqa: F821
    raise SystemExit("boss20: run only with --apply-on-boss20 (Odoo 17 practice applied by Belal's mandate 26/10; Ángel ratifies, task W10).")
company = env.ref("base.main_company")  # noqa: F821
Account = env["account.account"].with_company(company)  # noqa: F821
ACCOUNTS = {
    "419001": "Suplidos IVA repercutido importación", "419002": "Suplidos aranceles repercutidos importación",
    "419003": "Suplidos IVA soportado importación", "419004": "Suplidos aranceles soportados importación",
    "419005": "Suplidos antidumping", "419006": "Suplidos impuesto plástico no reutilizable repercutido",
    "419007": "Suplidos impuesto plástico no reutilizable soportado",
}
# product code -> (income account: charged to the customer, expense account: borne with the broker)
MAP = {"IVA": ("419001", "419003"), "ARA": ("419002", "419004"), "DUM": ("419005", "419005"),
       "PLA": ("419006", "419007")}
accounts = {}
for code, name in ACCOUNTS.items():
    account = Account.search([("code", "=", code), ("company_ids", "in", company.id)], limit=1)
    if not account:
        account = Account.create({"code": code, "name": name, "account_type": "liability_current",
                                  "reconcile": False, "company_ids": [(4, company.id)]})
    accounts[code] = account
for code, (income, expense) in MAP.items():
    template = env["product.template"].with_company(company).search([("default_code", "=", code)], limit=1)  # noqa: F821
    assert template and template.boss_paid_on_behalf, code
    template.write({"property_account_income_id": accounts[income].id,
                    "property_account_expense_id": accounts[expense].id})
    print("SUPLIDO", code, "income", income, "expense", expense)
env.cr.commit()  # noqa: F821
print("accounts", sorted((a.code, a.account_type) for a in accounts.values()))
