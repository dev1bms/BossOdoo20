The **shipment file** (expediente) gathers everything of a shipment: who, route, cargo, references, dates, services,
purchases, invoices and profitability. It is in the **Shipment files** app (and in **Sales → Orders → Shipment files**).

## When it opens

- When a quotation with BOSS services is **confirmed**, its file opens (number **E26xxxx**). Confirming again never
  opens a second one.
- If the shipment starts **before** the quotation (pre-alert, documents received), create the file by hand from
  **Shipment files**: it is **preliminary**. When the quotation is accepted, choose that file in the **File** field of
  the quotation (**Shipment** tab).
- A service sold **later** goes in a new quotation linked to the file: button [[Sell another service]].
- An agreement for several shipments: each shipment is a repeated quotation (Duplicate), hence its own file.

## What it holds

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
