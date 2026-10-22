Questions that change a calculation or a behaviour, reviewed on 22/10/2026 against the previous projects (Odoo 19
decisions and minutes, the NEW ODOO folder, Odoo 17 production). While a question is open the system does what the
last column says — never an invented value. Amounts are illustrative.

## Closed with a documented answer

| Id | Question | Answer | Source | In the system |
|---|---|---|---|---|
| P04 | Which date picks the tariff version? | Import ETA, export ETD | Ángel, meeting 16/10 | Planned date of the shipment; no supplier exception is written down |
| P08 | Which container types have their own price? | It is data of each document, not a decision | MSC/Hapag/CMA documents | Size and type condition on each price |
| P15 | How do WFS free days count? | Threshold: once exceeded, billed from day 1 | Cristina 08/09 and the WFS 2026 document | ALM in threshold mode, 24-hour periods; for carriers each document rules (see P29) |
| P25 | Master or house AWB/BL? | Master per shipment file; houses are the exception (≈10 %) | Cristina 28/09 | BL and AWB once per shipment; DOC for the house |
| P27 | Company data, currency, country, chart of accounts | Those of Odoo 17 production: Boss Continental S.L., EUR, Spain, PGC PYMEs 2008 | Odoo 17 company record | Configured on the server |
| P17 (part) | Odoo tax of NR, EX of EU and third-country customers, and NS paid on behalf | NR → «21% S»; EX EU customer → «0% UE S»; EX third-country customer → «0% EX S»; NS paid on behalf → «0% Exent NS» | Ángel's rules 31/08 (B01/B02) + Odoo 17 server action 1232 «Create Invoice» + legal nature in the localization | BOSS VAT table on the server |

## Open, by impact

