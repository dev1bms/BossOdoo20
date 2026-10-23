The system holds example files, with **[DEMO]** customers and tariffs only (illustrative amounts). Nothing is posted or
confirmed to a supplier: purchases are draft RFQs and invoices are drafts. The server has no outgoing mail. They are
rebuilt with `dev/demo_cycle.py` (no duplicates; skipped numbers come from earlier cancelled attempts).

| File | Example | What it shows |
|---|---|---|
| E260001 | MSC sea, 1×20' + 1×40'HC Shanghai → Valencia (S00009) | RFQ to MSC with THC, BL and demurrage; draft invoice of **the THC only** (milestone); extra port occupancy re-invoiced with a reason; the duties (ARA, paid on behalf) are paid and billed by the customs broker **without purchase order**. Margin at acceptance 215 €, forecast 255 € (see "Cost and profitability") |
| E260002 | WFS air, 500 kg Shanghai → Madrid (repeat of S00010) | **Recalculation with actual data**: final AWB 620 kg and collection 3 days later → handling and storage go up; the sale does not change and the forecast margin turns negative: the signal to re-invoice or negotiate |
| E260004 | IRENEO road, delivery in Madrid (repeat of S00011) | Bracket transport and fuel surcharge as a % of the transport |
| E260003 | BOSS consignment only (S00018) | No purchases; **CSA added after acceptance** with a reason: in the sale (135 €), not in the margin at acceptance (90 €) |
| E260009 + E260010 | One quotation, two files (S00019, repeat of S00009) | The 40' container travels on another vessel: its services (40' THC and demurrage) move to E260010; each file with its part of sale (825 € / 400 €), cost and invoice |

What can only be seen on the test database (never posted in the real books): confirmed purchase order, posted vendor
bill, customer credit note, receipt without order and their effect on actual cost and margin. The automated tests of
`boss_expediente` check them on a throw-away database.
