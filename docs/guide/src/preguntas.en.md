Questions that change a calculation or a behaviour, reviewed on 22/10/2026 against the previous projects (Odoo 19
decisions and minutes, the NEW ODOO folder, Odoo 17 production). While a question is open the system does what the
last column says — never an invented value. Amounts are illustrative.

## Approved on 23/10/2026

On 23/10/2026 **Belal approved** the proposed answers to the open questions and the system works that way since then.
**None has been ratified yet by Ángel or Cristina**: each decision in their area (Ángel: finance, VAT, accounts;
Cristina: services, prices, operations) stays «ratification pending» until they confirm it, with date and source. If an
owner decides otherwise, the setting or the data is changed, never interpreted.
Implementation plan in three phases, on the project structure (services, tariffs, quotation, shipment file; standard
Odoo first): **A** configuration or small code (done), **B** development, **C** data only people can give (the system
already takes it). No real tariff is approved on Cristina's behalf.

| Id | Decision approved by Belal | Phase | Status in the system | Ratification |
|---|---|---|---|---|
| P17 | VAT of a Spanish customer on EX services: «0% Exent Art.22» (exempt, art. 22, 303 [60]). Canaries, Ceuta and Melilla: «0% S NS» (not subject by place of supply, 303 [120]); Ceuta and Melilla in zone CAN | A | Done: BOSS VAT table and zone rules. Still open: NS services that are not paid on behalf (CAU, QBR) for Spanish customers | Ángel: pending |
| P03 | Cost in another currency: Odoo rate of the quotation date, frozen on acceptance. QBR only when a USD quotation is invoiced in EUR | A + B | Rate done (company setting). QBR: phase B (Odoo invoices in the order currency; a EUR invoice of a USD order must be designed) | Ángel: pending |
| P30 | The supplier bill **can be posted** when it arrives; what waits is its **payment**, until the customer invoice of the service is posted (exceptions: cost borne by BOSS or covered, freight paid in advance) | A | Done: setting «Block payment (posting allowed)», default. The setting also offers «Warn only» and «Block posting and payment» | Ángel and Cristina: pending |
| P32 | Supplier bills of services by **performed** quantities | A | Done: BOSS services with bill control «received quantities»; «Mark as performed» on the file | Ángel: pending |
| P18 · P37 | Amounts paid on behalf (ARA, IVA, PLA, DUM) on their own account (proposal: 419000); the other accounts per category are set by Ángel | A + C | Set on 23/10 on 419000, but in Odoo it is a **payable** account: the broker's bill cannot be recorded nor the amount invoiced to the customer (checked on 26/10 on the local copy; boss20 has the same setup, defect D-2, not fixed). Odoo 17 does not use 419000 but sub-accounts 419001–419007 (current liabilities). Other accounts: not decided | Ángel: pending |
| P40 | WFS «per 24 hours»: periods of 24 h from arrival | A | Done on the WFS [MUESTRA] prices (still waiting for approval, P19) | Cristina: pending |
| P41 | WFS «per 100 kg»: per 100 kg **or fraction** | A | Done, same | Cristina: pending |
| P29 | WFS tiers: the higher price only on the following days (by day number) | A | Done, same | Cristina: pending |
| P42 | WFS minimum per AWB stay | A | Done, same | Cristina: pending |
| P31 · P38 · P39 · P11 (THC VAT) | What the system already does is confirmed: NIF or other identification of a Spanish customer to post (address only a notice); margin «after external costs» (no internal cost); no Odoo Expenses; THC VAT all EX | A | No change: already in place | Ángel: pending |
| P33 · P35 · P36 · P05 · P06 · P07 · P11 (PAD) · P12 · P14 | What the system already does is confirmed: purchase order for supplier services and paid-on-behalf without order; standard visibility by role; numbering E26xxxx; quotation with a pending cost sent with a notice; re-pricing by the sales manager with a reason; PAD under T3; DEM/OCU/VGM/GLO sold and PFT never; chargeable weight from the AWB or the tariff | A | No change: already in place | Cristina: pending (P33 also Ángel) |
| P43 | Single ALM sale with the values of 25/09 (per 100 kg or fraction and day after 48 h; minimum; from day 8 another price from day 1) | B | Missing: the amounts of 25/09 (Odoo 19, customer storage conditions) and the time-based sale rule. Specification: `docs/especificacion-alm-venta.md` | Cristina: pending |
| P10 · P09 | ETX: bought per master AWB, sold per file. DET: own code when the supplier bills it separately | B | Set up both services (units and pricing method) with the supplier document | Cristina: pending |
| P44 | Special storage with a cargo-type condition; new code for the warehouse outside the airport | B + C | Missing: special tariffs and approval of the code | Cristina and Ángel: pending |
| P19 | Cristina reviews each tariff with its PDF and the examples and approves it | C | Waiting for Cristina. Review table: `docs/revision-tarifas.md` | Cristina |
| P28 | Ask IRENEO for the 2026 tariff or a written confirmation | C | Waiting for Cristina. The IRENEO 2025 tariffs are not extended | Cristina |
| P01 · P02 | Prices agreed per customer in its pricelist; minimum margin with the value set by Ángel | C | Mechanism ready; values missing | Cristina (prices) and Ángel (minimum) |
| P24 | List of «Far East» countries (FuelEU) and «short sea» trades | C | Waiting for Cristina | Cristina |
| P16 | Define the services really used (unit, supplier, document) and retire the rest | C | Waiting for Cristina | Cristina |
| P34 | Closed price for several shipments: customers, duration and maximum quantities of each agreement | C + B | Waiting for Cristina; then the agreement in the system | Cristina |
| P13 | Guarantee (CAU) and insurance (SEG): each value as a tariff with its document | C | Waiting for Cristina + Ángel | Cristina and Ángel |

