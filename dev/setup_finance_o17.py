"""Finance settings of Odoo 17 copied to boss20 (roadmap item 6; Belal's go-ahead of 03/11/2026 to copy settings).
Idempotent: what exists is kept. No account number is typed here: the bank accounts (IBAN) of the journals are entered
in Odoo by Belal or Ángel (Accounting › Configuration › Journals › the journal › Bank account).
    dev/server_shell.sh setup_finance_o17.py

- Payment terms of Odoo 17 that boss20 lacks: 6, 20 and 60 days (account.payment.term of Odoo 17, read 03/11/2026).
  75 and 90 days also exist in Odoo 17 but exceed the 60-day maximum between companies of Ley 3/2004 (art. 4, Ley
  15/2010): not created until Ángel says whether they are still used (one question, docs/hoja-de-ruta.md).
- Bank journals of Odoo 17 (account.journal of type bank, read 03/11/2026): one per account and currency, named by bank
  and currency, without the number."""
from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
company = env.company
eur, usd = env.ref("base.EUR"), env.ref("base.USD")

TERMS = [(6, "6 días", "6 Days"), (20, "20 días", "20 Days"), (60, "60 días", "60 Days")]
for days, es, en in TERMS:
    Term = env["account.payment.term"].with_context(active_test=False)
    term = Term.with_context(lang="es_ES").search([("name", "=", es)], limit=1) or Term.with_context(
        lang="en_US").search([("name", "=", en)], limit=1)
    if not term:
        term = Term.with_context(lang="en_US").create({
            "name": en, "sequence": 10 + days,
            "line_ids": [Command.create({"value": "percent", "value_amount": 100.0, "nb_days": days,
                                         "delay_type": "days_after"})]})
        term.with_context(lang="es_ES").name = es
        print("TERM created", es)
    else:
        print("TERM kept", es)

# Odoo 17 bank journals (name without the account number, currency); code ≤ 5 characters, after BNK1 in the list.
JOURNALS = [
    ("SANT", "Santander EUR", eur), ("SANTO", "Santander EUR (otros)", eur), ("SANU1", "Santander USD", usd),
    ("SANU2", "Santander USD (0075)", usd), ("POP", "Popular EUR", eur), ("CXB", "Caixabank EUR", eur),
    ("CXBU", "Caixabank USD", usd), ("BKT", "Bankinter EUR", eur), ("WCA", "WCA USD", usd),
]
Journal = env["account.journal"].with_context(active_test=False)
for sequence, (code, name, currency) in enumerate(JOURNALS, start=20):
    journal = Journal.search([("company_id", "=", company.id), ("code", "=", code)], limit=1)
    if journal:
        print("JOURNAL kept", code, journal.name)
        continue
    journal = Journal.create({"name": name, "code": code, "type": "bank", "company_id": company.id,
                              "currency_id": currency.id if currency != company.currency_id else False,
                              "sequence": sequence})
    print("JOURNAL created", code, name, currency.name, "account", journal.default_account_id.code)
env.cr.commit()
print("DONE bank accounts to type in Odoo:", ", ".join(code for code, _name, _currency in JOURNALS))
