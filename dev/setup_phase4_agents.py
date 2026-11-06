"""Agent business data on boss20 (go-live tracker P4-09, documented defaults P37, P12/F0-C58, P03). Commits.
Idempotent.
- The origin agent profit share services (PFT-FCL, PFT-LCL, PFT-AIR) move to the category «Profit share» so they
  book on 705005 / 607401 as in Odoo 17 (they were under local charges).
- A general price list in USD («Tarifa general (USD)») with the same «cost + %» rule as the EUR one, for payers
  invoiced in dollars (agents abroad); chosen on the quotation or set on the agent's contact.
    dev/server_shell.sh setup_phase4_agents.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
company = env.company
profit = env["product.category"].with_context(lang="en_US").search([("name", "=", "Profit share")], limit=1)
assert profit, "category Profit share"
pft = env["product.template"].search([("default_code", "like", "PFT")])
moved = pft.filtered(lambda t: t.categ_id != profit)
moved.write({"categ_id": profit.id})
print(f"OUT profit share services in category «Profit share» (705005 / 607401): {', '.join(pft.mapped('default_code'))} ({len(moved)} moved)")

usd = env.ref("base.USD")
Pricelist = env["product.pricelist"].with_company(company)
usd_list = Pricelist.with_context(lang="en_US").search([("currency_id", "=", usd.id), ("name", "ilike", "general")], limit=1)
if not usd_list:
    usd_list = Pricelist.create({"name": "Tarifa general (USD)", "currency_id": usd.id, "company_id": company.id})
    usd_list.with_context(lang="en_US").name = "General price list (USD)"
    print("OUT price list «Tarifa general (USD)» created")
eur_default = env["product.pricelist"]._get_partner_pricelist_multi([company.partner_id.id])[company.partner_id.id]
rule = env["product.pricelist.item"].search([("pricelist_id", "=", eur_default.id), ("applied_on", "=", "3_global"),
                                              ("base", "=", "boss_line_cost")], limit=1)
if rule and not env["product.pricelist.item"].search_count([("pricelist_id", "=", usd_list.id), ("applied_on", "=", "3_global"),
                                                             ("base", "=", "boss_line_cost")]):
    rule.copy({"pricelist_id": usd_list.id})
    print(f"OUT «cost + {rule.price_markup:g} %» rule copied to the USD price list")
env.cr.commit()  # noqa: F821
print(f"OUT USD price list: {usd_list.display_name}, rules {len(usd_list.item_ids)}")
