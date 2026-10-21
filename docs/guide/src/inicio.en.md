This guide explains the BOSS pricing system on Odoo 20 as it is implemented. It works in the standard **CRM**
and **Sales** screens; the BOSS parts are added there.

> Every amount, customer and supplier in the pictures and examples is **illustrative** (for instance
> «Naviera Ejemplo»). Real supplier prices live in Odoo with their document and are not published here.

## The cycle in seven steps

1. **Opportunity** in CRM with the customer and the request.
2. **Quotation** created from the opportunity, with the **shipment data** ([[Envío]] tab).
3. **Services**: [[Añadir servicios]] button; one line per service and, for container services, per size and type.
4. **Cost**: each line looks for the approved supplier price and explains the calculation.
5. **Missing price**: the system says what is missing (shipment data, tariff, approval, decision) and opens the right
   form; after saving, you are back on the quotation.
6. **Sale and VAT**: sale price per line, margin and markup, VAT from the BOSS rules.
7. **Send and accept**: confirming freezes the prices and keeps a **snapshot** of the calculation. Any later change
   goes through [[Recotizar]] with a reason.

## Principles

- **One service = one Odoo product** with its code (THC, BL, DEM…). See [Service catalogue](#/catalogo).
- **The supplier price lives in a tariff**, with its document, page, validity and approval. It is never typed on the
  quotation. See [Enter a tariff](#/tarifa-alta).
- **One calculation** for every screen; the result always states its status: priced, missing data, no price, waiting
  for approval, on request, several prices, manual amount, other currency.
- **Zero is not free**: a zero sale price means "price missing" unless "Free of charge" is ticked.
- **Nothing is guessed**: an undecided business rule stays "pending decision". See [Pending decisions](#/preguntas).

## Where things are

| What | Menu |
|---|---|
| Opportunities | CRM |
| Quotations and orders | Sales › Orders |
| Supplier tariffs | Sales › Products › Supplier tariffs |
| Supplier prices (all lines) | Sales › Products › Supplier prices |
| Services | Sales › Products › Products ("BOSS services" filter) |
| Ports and airports | Sales › Configuration › Ports and airports |
| VAT of services and currency | Settings › Sales › Pricing |