| # | Id | Question | What it blocks today | Services | Practical proposal | Who | Meanwhile |
|---|---|---|---|---|---|---|---|
| 1 | P17 | **VAT of a Spanish or Canary customer** for EX services (and NS services that are not paid on behalf: CAU, QBR); zone of Ceuta and Melilla | Quotations of Spanish customers with EX services (THC, T3, freight, SEG…) cannot be sent or confirmed | THC, T3, T3-PAD, FMI, FME, FAI, FAE, SEG, DEX, EXW, GAV, DVD, SAD; CAU, QBR | Ángel calls them exempt; Odoo 17 uses «0% S» (subject at 0 %, box 150). Choose an exempt tax with its article (21/22 → «Exempt Art.22», box 60…) or Odoo 17's practice; Canaries: «not subject by place of supply» (box 120). Example: THC of an import from China for a customer in Valencia | Ángel | VAT «pending» only in those cases; NR, EU and third-country customers and amounts paid on behalf already have their tax |
| 2 | P19 | **Approve** the sample/real tariffs after review | Automatic prices on the server (no tariff approved yet) | THC, T3-PAD, BL, GLO-CCC, GLO-FUELEU, DEM, OCU, ALM, HAN, AWB, X-R | Review each tariff with its PDF and examples, then click «Approve» | Cristina (or Belal) | Price «waiting for approval» |
| 3 | P03 | **Exchange rate** for USD costs and the **QBR** rule | USD costs in EUR quotations | Freight in USD, any USD tariff, QBR | Odoo rate of the quotation date, frozen on acceptance; QBR when a USD offer is invoiced in EUR (Cristina's requirement) | Ángel | Line «Other currency, no policy»; QBR pending |
| 4 | P28 | Are the **2025 ground-agent tariffs** valid in 2026? Fuel surcharge rate and date | Road transport and air handling of that agent in 2026 | TTE-CON, FS, SEG, HAN and X-R of that agent | Ask the agent for the 2026 tariff or a written confirmation | Cristina | 2025 samples are not applied to 2026 shipments |
| 5 | — | **Missing tariff documents** (not a decision) | Automatic price of those services | CES, GLO, T3, DOC, ENS/AMS, VGM, FAD, DEX, TRA, EUR1, inspections, warehouse, TTE-FCL, THC-LCL, agents | Collect the current PDFs and enter them | Cristina / operations | «No supplier price» → «Add supplier price» from the quotation |
| 6 | P01 · P02 | **Sale price**: rules per customer (cost + %, margin)? Minimum margin and who approves selling below it? | Automatic sale | All sellable services | The mechanism exists (customer pricelist with fixed price, surcharge on cost, margin on sale, minimum margin); the values per customer are to be decided | Cristina (+ Ángel for the minimum) | Sale agreed in the customer pricelist or typed; never an unapproved rule |
| 7 | — | **Unified ALM sale** (approved as a concept, Cristina 08/10): values | Automatic sale of ALM | ALM | Set the amount or the rule in the general pricelist | Cristina | Typed sale |
| 8 | P13 | **Derived parameters**: customs guarantee (CAU) and insurance (SEG) rates and minimums | CAU and SEG | CAU, SEG | Enter each value as a tariff with its document | Cristina + Ángel | Percentage method available; no approved values |
| 9 | P16 | Services without definition | Those services | VET, GT3, DES, VAC, POS, IMO, DVD, GAV, DUM | Define the ones in real use (unit, supplier, document), retire the rest | Cristina | «Pending decision», manual cost possible |
| 10 | P18 | **Paid on behalf** (ARA, IVA, PLA, DUM): invoicing product and accounting | Invoicing (phase 2) | ARA, IVA, PLA, DUM | Sale = declaration cost (Odoo 17 practice); confirm account and tax | Ángel | Manual amount at cost, class NS |
| 11 | P24 | «Far East» country list (FuelEU) and «short sea» THC trades | FuelEU outside China | GLO-FUELEU, THC | Written list from Cristina | Cristina | MSC sample limited to China |
| 12 | P11 | PAD under T3 or GLO; «THC + port charges» presentation; THC VAT (all EX or partly NR) | THC presentation and VAT | THC, T3-PAD, GLO | Keep T3-PAD; Ángel decides on splitting THC VAT | Cristina + Ángel | T3-PAD priced; VAT from the EX class |
| 13 | P10 | ETX (WFS point 49): concept and unit | ETX | ETX | Purchase per master AWB, sale per shipment (Cristina 08/10); concept to confirm | Cristina | «Pending decision» |
| 14 | P09 | DET: own code or inside DEM? | Detention billed separately | DET, DEM | Own code when the supplier bills it separately | Cristina | DET «pending decision» |
| 15 | P29 | WFS day tiers «up to 7 / more than 7»: by day position or whole stay? | Long ALM stays | ALM | Literal (positional) unless WFS says otherwise | Cristina | Positional (configurable per price). Illustrative: 10 days at 10 €/20 € → 7×10 + 3×20 = 130 € or 10×20 = 200 € |
| 16 | P12 | Cost services (DEM, OCU, VGM, PFT, GLO): sold, and how? | Their sale | DEM, OCU, VGM, GLO, PFT | DEM/OCU/VGM/GLO sellable (typed or agreed sale); PFT never sold (Cristina 29/09) | Cristina | Configured so |
| 17 | P05 | Send a quotation with a cost still pending? | — | All | Warning, no block | Cristina | Only pending VAT and missing sale price block |
| 18 | P06 · P07 | Tariff change during validity; who re-prices an accepted quotation? | — | All | Re-price with a reason, sales managers only | Cristina | Implemented so |
| 19 | P14 | Chargeable-weight factor when the document is silent | Chargeable weight without AWB | Air and road | AWB chargeable weight or the factor written in the tariff | Cristina | Implemented so |
| 20 | P20–P23 · P26 | Cost/margin visibility, route offers, alternatives, validity, code merges | — | — | Odoo standard until decided | Cristina | Odoo standard; original codes |
