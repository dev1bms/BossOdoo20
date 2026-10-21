Services are **Odoo products of type service** with their original code (THC, BL, DEM…). Sales › Products ›
Products, filter **BOSS services**.

![Service list](img/12-servicios-lista.png)

## Service form

The **BOSS pricing** (Precios BOSS) tab says how it is priced:

![Service form](img/11-servicio.png)

| Field | Meaning |
|---|---|
| Cost source | **Supplier tariff** (automatic calculation), **Manual amount** (freight by offer, paid on behalf), **BOSS own fee** (no cost), **Pending business decision** |
| Calculation method | The usual one; each supplier price may use another when its document says so |
| Open question | Reference in [Pending decisions](#/preguntas) |
| VAT class | NS, EX or NR (VAT rules) |
| Unit and other units | Possible charge bases of the service |
| Odoo 17 code and concept, former codes, replaced by | Traceability and history (e.g. TTE-FCL takes TCC and TTC; FTT is replaced by TTE-CON) |
| Description | What the service is and who provides it (translatable) |

## Create or change a service

1. Sales › Products › [[Nuevo]]: type **Service**, **code**, name (with English translation if wanted).
2. Unit = main charge basis; other units when it can be charged another way (e.g. AWB or shipment).
3. BOSS pricing tab: cost source, calculation method, VAT class.
4. Product sales price: **0** (the price is set on each quotation or in the customer pricelist).

> A service is never created because a tariff is missing: the price is added to a tariff. A pending service exists and
> can be quoted with a manual cost, but it has no invented formula.

Each service has its own page in this guide (side menu, by family).
