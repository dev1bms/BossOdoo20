"""Bank accounts (IBAN) of the company's bank journals on boss20, copied from Odoo 17 (go-live tracker P2-10, documented
default: the journals of Odoo 17, read 05/11/2026). The numbers never live in Git: they come in a private data file
mounted by dev/server_shell.sh (BOSS_FILES), one line per journal: <journal code>;<IBAN>;<BIC>;<bank name>.
    dev/server_shell.sh setup_phase2_banks.py .research/banks-o17.txt
Commits. Idempotent. Lock dates and the payment model stay for P3-09."""
import os  # noqa: E402

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
files = [f for f in os.environ.get("BOSS_FILES", "").split("|") if f]
assert files == ["banks-o17.txt"], files
company = env.company
Journal = env["account.journal"].with_company(company)
PartnerBank = env["res.partner.bank"].with_company(company)
done = 0
for raw in open("/tmp/boss/banks-o17.txt", encoding="utf-8"):
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        continue
    code, iban, bic, bank_name = [x.strip() for x in raw.split(";")]
    journal = Journal.search([("code", "=", code), ("type", "=", "bank")], limit=1)
    if not journal:
        print(f"OUT no journal with code {code}: skipped")
        continue
    acc = PartnerBank.search([("sanitized_account_number", "=", iban.replace(" ", "")),
                              ("partner_id", "=", company.partner_id.id)], limit=1)
    if not acc:
        acc = PartnerBank.create({"account_number": iban, "partner_id": company.partner_id.id, "bank_name": bank_name,
                                  "bank_bic": bic})
    if journal.bank_account_id != acc:
        journal.write({"bank_account_id": acc.id})
    if not acc.allow_out_payment:  # the company's own accounts are trusted: Odoo refuses to post invoices otherwise
        acc.sudo().write({"allow_out_payment": True})
    done += 1
    print(f"OUT journal {code} «{journal.name}» -> account ending …{iban[-4:]} ({bank_name})")
env.cr.commit()  # noqa: F821
print(f"OUT {done} journals with their bank account; without number: "
      + ", ".join(Journal.search([("type", "=", "bank"), ("bank_account_id", "=", False)]).mapped("code")))
