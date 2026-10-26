"""Read-only readiness snapshot of boss20 (odoo shell via dev/server_shell.sh). Nothing is written (rollback)."""
from collections import Counter
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, lang="en_US", active_test=False))  # noqa: F821
today = __import__("datetime").date.today()


def show(label, value):
    print(f"{label}: {value}")


M = env["ir.module.module"]
show("BOSS modules", sorted((m.name, m.state, m.latest_version) for m in M.search([("name", "like", "boss_%")])))
show("EDI/SII/Verifactu modules installed", sorted(m.name for m in M.search(
    [("state", "=", "installed"), "|", "|", ("name", "like", "l10n_es_edi%"), ("name", "like", "%verifactu%"),
     ("name", "like", "%sii%")])))
show("Other key modules", sorted((m.name, m.state) for m in M.search([("name", "in", [
    "account_accountant", "l10n_es", "purchase", "sale_purchase", "crm", "hr_expense", "stock", "account_reports"])])))
company = env.company
show("Company", (company.name, company.currency_id.name, company.country_id.code,
                 getattr(company, "boss_fx_policy", "n/a"), getattr(company, "boss_bill_before_invoice", "n/a"),
                 "lock dates", company.fiscalyear_lock_date, company.tax_lock_date))
show("Outgoing mail servers (active)", env["ir.mail_server"].search_count([("active", "=", True)]))
try:
    show("Verifactu/SII on company", {f: company[f] for f in company._fields
                                      if "verifactu" in f or "sii" in f or "edi_mode" in f})
except Exception as exc:  # noqa: BLE001
    show("Verifactu/SII on company", exc)

# Services and how they are priced
T = env["product.template"].search([("boss_pricing_mode", "!=", False), ("active", "=", True)])
show("Active BOSS services", len(T))
show("By cost source", dict(Counter(T.mapped("boss_pricing_mode"))))
show("Services with an open question", len(T.filtered("boss_open_question")))
show("purchase_method", dict(Counter(T.mapped("purchase_method"))))

# Tariffs
Tar = env["boss.tariff"].search([("active", "=", True)])
show("Tariffs by state", dict(Counter(Tar.mapped("state"))))
show("Tariffs DEMO / real", (len(Tar.filtered("is_demo")), len(Tar.filtered(lambda t: not t.is_demo))))
real = Tar.filtered(lambda t: not t.is_demo)
show("Real tariffs", [(t.name, t.partner_id.name, t.state, str(t.valid_from), str(t.valid_to or ""),
                       t.line_count, bool(t.document)) for t in real])
covered = env["boss.tariff.line"].search([("tariff_id", "in", real.ids)]).mapped("product_id.product_tmpl_id")
approved = env["boss.tariff.line"].search([("tariff_id", "in", real.filtered(
    lambda t: t.state == "approved" and (not t.valid_to or t.valid_to >= today)).ids)]).mapped(
    "product_id.product_tmpl_id")
tariff_services = T.filtered(lambda p: p.boss_pricing_mode == "tariff")
show("Tariff services with a real price / approved and valid",
     (len(tariff_services & covered), len(tariff_services & approved), "of", len(tariff_services)))
show("Tariff services with no real price at all", sorted(p.default_code or p.name for p in tariff_services - covered))

# Sale side
PL = env["product.pricelist"].search([])
show("Pricelists (items)", [(p.name, len(p.item_ids)) for p in PL])
V = env["boss.vat.tax"].search([])
show("BOSS VAT table rows", len(V))
Partner = env["res.partner"]
show("Customers / suppliers (DEMO excluded)", (
    Partner.search_count([("customer_rank", ">", 0), ("name", "not like", "[DEMO]")]),
    Partner.search_count([("supplier_rank", ">", 0), ("name", "not like", "[DEMO]")])))
SO = env["sale.order"]
show("Sale orders by state", dict(Counter(SO.search([]).mapped("state"))))
show("Sale orders non-DEMO", SO.search_count([("partner_id.name", "not like", "[DEMO]")]))
show("Files", env["boss.expediente"].search_count([]))
show("Purchase orders by state", dict(Counter(env["purchase.order"].search([]).mapped("state"))))
Move = env["account.move"]
show("Moves by type/state", dict(Counter((m.move_type, m.state) for m in Move.search([]))))
show("Journals", [(j.code, j.type, j.name) for j in env["account.journal"].search([])])
show("Accounts 419000/4000", [(a.code, a.name) for a in env["account.account"].search(
    ["|", ("code", "=like", "419%"), ("code", "=like", "4000%")])])

# People
users = env["res.users"].search([("share", "=", False), ("active", "=", True)])
for u in users:
    groups = [g for g, x in (("sales mgr", "sales_team.group_sale_manager"), ("salesman", "sales_team.group_sale_salesman"),
                              ("purchase", "purchase.group_purchase_user"), ("invoicing", "account.group_account_invoice"),
                              ("accountant", "account.group_account_user"), ("acc mgr", "account.group_account_manager"),
                              ("tariff mgr", "boss_pricing.group_tariff_manager"),
                              ("tariff user", "boss_pricing.group_tariff_user"))
              if env.ref(x, raise_if_not_found=False) and u.has_group(x)]
    print("USER", u.login.split("@")[0], "|", u.name, "|", u.login_date and str(u.login_date)[:10], "|", groups)
for r in env["boss.vat.tax"].search([]):  # noqa: F821
    print("VAT", r.vat_class, r.customer_zone, r.service_kind, "->", r.tax_id.name)
env.cr.rollback()  # noqa: F821
