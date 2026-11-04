Transport documents are printed from the file. Odoo **sends nothing**: the operator prints or copies and sends.

## Where they are

Press **⋮** next to the file number → **Print**:

| Document | From which file | What it is |
|---|---|---|
| **House bill of lading** | sea file that is not a master | The B/L BOSS issues as NVOCC |
| **House air waybill** | air file that is not a master | BOSS's house AWB, with the master AWB number |
| **Cargo manifest** | master (or single shipment) | One line per house: shipper, consignee, packages, weight, goods, totals |

If a document the file does not have is asked for (an HBL of an air file, the manifest of a house), a page says why
and where to print it. They are printed **in English** for every user: they are international documents.

## House B/L and AWB: draft and issue

- Until it is issued, the document prints with **DRAFT** at the top: it is for the shipper to check.
- [[Issue HBL]] or [[Issue HAWB]] (file header) checks the shipper, consignee, ports, vessel or flight, packages,
  weight, goods and freight (prepaid or collect); on FCL, the number of every container; on air, the master AWB. When
  something is missing, it says so. Then it sets the number (the file's, unless another one is typed) and the date of
  issue, and the button disappears.
- **Freight payable**: proposed from the incoterm (C and D: prepaid; E and F: collect) and editable in **References
  and dates**, next to **Marks and numbers**.
- Originals: 3; when the B/L is a **sea waybill**, «express», zero originals.
- On an LCL house, the containers and seals printed are its master's.

## Transport order

[[Transport order]] (header): PDF for the haulier with the pickup, delivery, containers and goods, without prices or
the customer's reference. It needs the haulier chosen and, on a sea import with delivery, the house B/L released or a
sea waybill (Cristina).

## Data for the customs broker

Tab **Customs** → **Data for the customs broker** and the [[Copy]] button: parties with tax ID and EORI, DUA, route,
vessel, MBL/HBL, containers with seals, goods (HS code, packages, weight, volume), goods value, guarantee, and the
**freight, THC, T3 and insurance** sold to the customer for the customs value (Cristina, A37). It comes in the broker's
language (Spanish by default). A user who does not see the sale gets it without amounts.
