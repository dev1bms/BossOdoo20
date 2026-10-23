The customer request is recorded as an **opportunity** in CRM (standard Odoo): customer, salesperson, expected
revenue, stage and activities.

![CRM opportunity with the New quotation button](img/01-oportunidad.png)

1. CRM › [[Nuevo]] (or from the pipeline) and set the **customer** and a clear name, e.g. "Import 2x20' + 1x40'HC
   Shanghai - Valencia".
2. Click [[Nuevo presupuesto]] (New quotation). The quotation is created **linked to the opportunity** with the
   customer, salesperson and team. One opportunity may have several quotations (e.g. one per carrier).

> Pipeline stages and lost reasons are standard; they can be adapted to the Odoo 17 ones (validity and
> alternatives are open questions).

## Shipment data on the opportunity

In the **Shipment** tab of the opportunity, note what the customer asks for, even if data is missing: direction, mode,
incoterm, origin and destination, port and country, what BOSS handles (pickup, customs, main carriage, delivery),
shipper and consignee, goods, packages, weight, volume, containers and **requested services**. [[New Quotation]] takes
it **once** to the quotation; [[Add services]] proposes the requested services. Afterwards each document keeps its own.

Without an opportunity, start from **Sales → New**. For a repeat customer, **Duplicate** a previous quotation: route
and services are copied and prices are looked up again for today; accepted prices, snapshots, file, BL/AWB, invoices
and purchases are never copied.
