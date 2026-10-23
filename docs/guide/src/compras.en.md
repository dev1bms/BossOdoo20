BOSS buys from suppliers the services it does not do itself. Each external purchase goes in an Odoo **purchase order**.

## Who executes each service

On the quotation, column **By** of each line says who does it:

- **Supplier**: it is bought. Its cost comes from the supplier tariff (or is typed in **Manual cost**).
- **BOSS**: BOSS does it (consignment, own handling, own truck). No supplier cost and nothing to buy.

The service gives the default (BOSS fees "BOSS", the rest "Supplier"); a mixed service is changed on the line before
acceptance.

A quotation is **not accepted** while a supplier service has an **unknown** cost. Only a sales manager can accept it
anyway, writing the reason in **Accepted without cost because**; the file shows that cost as unknown until the
supplier bill arrives.

## Services to buy

On acceptance, each supplier service goes to the **Services and costs** tab of the file with its own **purchase
basis**: supplier, quantity, unit and currency of the supplier tariff, and the expected cost. The sale is not touched and
a basis is never converted into another (containers, kg, W/M…).

The supplier can be changed while nothing is ordered; once ordered, cancel that purchase order first.

## Requests for quotation

[[Create RFQs]] prepares **drafts**, one per supplier and currency, with only what is still to order. Clicking twice
duplicates nothing (two users at once neither: the second gets a notice). The price is BOSS's expected cost; Odoo does
not replace it with the product cost. Services without supplier are reported.

Nothing is confirmed or sent automatically: a person reviews the draft, adjusts it if needed and clicks **Confirm
Order** on the purchase order.

## Service performed

When the supplier has done the service, click the ✓ icon (**Mark as performed**) on the line: the received quantity
becomes the ordered one. If the product's bill control is "received quantities", only performed services are billed
(decision pending, Ángel A8).

## Vendor bill

It is created from the purchase order (**Create Bill**), with its analytic account. Before posting it:

- each BOSS service line needs the **tax shown on the supplier invoice** (0 % included);
- the service must be **already invoiced to the customer** (Cristina's requirement), unless the extra cost is "covered
  by the agreed price" or "BOSS bears it". An extra cost "needs customer approval" or "disputed" is decided first.

A cost without purchase order (expense, receipt) is entered with [[Cost without purchase order]]: the vendor bill goes
to the file's analytic account.
