"""Load the QWeb templates of boss_portal (not installed yet) in a rolled-back transaction: the inherited xpaths must
match the Odoo 20 templates, the combined arch must carry the rate-quotation conditions, and the shipment
sub-templates must render the whitelisted values (estimated vs actual)."""
import os
from datetime import date, datetime

from odoo.tools import convert_file

assert env.cr.dbname == "boss20"  # noqa: F821
results = []


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


path = "/mnt/wip-addons/boss_portal/views"
for filename in ("portal_sale_templates.xml", "portal_shipment_templates.xml"):
    convert_file(env, "boss_portal", f"views/{filename}", {}, mode="init", pathname=os.path.join(path, filename))  # noqa: F821
env.flush_all()  # noqa: F821
View = env["ir.ui.view"]  # noqa: F821
sidebar = View._get_combined_arch_for_xmlid("sale.sale_order_portal_template") if hasattr(View, "_get_combined_arch_for_xmlid") else None
if sidebar is None:
    sidebar = env.ref("sale.sale_order_portal_template")._get_combined_arch()  # noqa: F821
from lxml import etree  # noqa: E402
arch = etree.tostring(sidebar, encoding="unicode") if not isinstance(sidebar, str) else sidebar
check("sidebar: total hidden for a rate quotation (title and mobile price row)", (True, True, True),
      (arch.count("sale_order.boss_rate_quotation") >= 2, "Rates" in arch, "0 if sale_order.boss_rate_quotation else sale_order.amount_total" in arch))
quotes = env.ref("sale.portal_my_quotations")._get_combined_arch()  # noqa: F821
check("quotations list: «Rates per unit» instead of the total", True, "Rates per unit" in etree.tostring(quotes, encoding="unicode"))
values = {"s": {"atd": None, "etd": date(2026, 11, 20), "ata": None, "eta": date(2026, 12, 5), "delivered": None,
                "events": [{"date": datetime(2026, 11, 20, 9, 0), "kind": "milestone", "text": "Loaded on board"}],
                "last_update": datetime(2026, 11, 20, 9, 0)}}
html = str(env["ir.qweb"]._render("boss_portal.boss_shipment_dates", values))  # noqa: F821
check("dates: estimated departure and arrival shown as estimated; nothing actual; delivery «Not yet»", (2, 0, True),
      (html.count("Estimated"), html.count("Actual"), "Not yet" in html))
html = str(env["ir.qweb"]._render("boss_portal.boss_shipment_events", values))  # noqa: F821
check("events: the published text and the source of the update", (True, True), ("Loaded on board" in html, "BOSS operations" in html))
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if len(results) - sum(results):  # a failed check fails the run (dev/uat_run.sh records the exit status)
    raise SystemExit(1)
