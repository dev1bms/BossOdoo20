"""BOSS VAT table on boss20 / the local copy (odoo shell): the Odoo tax of each VAT case that the sources settle.

Sources (docs/adr/004-vat-readiness-and-samples.md):
- Ángel's VAT rules, final 31/08/2026 (Odoo 19 docs/iva_rules.md, decision log B01/B02): NS = not subject by the
  nature of the product, EX = exempt, NR = carries VAT; customer CAN/COM/TER turns NR into EX.
- Odoo 17 production, server action 1232 «Create Invoice» (read-only): NR -> 21 %; zero-rate lines by customer
  type: Spain -> «0% S», EU -> «0% EU S» (or «21% EU S» with zero amount), third country -> «0% EX S»; concepts of
  type TAX (ARA, IVA, PLA, DUM: paid on behalf) on a tax invoice -> «0% EXEMPT NS».
- Odoo 20 Spanish localization: legal nature and VAT return boxes of each tax template.
Only cases where the three agree get a row; the rest stay «VAT pending» (EX or NS for a Spanish / Canary customer,
NS of CAU and QBR). Taxes are found by their localization template, never by name. Idempotent.
"""
env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname
company = env.ref("base.main_company")
assert company.chart_template == "es_pymes", company.chart_template
tax = env["account.chart.template"].with_company(company).ref
ROWS = [
    ("NR", "any", "any", "account_tax_template_s_iva21s",
     "Ángel 31/08/2026: NR lleva IVA · Odoo 17 acción 1232: NR = 21 % → «21% S» · PGC: sujeta, 303 [07]/[09]"),
    ("EX", "COM", "any", "account_tax_template_s_iva0_sp_i",
     "Ángel: cliente UE → EX · Odoo 17 acción 1232: cliente UE → «0% EU S» · PGC: no sujeta por localización, 303 [59], 349"),
    ("EX", "TER", "any", "account_tax_template_s_iva_e",
     "Ángel: cliente de tercer país → EX · Odoo 17 acción 1232: «0% EX S», 303 [120] · PGC: no sujeta por localización"),
    ("NS", "any", "paid_on_behalf", "account_tax_template_s_iva0_ns",
     "Ángel: NS = no sujeto por naturaleza · Odoo 17: suplidos (conceptos TAX: ARA, IVA, PLA, DUM) en factura de "
     "impuestos con «0% EXEMPT NS», sin casilla 303"),
]
VatTax = env["boss.vat.tax"]
for vat_class, zone, kind, template, source in ROWS:
    odoo_tax = tax(template)
    assert odoo_tax.type_tax_use == "sale" and odoo_tax.company_id == company, template
    row = VatTax.search([("company_id", "=", company.id), ("vat_class", "=", vat_class),
                         ("customer_zone", "=", zone), ("service_kind", "=", kind)])
    values = {"tax_id": odoo_tax.id, "source": source}
    if row:
        row.write(values)
    else:
        VatTax.create({"company_id": company.id, "vat_class": vat_class, "customer_zone": zone,
                       "service_kind": kind, **values})
env.cr.commit()
for row in VatTax.search([("company_id", "=", company.id)]):
    print("VAT", row.vat_class, row.customer_zone, row.service_kind, "->", row.tax_id.name, "|", row.tax_id.description)
