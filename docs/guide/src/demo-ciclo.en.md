The system holds four example files, with **[DEMO]** customers and tariffs only (illustrative amounts). Nothing is
posted or confirmed to a supplier: purchases are draft RFQs and invoices are drafts. The server has no outgoing mail.
They are rebuilt with `dev/demo_cycle.py` (no duplicates).

| File | Example | What it shows |
|---|---|---|
| E260001 | MSC sea, 1×20' + 1×40'HC Shanghai → Valencia (order S00009) | RFQ to MSC with THC, BL and demurrage; draft invoice of **the THC only** (milestone); extra port occupancy re-invoiced to the customer with a reason; duties (paid on behalf) without supplier yet. |
| E260002 | WFS air, 500 kg Shanghai → Madrid (repeat of S00010) | Handling per chargeable kg, AWB and estimated storage bought from WFS. |
| E260004 | IRENEO road, delivery in Madrid (repeat of S00011) | Bracket transport and fuel surcharge as a % of the transport. |
| E260003 | BOSS consignment only (S00018) | No purchases: the margin after external costs is the sale. |

What can only be seen on the test database (never posted in the real books): confirmed purchase order, posted vendor
bill, customer credit note and their effect on actual cost and margin. The automated tests of `boss_expediente` check
them on a throw-away database.
