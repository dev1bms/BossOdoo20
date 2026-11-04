Script of the **full trial with Ángel and Cristina** before the live test. Everything is done on
**https://system.bosscontinental.com** with **[PRUEBA]** records: confirming, invoicing, paying and closing are all
safe. Odoo sends nothing outside (mail is switched off during the tests). Remarks go in the **prueba-completa** sheet
(yellow columns).

## How it is organised

| Part | Who | What | Time |
|---|---|---|---|
| 1 | Ángel | Tariffs, quotation, selling price, VAT, invoices and payments | 1 h 30 |
| 2 | Cristina | File, states, customs, documents, consolidation and close | 1 h 30 |
| 3 | Both | The open questions (below) | 30 min |

## Scenarios

| # | Scenario | Where | What to check |
|---|---|---|---|
| 1 | Sea import FCL quotation from the template | Sales → New quotation, template «IMB FOB» | With about 6 entries (customer, template, carrier, origin port, ETA, container) the prices come out; choosing the port fills its country; [[Confirm]] opens a file |
| 2 | Approve the WFS tariff | Pricing & Suppliers → Tariffs and documents, filter «Waiting for approval» | [[Approve]]; then an air import takes the WFS cost by itself |
| 3 | One file from start to end | **E260181** (FCL import) | Follow the **Next step** with [[Go]]: suppliers and costs → orders → In transit → ATA (Arrived) → customs → Delivered → transport order → invoice (paid-on-behalf apart) → supplier bills → ratings → [[Close operations]] → frozen data → financial close |
| 4 | Air import | **E260182** | Handler proposed; ALM by days; house AWB as a draft (⋮ → Print) |
| 5 | Sea export | **E260183** | House B/L as a draft → [[Issue HBL]] → number and date |
| 6 | Consolidation | **E260231** with **E260232** and **E260233** | Cost split, margin of each house and consolidated, master's manifest, HBL of each house |
| 7 | LCL for an agent | **E260184** | In agent business the agent (the orderer) is invoiced |
| 8 | My files | Shipment files | Opens on «My files» and «In progress»; filters «Needs action», «To do in operations», «To invoice or close»; board view |

The pages [Closing](#/cierre), [Consolidations](#/consolidacion) and [Transport documents](#/documentos) explain each
part.

## Questions for the call

| Who | Question |
|---|---|
| Ángel | WFS tariff: approve or return it (point 38) |
| Ángel | Import demurrage: does it end at the pickup at the port or at the empty return? (point 17) |
| Ángel | From 01/01/2027: SII or VERI*FACTU? |
| Ángel | Payment terms of 75 and 90 days from Odoo 17: still used? (the law allows 60 days between companies) |
| Ángel and Cristina | DAP/DDP files: opened at acceptance or when the documents arrive? |
| Cristina | Storage (ALM): her e-mail of 25/09 or the clause in the quotations? |
| Cristina | Check the 7 quotation templates and their prices |