### Open accounting and tax questions

None has an assumed answer: while they are open, the system does what the last column says.

| Id | Question | Who | Meanwhile (in the system) |
|---|---|---|---|
| P17 (part) | VAT of NS services that are not paid on behalf (CAU, QBR) for a Spanish customer | Ángel | «VAT pending»: the quotation cannot be sent or confirmed |
| P18 | Accounts for amounts paid on behalf, sale and purchase, per concept. 419000 does not work (payable account, D-2); Odoo 17 uses 419001 VAT charged, 419002 duties charged, 419003 VAT borne, 419004 duties borne, 419005 anti-dumping, 419006 and 419007 plastic tax charged and borne | Ángel | ARA, IVA, PLA and DUM on 419000: their supplier bill and their customer invoice cannot be recorded |
| P37 | Income and expense accounts per service or category | Ángel | Those of the product category; nothing invented |
| P03 (QBR) | Bank-loss percentage and how a USD order is invoiced in EUR (exchange difference) | Ángel | Odoo invoices in the order currency; no QBR line |
| P01 · P02 | Value of the minimum margin and who approves selling below it | Ángel (+ Cristina) | No minimum margin |
| P13 | Percentages, rates and minimums of guarantee (CAU) and insurance (SEG) | Cristina + Ángel | No approved values |
| P38 | Internal cost of BOSS own services | Ángel | Margin «after external costs»: not net profit |
| P45 | Sending invoices to the tax agency (SII or VeriFactu) and returns Odoo 20 must prepare from go-live | Ángel | No SII or VeriFactu module installed on boss20 (checked 26/10/2026); nothing is sent |

### Known defects (26/10/2026)

