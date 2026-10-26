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

![Services and costs of file E260001 [DEMO]](img/31-expediente-servicios.png)

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
(BOSS services use «received quantities», proposal approved by Belal on 23/10/2026, P32; Ángel's ratification pending).

## Vendor bill

It is created from the purchase order (**Create Bill**), with its analytic account. Before posting it, each BOSS service line needs the
**tax shown on the supplier invoice** (0 % included).

**Order of work** (proposal approved by Belal on 23/10/2026, P30; Ángel's and Cristina's ratification pending): the supplier bill is **posted on time**; its **payment** waits until the
service is on a **posted** customer invoice. Meanwhile the vendor bill shows a yellow notice ("Before posting or paying")
and the file lists it; registering the payment is blocked. Setting: **Settings › Sales › Supplier bill before the
customer invoice** = "Block payment (posting allowed)". No notice: cost covered by the price or borne by BOSS; **Paid in
advance** (freight paid to an agent: the sale line is enough).

A cost without purchase order (expense, receipt) is entered with [[Cost without purchase order]]: the vendor bill goes
to the file's analytic account.

## Paid on behalf: duties and VAT of the customs declaration

Amounts paid in the customer's name (ARA, IVA, PLA of the declaration) are not requested with an RFQ: the customs broker
pays them and bills them at cost. The service is **Billed without purchase order**, with the file's customs broker as
supplier and the state "Bill without order expected". Its bill is entered with [[Cost without purchase order]] and
matched to the service by product and analytic account (never counted twice).

## Partial, cancelled orders and supplier replacement

- **Partial**: reduce the quantity on the RFQ before confirming it; the rest goes back to [[Create RFQs]].
- **Cancelled**: the quantity of a cancelled order is to order again.
- **Another supplier**: cancel the active order, change the supplier of the service and click
  [[Recompute expected cost]]: the tariff of the new supplier applies.
- **Another purchase basis**: before ordering, the purchase unit can differ from the sale unit (sold per shipment,
  bought per kg): the sale does not change and a unit is never converted into another.
