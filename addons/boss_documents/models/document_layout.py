"""BOSS document layout (ADR-011): the standard Odoo «Light» template with the BOSS identity used on the production
invoices of Odoo 17 (same two colours, same font), striped tables, contact footer. Applied once at installation to
the companies that have no layout yet; afterwards Settings › General › Document layout is the only place to change it
(the module never overwrites a choice made there)."""
from markupsafe import Markup

PRIMARY_COLOR = "#64a8af"  # BOSS teal (Odoo 17 production, 28/10/2026)
SECONDARY_COLOR = "#003a5c"  # BOSS navy
FONT = "Lato"
TABLES = "striped"


def apply_boss_layout(companies):
    env = companies.env
    layout = env.ref("web.external_layout_standard", raise_if_not_found=False)
    for company in companies:
        if company.external_report_layout_id:
            continue
        vals = {
            "external_report_layout_id": layout.id if layout else False,
            "report_tables_id": TABLES,
            "font": FONT,
            "primary_color": company.primary_color or PRIMARY_COLOR,
            "secondary_color": company.secondary_color or SECONDARY_COLOR,
        }
        if not company.report_footer or not company.report_footer.striptags().strip():
            parts = [p for p in (company.phone, company.email, company.website) if p]
            vals["report_footer"] = Markup("<p>%s</p>") % " · ".join(parts)
        company.write(vals)