| Id | Defect | Status |
|---|---|---|
| D-1 | A supplier bill created from the purchase order carries every line, also those with quantity 0 (services not performed), and the payment block (P30) counted them | Fixed in code with a test on 26/10 (Belal's decision W04-1); deployment to boss20 pending (task BOSS20-W09) |
| D-2 | Amounts paid on behalf (ARA, IVA, PLA, DUM) on account 419000, a **payable** account: neither the broker's bill nor the customer invoice can be created, also on boss20 | Account map as Odoo 17 (419001–419007) prepared and tested locally (`docs/cuentas-suplidos.md`); the change on boss20 waits for Ángel's approval (task BOSS20-W10) |

Still open (not among the proposals): P20–P23 · P26. The tables below keep the context of each question.

## Closed with a documented answer

| Id | Question | Answer | Source | In the system |
|---|---|---|---|---|
| P04 | Which date picks the tariff version? | Import ETA, export ETD | Ángel, meeting 16/10 | Planned date of the shipment; no supplier exception is written down |
| P08 | Which container types have their own price? | It is data of each document, not a decision | MSC/Hapag/CMA documents | Size and type condition on each price |
| P15 | How do WFS free hours count? | Threshold in real hours: 48 h 00 min is free; once exceeded, billed from the NOA/FOH included, not only the excess | Cristina 08/09 (decision B20, «48.0 h does not exceed, 49 h does») and the WFS 2026 document p.5 item 1 | ALM in threshold mode with the exact hours of the actual period. **How the charged periods are counted (24 h or calendar days) is still open: P40** |
| P25 | Master or house AWB/BL? | Master per shipment file; houses are the exception (≈10 %) | Cristina 28/09 | BL and AWB once per shipment; DOC for the house |
| P27 | Company data, currency, country, chart of accounts | Those of Odoo 17 production: Boss Continental S.L., EUR, Spain, PGC PYMEs 2008 | Odoo 17 company record | Configured on the server |
| P17 (part) | Odoo tax of NR, EX of EU and third-country customers, and NS paid on behalf | NR → «21% S»; EX EU customer → «0% UE S»; EX third-country customer → «0% EX S»; NS paid on behalf → «0% Exent NS» | Ángel's rules 31/08 (B01/B02) + Odoo 17 server action 1232 «Create Invoice» + legal nature in the localization | BOSS VAT table on the server |

## Context of the questions

| # | Id | Question | What it blocks today | Services | Practical proposal | Who | Meanwhile |
|---|---|---|---|---|---|---|---|
| 1 | P17 | **VAT of a Spanish or Canary customer** for EX services (and NS services that are not paid on behalf: CAU, QBR); zone of Ceuta and Melilla | Quotations of Spanish customers with EX services (THC, T3, freight, SEG…) cannot be sent or confirmed | THC, T3, T3-PAD, FMI, FME, FAI, FAE, SEG, DEX, EXW, GAV, DVD, SAD; CAU, QBR | Ángel calls them exempt; Odoo 17 uses «0% S» (subject at 0 %, box 150). Choose an exempt tax with its article (21/22 → «Exempt Art.22», box 60…) or Odoo 17's practice; Canaries: «not subject by place of supply» (box 120). Example: THC of an import from China for a customer in Valencia | Ángel | VAT «pending» only in those cases; NR, EU and third-country customers and amounts paid on behalf already have their tax |
| 2 | P19 | **Approve** the sample/real tariffs after review | Automatic prices on the server (no tariff approved yet) | THC, T3-PAD, BL, GLO-CCC, GLO-FUELEU, DEM, OCU, ALM, HAN, AWB, X-R | Review each tariff with its PDF and examples, then click «Approve» | Cristina (or Belal) | Price «waiting for approval» |
| 3 | P03 | **Exchange rate** for USD costs and the **QBR** rule | USD costs in EUR quotations | Freight in USD, any USD tariff, QBR | Odoo rate of the quotation date, frozen on acceptance; QBR when a USD offer is invoiced in EUR (Cristina's requirement) | Ángel | Line «Other currency, no policy»; QBR pending |
| 4 | P28 | Are the **2025 ground-agent tariffs** valid in 2026? Fuel surcharge rate and date | Road transport and air handling of that agent in 2026 | TTE-CON, FS, SEG, HAN and X-R of that agent | Ask the agent for the 2026 tariff or a written confirmation | Cristina | 2025 samples are not applied to 2026 shipments |
| 5 | — | **Missing tariff documents** (not a decision) | Automatic price of those services | CES, GLO, T3, DOC, ENS/AMS, VGM, FAD, DEX, TRA, EUR1, inspections, warehouse, TTE-FCL, THC-LCL, agents | Collect the current PDFs and enter them | Cristina / operations | «No supplier price» → «Add supplier price» from the quotation |
| 6 | P01 · P02 | **Sale price**: rules per customer (cost + %, margin)? Minimum margin and who approves selling below it? | Automatic sale | All sellable services | The mechanism exists (customer pricelist with fixed price, surcharge on cost, margin on sale, minimum margin); the values per customer are to be decided | Cristina (+ Ángel for the minimum) | Sale agreed in the customer pricelist or typed; never an unapproved rule |
| 7 | P43 | **One ALM sale price**: Cristina (08/10, relayed by Belal; original not seen) said ALM has one sale price for every customer (not negotiated), ALM only; the values are pending. «Highest supplier cost + %» is a **proposal** (Belal 08/10), not approved and without a percentage. Do the values she gave on 25/09 apply (a price per 100 kg or fraction and day from arrival once 48 h are exceeded; a minimum; from the 8th day another price from day 1; recorded in Odoo 19, customer storage terms)? | Automatic sale of ALM | ALM | Confirm values and rule; then the time-based sale rule is built (it does not exist today: a pricelist per shipment cannot express it, and «cost + %» of the chosen supplier is not what was asked) | Cristina | Typed sale; the system proposes no ALM sale price |
| 8 | P13 | **Derived parameters**: customs guarantee (CAU) and insurance (SEG) rates and minimums | CAU and SEG | CAU, SEG | Enter each value as a tariff with its document | Cristina + Ángel | Percentage method available; no approved values |
| 9 | P16 | Services without definition | Those services | VET, GT3, DES, VAC, POS, IMO, DVD, GAV, DUM | Define the ones in real use (unit, supplier, document), retire the rest | Cristina | «Pending decision», manual cost possible |
| 10 | P18 | **Paid on behalf** (ARA, IVA, PLA, DUM): invoicing product and accounting | Invoicing (phase 2) | ARA, IVA, PLA, DUM | Sale = declaration cost (Odoo 17 practice); confirm account and tax | Ángel | Manual amount at cost, class NS |
| 11 | P24 | «Far East» country list (FuelEU) and «short sea» THC trades | FuelEU outside China | GLO-FUELEU, THC | Written list from Cristina | Cristina | MSC sample limited to China |
| 12 | P11 | PAD under T3 or GLO; «THC + port charges» presentation; THC VAT (all EX or partly NR) | THC presentation and VAT | THC, T3-PAD, GLO | Keep T3-PAD; Ángel decides on splitting THC VAT | Cristina + Ángel | T3-PAD priced; VAT from the EX class |
| 13 | P10 | ETX (WFS point 49): concept and unit | ETX | ETX | Purchase per master AWB, sale per shipment (Cristina 08/10); concept to confirm | Cristina | «Pending decision» |
| 14 | P09 | DET: own code or inside DEM? | Detention billed separately | DET, DEM | Own code when the supplier bills it separately | Cristina | DET «pending decision» |
| 15 | P29 | WFS day tiers «up to 7 / more than 7»: the higher price on the following days only or on the whole stay? The document does not say; Cristina's sale rule of 25/09 uses the whole stay («8 days or more … from day 1»), but that is the sale, not the WFS purchase | ALM over 7 days | ALM | Confirm with WFS or with a real bill of more than 7 days | Cristina | «Not decided» on the price: up to 7 periods it is computed; longer, a manual cost with both amounts. Illustrative: 500 kg, 10 days at 10 €/20 € per 100 kg → 650 € or 1,000 € |
| 16 | P12 | Cost services (DEM, OCU, VGM, PFT, GLO): sold, and how? | Their sale | DEM, OCU, VGM, GLO, PFT | DEM/OCU/VGM/GLO sellable (typed or agreed sale); PFT never sold (Cristina 29/09) | Cristina | Configured so |
| 17 | P05 | Send a quotation with a cost still pending? | — | All | Warning, no block | Cristina | Only pending VAT and missing sale price block |
| 18 | P06 · P07 | Tariff change during validity; who re-prices an accepted quotation? | — | All | Re-price with a reason, sales managers only | Cristina | Implemented so |
| 19 | P14 | Chargeable-weight factor when the document is silent | Chargeable weight without AWB | Air and road | AWB chargeable weight or the factor written in the tariff | Cristina | Implemented so: WFS says «peso cargable indicado en el AWB» (p.4); without that weight, «Missing shipment data» (167 or 333 are never assumed). IRENEO writes its factor (333; 167 for ADT) |
| 20 | P20–P23 · P26 | Cost/margin visibility, route offers, alternatives, validity, code merges | — | — | Odoo standard until decided | Cristina | Odoo standard; original codes |
| 21 | P40 | WFS MAD/BCN «por 24 horas»: 24-hour periods from the NOA or calendar days? Evidence conflicts: the document (p.5) says «por 24 horas»; an Odoo 19 script of 10/09 says «Cristina confirmed WFS counts calendar days»; the 25/09 question («4 periods of 24 h or 5 days?») has no recorded answer | ALM amount when the exit time is earlier than the arrival time | ALM | Confirm with a real WFS bill or with WFS | Cristina | «Not decided» on the price: when both counts agree it is computed; otherwise a manual cost with both amounts. Illustrative: Monday 10:00 → Friday 10:00 (96 h), 500 kg at 10 €: 4 periods = 200 € or 5 days = 250 € |
| 22 | P41 | WFS 2026 «por 100 kg» without «o fracción»: pro rata or per fraction of 100 kg? Cristina (08/09) spoke of «fracción de 100 kg» and the WFS 2025 edition said «por fracción»; the 2026 one does not | ALM with a weight that is not a multiple of 100 | ALM | Confirm with WFS | Cristina | «Not decided» on the price. Illustrative: 450 kg, 3 days at 10 €: 135 € or 150 € |
| 23 | P42 | WFS items 1–3: the minimum prints no unit (items 4–5 say «AWB/día», item 6 «por expedición») | ALM of small shipments | ALM | Per AWB stay (when WFS means per day it writes so) | Cristina | Minimum per stay; the price has «Minimum per day» for documents that say so |
| 24 | P44 | Special handler storage (cold room 36 h, dangerous, valuable goods, live animals: WFS items 2–6) and warehouse storage outside the airport (pallet, m³, entries and exits: its own code, Cristina 08/10; VAT and units with Ángel) | Cost of those stays | ALM and a new code | Enter the special tariffs with a cargo-type condition and create the warehouse code once approved | Cristina + Ángel | The WFS ALM tariff is for general cargo: special cargo gets a typed cost. No codes are created without approval |
