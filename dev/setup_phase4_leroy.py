"""Leroy Merlin data on boss20 (go-live tracker P4-10, documented defaults F0-C59 and Odoo 17 facts). Commits.
Idempotent.
- The customer is a periodic-invoice customer: its files are invoiced together (F0-C59 names Leroy Merlin as the
  example of the monthly grouped invoice of Odoo 17).
- Its payment term as in Odoo 17 (partner 23014: «60 Days»), when boss20 has that term and the contact has none yet.
    dev/server_shell.sh setup_phase4_leroy.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
leroy = env["res.partner"].search([("ref", "=", "O17:23014")], limit=1)
assert leroy, "Leroy Merlin (Odoo 17 id 23014) not found on boss20"
if leroy.boss_invoice_grouping != "grouped":
    leroy.boss_invoice_grouping = "grouped"
    print(f"OUT {leroy.name}: periodic invoicing (several files on one invoice) set")
else:
    print(f"OUT {leroy.name}: periodic invoicing already set")
term = env["account.payment.term"].with_context(lang="en_US").search([("name", "ilike", "60")])
if len(term) == 1 and not leroy.property_payment_term_id:
    leroy.property_payment_term_id = term
    print(f"OUT payment term «{term.name}» set (Odoo 17: 60 Days)")
else:
    print(f"OUT payment term left as is: {leroy.property_payment_term_id.name or '-'} (terms matching 60: {term.mapped('name')})")
env.cr.commit()  # noqa: F821
