"""Supplier tariffs whose supplier is an address or contact of a company (the add-price dialog proposed the invoice
address of the line's supplier until 04/11/2026): the supplier becomes the company and the name follows the other
tariffs («<company> <service> <route>»). Approved by Belal on 04/11/2026 for the three MSC FMI tariffs of Hong Kong and
Shanghai. Idempotent; prints what it changes; a note stays in each tariff's history.
    dev/server_shell.sh fix_tariff_supplier.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
Tariff = env["boss.tariff"].with_context(active_test=False)  # noqa: F821
for tariff in Tariff.search([("partner_id.parent_id", "!=", False)]):
    address, company = tariff.partner_id, tariff.partner_id.commercial_partner_id
    values = {"partner_id": company.id}
    if not tariff.name.startswith(company.name):
        values["name"] = f"{company.name} {tariff.name}"
    tariff._workflow_write(values)  # an approved tariff: data correction, not a new price
    tariff.message_post(body=f"Supplier corrected: «{address.display_name}» (an address of the company) → «{company.name}».")
    print("FIXED", tariff.id, "|", tariff.name, "| state", tariff.state)
env.cr.commit()  # noqa: F821
print("LEFT", Tariff.search_count([("partner_id.parent_id", "!=", False)]))
