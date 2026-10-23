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

- **Who**: contracting customer, responsible, shipper, consignee, agent, carrier; in **References and dates**, notify
  party, haulier and customs broker.
- **Route**: direction, mode, load type, incoterm, origin and destination, port, country and what BOSS handles (pickup,
  customs at origin, main carriage, customs at destination, delivery).
- **Cargo**: goods, packages, weight, volume, pallets and one row per container with number, seal, full pickup and
  empty return.
- **References and dates**: booking, master/house BL (or AWB), vessel/flight, voyage, customs declaration; planned
  ETD/ETA and actual ATD/ATA in separate fields.
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
