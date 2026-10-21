Business decisions that change a calculation or a behaviour and have no documented answer yet. Until they are decided,
the system does what the last column says — never an invented value.

| Id | Question | Who | Meanwhile in the system |
|---|---|---|---|
| P01 | May the system **propose** a sale price from a rule (markup % or margin %) that a person then confirms? | Cristina | Sale price typed or agreed in a pricelist; markup and margin shown separately |
| P02 | Minimum margin; who approves selling below it; per unit, line or quotation? | Cristina + Ángel | Margin shown per line and quotation; no block |
| P03 | **Exchange-rate** policy for USD costs and the bank-loss (QBR) rule | Ángel | No conversion: the line shows "other currency"; QBR pending |
| P04 | Which date chooses the tariff version (ETA import / ETD export; supplier exceptions) | Ángel / Cristina | Planned date of the shipment |
| P05 | May a quotation be sent/confirmed with a **cost** still pending? | Cristina | Warning only; only VAT pending and missing sale price block |
| P06 | Tariff change during the quotation validity: keep the price or re-quote? | Cristina + Ángel | Accepted quotations never change by themselves; drafts with "Update costs" |
| P07 | Who may **re-price** an accepted quotation? | Cristina | Sales administrators |
| P08 | Container types with their own price (HC, reefer, OT/FR) | — | Size and type conditions on each price (supplier data) |
| P09 | **DET**: own code or inside DEM? | Cristina | DET pending decision |
| P10 | **ETX** (handler maintenance surcharge): concept, unit, scope | Cristina | ETX pending decision |
| P11 | PAD under T3 or GLO; "THC + port charges" presentation; THC VAT split | Cristina + Ángel | T3-PAD priced; VAT from the service class |
| P12 | Cost-only services in Odoo 19 but sold in Odoo 17 (DEM, OCU, VGM, PFT, GLO) | Cristina | They can be quoted; sale price typed |
| P13 | Derived parameters (customs guarantee, insurance rates and minimums) | Cristina + Ángel | Percentage method available; no values loaded |
| P14 | Chargeable-weight factors when the document gives none | Cristina | AWB chargeable weight or the factor written on the price |
| P15 | Day counting: is the arrival day day 1? Calendar days or 24-hour periods? | Cristina | Days/periods estimated on the quotation |
| P16 | Services without definition (VET, GT3, DES, VAC, POS, IMO, DVD, GAV, DUM) | Cristina | Pending decision; manual cost possible |
| P17 | **VAT**: Odoo tax for NR / EX / NS; Ceuta and Melilla; chart of accounts | Ángel | VAT pending → the quotation cannot be sent or confirmed |
| P18 | Amounts paid on behalf (duties, plastic tax, import VAT): accounting and VAT | Ángel | Manual amount |
| P19 | Who approves tariffs? | Cristina | "Approver" group (administrator by default) |
| P20 | Who sees cost and margin? | Cristina | All Sales users |
| P21 | One quotation per shipment or rate offers per route? | Cristina | One quotation = one shipment |
| P22 | Alternatives (several carriers) in one document | Cristina | Several quotations under one opportunity (standard) |
| P23 | Default validity and expiry | Cristina | Standard Odoo validity |
| P24 | "Far East" country list (FuelEU) and short-sea trades | Cristina | MSC sample limited to origin China |
| P25 | AWB: master per file or house per AWB | Cristina | Per air waybill |
| P26 | Proposed merges of codes (consignment fees, AMS/ENS, inspections) | Cristina | Original codes kept |
| P27 | Company set-up in Odoo 20 (name, EUR, country, localisation) | Belal / Ángel | Not changed (needs authorisation) |
| P28 | Are the 2025 ground-agent tariffs valid in 2026? Fuel surcharge rate and date | Cristina | Samples valid in 2025 only |
| P29 | "Up to 7 days / more than 7 days" tiers: per day position or whole stay? | Cristina | Per day position (configurable per price) |
