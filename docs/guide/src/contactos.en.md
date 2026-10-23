An Odoo contact is **one record per company or person**, whether customer, supplier or both. It is never duplicated
per role.

## Customer and supplier

In the **Sales & Purchase** tab of the contact:

- **Customer** and **Supplier** are two switches. Once ticked, the contact is listed at once in **Customers** or
  **Suppliers**, before its first document. They are also set by its first sale or purchase.
- A contact can be customer and supplier at the same time (filter **Customer and supplier**).

## Logistic roles and customs

In the same tab:

- **Logistic roles**: shipper, consignee, notify party, agent abroad, carrier (shipping line / airline), haulier,
  air handler / terminal, customs broker, warehouse, insurer. They are fixed values (not free tags), used in searches.
- **EORI**: economic operator number for customs.

On each contact person, **Contact for** says whether it is commercial, operations or accounting. The invoice address is
Odoo's **Invoice** address type.

## Missing data

A **preliminary** contact can be created with its name only and quoted. If it is a customer or supplier, the record shows
**Missing for invoices** in yellow: tax ID, address (street, city, country) and email.

A customer invoice is **not posted** without the customer's tax ID and address (complete invoice to a business,
RD 1619/2012 art. 6). In Odoo 20 "is a company" means "has a tax ID".
