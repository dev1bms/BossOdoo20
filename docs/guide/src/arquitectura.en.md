Three BOSS modules on top of the standard Odoo 20 ones (Product, CRM, Sales, `sale_margin`, Accounting); Odoo's own
code is never modified.

| Module | Responsibility |
|---|---|
| `boss_services` | Catalogue: services (products), charge bases (independent units), Odoo 17 identity, VAT class |
| `boss_pricing` | Supplier tariffs (document, validity, versions, approval), pure-Python **calculation engine** and the single `boss.pricing` service, tariff importer |
| `boss_pricing_sale` | Shipment data on the quotation, cost/sale/VAT per line, add a price from the quotation, freeze, snapshot and re-pricing |

- **One calculation**: `boss.pricing.price_cost()` picks the price ([selection rule](#/seleccion)) and applies its
  method; `explain()` explains it. CRM, quotations and, later, shipment files call it the same way.
- **Service differences = data**: the five methods are generic; each tariff keeps its parameters.
- **Design decisions** are documented as ADRs (repository, `docs/adr`).

## Adding a calculation method

1. New function in `boss_pricing/engine/methods.py` (parameters → amount and steps) and in `METHODS`.
2. Parameter fields on the supplier price and its form.
3. Explanation text in `boss.pricing._explain_step`.
4. Engine tests (without Odoo) and, when a document exists, a reference example.
