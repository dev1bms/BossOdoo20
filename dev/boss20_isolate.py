"""boss20 during the tests on the main database (Belal, 27/10/2026): external effects off. No mail server exists (and
none is created); this script deactivates the scheduled actions that send or fetch anything outside Odoo and keeps
their list in the parameter «boss.test_disabled_crons» so that `--restore` can switch the same ones back on.
    dev/server_shell.sh boss20_isolate.py              (deactivate)
    dev/server_shell.sh boss20_isolate.py restore.txt  (restore, with a file named restore.txt mounted)"""
import os

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
EXTERNAL = [  # names as installed on boss20 (English source)
    "Mail: Email Queue Manager", "SMS: SMS Queue Manager", "Digest Emails", "Send invoices automatically",
    "Account: Journal online sync", "Account: Journal online sync reminder",
    "Account: Journal online sync cleanup unused connections", "Invoice OCR: Update All Status",
    "Invoice OCR: Validate Invoices", "CRM: enrich leads (IAP)", "Product Images: Get product images from Barcode Lookup",
    "Send account reports automatically", "Purchase reminder", "Payment: Run Processing", "Currency: rate update",
    "Calendar: Event Reminder", "Users: Notify About Unregistered Users", "Publisher: Update Notification",
]
Cron, Param = env["ir.cron"].sudo().with_context(active_test=False), env["ir.config_parameter"].sudo()  # noqa: F821
if "restore.txt" in os.environ.get("BOSS_FILES", ""):
    ids = [int(i) for i in (Param.get_str("boss.test_disabled_crons") or "").split(",") if i]
    Cron.browse(ids).exists().write({"active": True})
    Param.set_str("boss.test_disabled_crons", "")
    Param.set_str("iap.endpoint", Param.get_str("boss.test_saved_iap_endpoint"))
    print("restored", ids)
else:
    crons = Cron.search([("active", "=", True)]).filtered(lambda c: c.cron_name in EXTERNAL)
    known = [int(i) for i in (Param.get_str("boss.test_disabled_crons") or "").split(",") if i]
    Param.set_str("boss.test_disabled_crons", ",".join(str(i) for i in sorted(set(known) | set(crons.ids))))
    crons.write({"active": False})
    if Param.get_str("iap.endpoint") != "http://127.0.0.1:9":  # IAP (OCR, autocomplete, SMS, enrichment) to a closed port
        Param.set_str("boss.test_saved_iap_endpoint", Param.get_str("iap.endpoint"))
        Param.set_str("iap.endpoint", "http://127.0.0.1:9")
    print("deactivated", sorted(crons.mapped("cron_name")))
    print("mail servers", env["ir.mail_server"].sudo().search_count([]), "| iap.endpoint",  # noqa: F821
          Param.get_str("iap.endpoint"))
env.cr.commit()  # noqa: F821
