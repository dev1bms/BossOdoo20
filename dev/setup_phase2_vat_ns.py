"""BOSS VAT table: the NS services that are not paid on behalf (customs guarantee fee CAU, bank exchange loss QBR) get
the Odoo tax «0% EXEMPT NS», as Odoo 17 books them (products 213 CAU and 232 QBR carry tax 51 «0% EXEMPT NS», read
05/11/2026) and as Ángel's table of 31/08/2026 classes them (NS). Go-live tracker P2-08, documented default.
Commits. Idempotent.
    dev/server_shell.sh setup_phase2_vat_ns.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
company = env.company  # noqa: F821
Tax = env["account.tax"].with_company(company)  # noqa: F821
tax = Tax.with_context(lang="en_US").search([("name", "=", "0% EXEMPT NS"), ("type_tax_use", "=", "sale"),
                                             ("company_id", "=", company.id)], limit=1)
assert tax, "0% EXEMPT NS (sale) not found"
Row = env["boss.vat.tax"]  # noqa: F821
row = Row.search([("company_id", "=", company.id), ("vat_class", "=", "NS"), ("customer_zone", "=", "any"),
                  ("service_kind", "=", "other")], limit=1)
vals = {"company_id": company.id, "vat_class": "NS", "customer_zone": "any", "service_kind": "other", "tax_id": tax.id,
        "source": "Odoo 17: CAU y QBR con «0% EXEMPT NS» (productos 213 y 232, leídos 05/11/2026) · Ángel 31/08/2026: "
                  "NS = no sujeto por naturaleza · aplicado por defecto 05/11/2026 (P2-08)"}
if row:
    row.write(vals)
    print("OUT row NS/any/other updated")
else:
    Row.create(vals)
    print("OUT row NS/any/other created -> 0% EXEMPT NS")
env.cr.commit()  # noqa: F821
ns = env["product.template"].search([("boss_vat_class", "=", "NS"), ("boss_pricing_mode", "!=", False)])  # noqa: F821
print("OUT NS services: " + ", ".join(sorted(ns.mapped("default_code"))))
