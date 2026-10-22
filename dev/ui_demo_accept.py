"""LOCAL copy only (boss_test): accept the priced [DEMO] quotation for the guide screenshots. The VAT mapping uses
three taxes named '(prueba)' that exist only here: on the server the mapping is Ángel's decision (P17)."""
env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname == "boss_test", "local copy only"
company = env.company
Tax = env["account.tax"]
taxes = {k: Tax.search([("name", "=", name), ("company_id", "=", company.id)], limit=1) or Tax.create(
    {"name": name, "amount": rate, "type_tax_use": "sale", "company_id": company.id})
    for k, name, rate in (("nr", "IVA (prueba)", 21.0), ("ex", "Exento (prueba)", 0.0), ("ns", "No sujeto (prueba)", 0.0))}
company.write({f"boss_tax_{k}_id": tax.id for k, tax in taxes.items()})
order = env["sale.order"].browse(17)
lines = order.order_line
env.add_to_compute(lines._fields["boss_vat_status"], lines)
lines._recompute_recordset(["boss_vat_status", "tax_ids"])
order.with_user(env.ref("base.user_admin")).action_confirm()
env.cr.commit()
print("ACCEPTED", order.name, order.state, order.boss_pricing_frozen, len(order.boss_snapshot_ids))
