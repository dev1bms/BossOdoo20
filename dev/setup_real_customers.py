"""The two customers of the reference cases (Belal 27/10/2026), with their company data from Odoo 17 production (read
on 27/10/2026; partner id in «ref» as O17:<id>): COFITEL (air import offer 05570 / file E260167) and AGUILERA EXTINCION
(FCL import file E260883). Searched first by Odoo 17 id, VAT and name: never created twice. No prices here.
    dev/server_shell.sh setup_real_customers.py"""
from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
Partner = env["res.partner"]
madrid = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "M")], limit=1)
Term = env["account.payment.term"]
# Both customers pay at 25 days in Odoo 17 («25 Days»); boss20 had no such term: the standard one, same as Odoo 17.
term = Term.search([("name", "in", ["25 días", "25 Days"])], limit=1) or Term.create({
    "name": "25 días", "line_ids": [Command.create({"value": "percent", "value_amount": 100, "nb_days": 25})]})
term.with_context(lang="en_US").name = "25 Days"
customer_role = env.ref("boss_expediente.role_customer", raise_if_not_found=False)
CUSTOMERS = [
    (23012, "COFITEL, S.A.", "ESA82595067", "Camino de los Nogales, 2", "28140", "Fuente el Saz del Jarama"),
    (23155, "AGUILERA EXTINCION, S.L.", "ESB80939861", "Julián Camarillo, 26 - 2ª Pl.", "28037", "Madrid"),
]
for o17, name, vat, street, zip_code, city in CUSTOMERS:
    partner = (Partner.search([("ref", "=", f"O17:{o17}")], limit=1) or Partner.search([("vat", "=", vat)], limit=1)
               or Partner.search([("name", "=ilike", name)], limit=1))
    vals = {"name": name, "ref": f"O17:{o17}", "vat": vat, "street": street, "zip": zip_code, "city": city,
            "state_id": madrid.id, "country_id": env.ref("base.es").id, "is_company": True, "lang": "es_ES",
            "customer_rank": 1}
    vals["property_payment_term_id"] = term.id
    if customer_role:
        vals["boss_role_ids"] = [Command.link(customer_role.id)]
    if partner:
        partner.write(vals)
        print("UPDATED", partner.id, name)
    else:
        partner = Partner.create(vals)
        print("CREATED", partner.id, name)
    print("   term:", partner.property_payment_term_id.name, "| pricelist:", partner.property_product_pricelist.name)
env.cr.commit()
