"""Local copy only (boss_test): nothing leaves the machine during the accounting session (posting, payments).
Scheduled jobs off, no mail server, Odoo online services (IAP: OCR of bills, partner autocomplete, SMS, live currency
rates...) pointed at a closed local port. `dev/test.sh serve` also starts Odoo without cron threads, with a closed
SMTP port and a dead HTTP proxy. Idempotent."""
assert env.cr.dbname == "boss_test", env.cr.dbname  # noqa: F821
DEAD = "http://127.0.0.1:9"
ICP = env["ir.config_parameter"].sudo()  # noqa: F821

env["ir.cron"].with_context(active_test=False).search([]).write({"active": False})  # noqa: F821
env["ir.mail_server"].with_context(active_test=False).search([]).unlink()  # noqa: F821
for key in ("iap.endpoint", "iap_extract_endpoint", "iap.partner_autocomplete.endpoint", "enrich.endpoint",
            "reveal.endpoint", "snailmail.endpoint", "odoo_ocn.endpoint", "currency_rate_live.iap_proxy_url",
            "html_editor.olg_api_endpoint", "html_editor.media_library_endpoint"):
    ICP.set_str(key, DEAD)
for company in env["res.company"].search([]):  # noqa: F821
    values = {}
    for field, value in (("currency_interval_unit", "manually"), ("extract_in_invoice_digitalization_mode", "no_send"),
                         ("extract_out_invoice_digitalization_mode", "no_send")):
        if field in company._fields:
            values[field] = value
    company.write(values)
env.cr.commit()  # noqa: F821
print("ISOLATED crons active:", env["ir.cron"].search_count([]),  # noqa: F821
      "| mail servers:", env["ir.mail_server"].with_context(active_test=False).search_count([]),  # noqa: F821
      "| iap.endpoint:", ICP.get_str("iap.endpoint"))
