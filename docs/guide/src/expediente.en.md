The **shipment file** (expediente) gathers everything of a shipment: who, route, cargo, references, dates, services,
purchases, invoices and profitability. It is in the **Shipment files** app (and in **Sales → Orders → Shipment files**).

## When it opens

- When a quotation with BOSS services is **confirmed**, its file opens (number **E26xxxx**). Confirming again never
  opens a second one.
- If the shipment starts **before** the quotation (pre-alert, documents received), create the file by hand from
  **Shipment files**: it is **preliminary**. When the quotation is accepted, choose that file in the **File** field of
  the quotation (**Shipment** tab).
- A service sold **later** goes in a new quotation linked to the file: button [[Sell another service]].
- One accepted quotation can be shared by **several files** (e.g. a container on another vessel):
  [[Move services to another file]] (see below).

## What it holds

![Summary of file E260001 [DEMO]](img/30-expediente-resumen.png)

- **Who**: contracting customer, responsible, shipper, consignee, agent, carrier and, on air files, the **handler**
  (see «Airline and handler»); in **References and dates**, notify party, haulier and customs broker.
- **Route**: direction, mode, load type, incoterm, origin and destination, port, country and what BOSS handles (pickup,
  customs at origin, main carriage, customs at destination, delivery).
- **Cargo**: goods, packages, weight, volume, pallets and one row per container with number, seal, full pickup and
  empty return.
- **References and dates**: booking, master/house BL (or AWB), vessel/flight, voyage, customs declaration; planned
  ETD/ETA and, with **date and time**, the actual ones: ATD, ATA, NOA (handler's arrival notice), FOH (freight on hand
  at the terminal, export), actual pickup and actual delivery.
- **Events**: milestones, incidents and notes with date and user; plus the chatter with activities and attachments.

The file data is copied **once** from the accepted quotation. Afterwards each keeps its own: the quotation what was
agreed, the file what really happens. **Summary → Differences with the quotation** shows what changed (containers,
weights, carrier, dates). Nothing is synchronised automatically.

## States and closing

[[In transit]] → [[Delivered]] → [[Close operations]]. The **financial** close is separate:
[[Close financially]] is only allowed with everything invoiced, every cost billed or closed, variances reviewed and
nothing in draft. The yellow **To do** notice says what is missing.

## Analytic account

Each file has its analytic account (plan **Shipment files**). It is set on the sale lines, on the purchase lines and,
from them, on the invoices. Cost and revenue of each shipment are read from accounting, never typed.

## Recompute the expected cost with the actual data

When the shipment data change (containers in **Cargo**, weight, volume, AWB weight, actual ATA/ATD, supplier) or the
**days** of a time-based service (column **Days** in **Services and costs**: storage, demurrage, port occupancy), click
[[Recompute expected cost]]. The same calculation as on the quotation runs with the file data:

- each service to buy takes its new quantity and cost; the **Cost recalculations** tab keeps before/after, user, date,
  data used and the explanation;
- the **accepted sale and its snapshot do not change** (to charge more use [[Add a service]] or Re-invoice);
- draft RFQs follow; a confirmed order is not touched: the service shows **Order to review** and the forecast final cost
  uses the latest data.

Example: ALM quoted with 5 days (2 free, 25 €/day → 75 €); the container is collected on day 9 → 175 €. A second 40'
container in **Cargo** → THC 2 × 240 € = 480 €.

![Cost recalculations of the WFS file [DEMO]: AWB 500 → 620 kg and storage 3 days longer](img/32-expediente-recalculos.png)

## Actual dates and the period of time-based services

Cristina (26/10/2026): ATA and actual pickup with date and time, and the system computes the dates. Each time-based
service (ALM, DEM, OCU, DET) takes its period from **the events its tariff states** («Period starts at» and «Period ends
at» of the supplier price) or, when the tariff states none, from those of its service. When a date of the file or of a
container is saved, the expected cost is recomputed by itself (reason «File dates changed» in **Cost recalculations**
and an event):

