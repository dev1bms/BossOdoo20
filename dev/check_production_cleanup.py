"""boss20 as the production database (go-live tracker P3-04): what test data would be cleaned before go-live, the Odoo
way (cancel/reverse posted test documents, archive test records), and the 2027 sequences. Before go-live EVERY posted
document, payment, file and quotation of boss20 is a test (some were made on real partner names: AGUILERA, ADUCEX,
MSC... in the trials of 27-28/10), so the clean-up takes them all. DRY RUN by default: it only counts and lists;
nothing changes. Run with the token file to apply (after the owners' trial, never before):
    dev/server_shell.sh check_production_cleanup.py                       # dry run
    dev/server_shell.sh check_production_cleanup.py dev/apply-on-boss20.txt   # apply"""
import os

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
APPLY = os.path.exists("/tmp/boss/apply-on-boss20.txt")
Move = env["account.move"]  # noqa: F821
Pay = env["account.payment"]  # noqa: F821
posted = Move.search([("state", "=", "posted"), ("move_type", "!=", "entry")])
entries = Move.search([("state", "=", "posted"), ("move_type", "=", "entry")])
drafts = Move.search([("state", "=", "draft")])
payments = Pay.search([("state", "not in", ("draft", "cancel"))])
test_partners = env["res.partner"].search([("name", "ilike", "[PRUEBA]")])  # noqa: F821
test_files = env["boss.expediente"].search([("name", "ilike", "[PRUEBA]")]) | env["boss.expediente"].search(  # noqa: F821
    [("partner_id", "in", test_partners.ids)])
all_files = env["boss.expediente"].search([])  # noqa: F821
orders = env["sale.order"].search([])  # noqa: F821
test_orders = orders.filtered(lambda o: o.partner_id in test_partners or "[PRUEBA]" in (o.name or ""))
real_partners_with_docs = (posted.partner_id.commercial_partner_id - test_partners.commercial_partner_id)
print(f"OUT posted invoices/bills: {len(posted)} (partners: {len(posted.partner_id.commercial_partner_id)}, "
      f"of which not [PRUEBA]: {len(real_partners_with_docs)}: {', '.join(real_partners_with_docs.mapped('name')[:5])})")
print(f"OUT posted journal entries: {len(entries)}; drafts: {len(drafts)}; payments: {len(payments)}")
print(f"OUT files: {len(all_files)} ({len(test_files)} of [PRUEBA] customers); quotations: {len(orders)} ({len(test_orders)} test)")
print(f"OUT [PRUEBA] partners: {len(test_partners)}")
seq = env["ir.sequence"]  # noqa: F821
for journal in env["account.journal"].search([("type", "in", ("sale", "purchase"))]):  # noqa: F821
    last = Move.search([("journal_id", "=", journal.id), ("state", "=", "posted")], order="name desc", limit=1)
    print(f"OUT journal {journal.code}: last posted {last.name or '-'} (2027 numbering starts fresh by year, standard)")
if not APPLY:
    print("OUT dry run: nothing changed. Apply only after the owners' trial (P3-01/02), with the token file.")
    raise SystemExit(0)
# --- apply (the Odoo way): reverse posted test documents, cancel payments, cancel test files and quotations, archive
reversed_moves = Move
for move in (posted | entries):
    reversal = move._reverse_moves([{"date": move.date, "ref": "[PRUEBA] limpieza antes del arranque"}], cancel=True)
    reversed_moves |= reversal
print(f"OUT reversed {len(reversed_moves)} test documents")
for pay in payments:
    pay.action_cancel()
drafts.button_cancel()
for f in all_files.filtered(lambda f: f.state not in ("cancel",)):
    try:
        f.with_context(file_action=True).write({"state": "cancel"})
    except Exception as e:  # noqa: BLE001
        print(f"OUT file {f.name} not cancelled: {e}")
orders.filtered(lambda o: o.state not in ("cancel",))._action_cancel()
test_partners.write({"active": False})
env.cr.commit()  # noqa: F821
print("OUT applied: test documents reversed, payments cancelled, test files and quotations cancelled, [PRUEBA] partners archived")
