"""Month-close configuration on boss20 (go-live tracker P4-07, documented defaults F0-A36 and P03): currency
revaluation journal and provision accounts (the same exchange-difference accounts Odoo 17 uses for realised
differences), accrual account 607800 already created (P2-09). Commits. Idempotent.
    dev/server_shell.sh setup_phase4_monthclose.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
company = env.company  # noqa: F821
Journal = env["account.journal"].with_company(company)  # noqa: F821
Account = env["account.account"].with_company(company)  # noqa: F821
print(f"OUT realised exchange differences: journal {company.currency_exchange_journal_id.code}, "
      f"expense {company.expense_currency_exchange_account_id.code}, income {company.income_currency_exchange_account_id.code}")
journal = Journal.search([("code", "=", "REVAL"), ("company_id", "=", company.id)], limit=1)
if not journal:
    journal = Journal.create({"name": "Revaluación de moneda", "code": "REVAL", "type": "general", "company_id": company.id})
    print("OUT journal REVAL created")
vals = {}
if not company.account_revaluation_journal_id:
    vals["account_revaluation_journal_id"] = journal.id
if not company.account_revaluation_expense_provision_account_id:
    vals["account_revaluation_expense_provision_account_id"] = company.expense_currency_exchange_account_id.id
if not company.account_revaluation_income_provision_account_id:
    vals["account_revaluation_income_provision_account_id"] = company.income_currency_exchange_account_id.id
if vals:
    company.write(vals)
accrual = Account.search([("code", "=", "607800"), ("company_ids", "in", company.id)], limit=1)
env.cr.commit()  # noqa: F821
print(f"OUT revaluation: journal {company.account_revaluation_journal_id.code}, expense provision "
      f"{company.account_revaluation_expense_provision_account_id.code}, income provision "
      f"{company.account_revaluation_income_provision_account_id.code}; accrual account 607800 {'present' if accrual else 'MISSING'}")
