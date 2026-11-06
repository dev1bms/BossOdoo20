"""VERI*FACTU prepared on boss20 without activating it (go-live tracker P3-08, documented default P1-06: no SII today):
module installed, test environment (AEAT pre-production) ticked, «required» left OFF so nothing changes when invoices
are posted. Activation = Belal loads the company certificate and Ángel/Belal tick «required» after the AEAT test.
    dev/server_shell.sh setup_verifactu_prepare.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
company = env.company  # noqa: F821
mod = env["ir.module.module"].search([("name", "=", "l10n_es_edi_verifactu")], limit=1)  # noqa: F821
print(f"OUT module l10n_es_edi_verifactu: {mod.state}")
company.write({"l10n_es_edi_verifactu_test_environment": True, "l10n_es_edi_verifactu_required": False})
env.cr.commit()  # noqa: F821
print(f"OUT test environment {company.l10n_es_edi_verifactu_test_environment}, required {company.l10n_es_edi_verifactu_required}, "
      f"certificates {len(company.l10n_es_edi_verifactu_certificate_ids)}")