| Service | Starts | Ends | Source |
|---|---|---|---|
| ALM air import | NOA (or ATA without NOA) | Actual pickup | Cristina 25/09; WFS «from the NOA» |
| ALM air export | FOH | Actual departure (ATD) | Cristina 25/09 (ETD; the actual one once known) |
| ALM groupage import | Emptying (LCL) | Pickup | Cristina 25/09 |
| DEM import | Vessel arrival (ATA); Hapag: vessel discharge | Empty return **of each container** | MSC p.18; Hapag MHD/DTD |
| OCU import | Vessel arrival | Full out **of each container** | MSC p.17 |
| DET export | Empty pickup of each container | Full gate-in at the terminal | MSC p.10 |

The dates of each container are in **Cargo** (empty pickup, full in terminal, full pickup, empty return). When the
containers have different dates, each one is priced on its own period and the cost is the sum (the recalculation shows
«Per container: …»). The «Period from» column of **Services and costs** says which events are used. When a person types
the period on the service line, it is flagged **Period set by hand** and the dates no longer change it. The accepted
sale does not change.

![File E260015: demurrage per container after saving the ATA and the container dates](img/43-periodo-por-contenedor.png)

## Airline and handler (air)

**Shipment files → Airlines and handlers** says which handler serves each airline at each airport (loaded from the
Odoo 17 configuration on 26/10/2026: MAD, BCN, VLC, AGP, BIO; maintained by purchasing and the sales manager). On an
air file:

- with **one** known handler for the airline and the airport, the **Handler** field fills in by itself;
- with **several** (for example an airline served by WFS or by Iberia in Madrid), nothing is chosen for you: the field
  only offers those handlers;
- with none recorded, choose freely among the contacts with the role «Air handler / terminal»;
- when the airline or the airport changes, the previous handler is replaced by the new one if there is only one.

HAN, ALM, AWB, ETX and X-R are bought from the handler: on the quotation the line takes the handler as supplier when it
is the only one (only its tariff prices it); on the file, the services not ordered yet move to the chosen handler and
their cost is recomputed (reason «Handler changed»).

## Summary by service group

The **Summary** tab starts with the table of the Odoo 17 «Resumen»: one row per **service group** (Freight, Inland
transport, Local charges, Customs, Storage and warehouse, Insurance and courier, Profit share, Duties and taxes paid on
behalf; the group is the product category) and a Total row, with the **agreed, invoiced and to-invoice sale**, the
**cost still expected** (services without a vendor bill yet), the **actual cost** (posted vendor bills and credit
notes), the **forecast cost** and the **forecast margin**. Company currency, without taxes. The Total row equals the
figures below it (agreed sale, forecast cost, forecast margin). Sales managers and accounting only.

## Cost forecast

**Shipment files → Cost forecast** (also pivot and graph views in **Services to buy**) adds up the expected cost of the
services to buy of the open files, by supplier and **forecast**: *Estimated (quotation)* → *Recomputed with the file
data* → *Ordered to the supplier* → *Confirmed by the supplier bill*. It shows which forecasts are still estimates and
which a document already confirmed («Nuevo Odoo», previsiones sheet). It can also be grouped by service, file, customer
or state.

![Cost forecast by supplier and forecast](img/44-prevision-costes.png)

## One quotation, several files

[[Move services to another file]] moves part of the accepted quantities to another file of the same customer (new or
existing). The **Sold services** tab shows the part of each line in this file: all files together never exceed what was
accepted, the price does not change, each file invoices its part and the analytic account of the line is split in
proportion. A service already ordered from the supplier is reduced on its order first.

![Sold services: part of the quotation in this file](img/33-servicios-vendidos.png)

![Move services to another file](img/34-mover-servicios.png)

## Add a service after acceptance

[[Add a service]] (sales manager) adds a new service to the accepted order with its price and the reason: done by
**BOSS** (no supplier cost) or by a **supplier** (it becomes a service to buy). The accepted lines and their snapshot do
not change; a new snapshot "Service added after acceptance" is kept and the line stays out of the margin at acceptance.

![Add a service after acceptance](img/35-anadir-servicio.png)
