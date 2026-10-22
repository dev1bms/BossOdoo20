A complete walkthrough on **https://system.bosscontinental.com** with test data marked **[DEMO]** (fictitious
customer, carrier, haulier and handler, fictitious prices). The test customer has no e-mail: nothing is sent to anyone.

## What is prepared

| Data | Content |
|---|---|
| Customers | [DEMO] Cliente Ejemplo, S.L. (Valencia) and [DEMO] Cliente UE Ejemplo GmbH (Hamburg), with the pricelist «[DEMO] … acuerdo de precios»: THC agreed at 230 € per container; DEM cost + 15 % with a minimum margin of 30 € per container; the rest cost + 15 % |
| Tariffs | [DEMO] Naviera Ejemplo (THC per container, DEM per day), [DEMO] Transportista Ejemplo (transport per container and an 8 % fuel surcharge), [DEMO] Handler Aéreo Ejemplo (ALM with 48 h and the Saturday rule, HAN per kg). **Sent for approval, not approved** |
| Opportunities | «[DEMO] Importación 2x20' + 1x40'HC Shanghái - Valencia», «[DEMO] Importación 1x40'HC Shanghái - Valencia para cliente UE» and «[DEMO] Importación aérea 500 kg Shanghái - Madrid» |
| Missing on purpose | CES (container release): to try «Add supplier price» |

![Test tariffs sent for approval](img/18-prueba-tarifas.png)

## Steps that need a specific person

| Step | Who | Where |
|---|---|---|
| A. Approve the three [DEMO] tariffs (check document and prices) | **Belal** (approver) | Sales › Products › Supplier tariffs › open › [[Approve]] |
| B. Decide the tax of EX for Spanish customers (P17) | **Ángel** | Then one row in Sales › Configuration › BOSS VAT table |
| C. Approve the CES price added from the quotation | **Belal** | From the line (review icon) or the tariff list |

The VAT of NR, of EU and third-country customers and of amounts paid on behalf is already in the table. Without step
B, the **Spanish customer's** quotation stays «VAT pending» only because of THC (EX) and cannot be sent or confirmed:
that is expected. The **EU customer's** quotation goes all the way to acceptance.

## Sea (FCL) walkthrough

1. **CRM** › opportunity «[DEMO] Importación 2x20'…» › [[New quotation]].
2. **[[Shipment]]** tab: Import · Sea · FCL · carrier «[DEMO] Naviera Ejemplo» · port ESVLC · country China · planned
   date 04/11/2026 · containers 2 × 20' DV and 1 × 40' HC · days 12.
3. [[Add services]]: THC, DEM, TTE-FCL, FS and CES → one line per container size.
4. **Cost**: THC 150 € and 200 € per container; DEM estimate 12 days (7 free): 5 × 30 € per container; transport 320 €
   per container; FS 8 % of the same haulier's transport; CES **No supplier price**.
5. **Sale** (Sale column): THC 230 € «Agreed price»; the rest «From the expected cost» (+15 %); DEM 180 € because the
   minimum margin of 30 € per container applies.
6. **CES**: icon [[Add supplier price]] → 45 € per container, page 3, attach any test PDF → [[Save price]] → «Waiting for
   approval» → step C → CES with cost and sale.
7. **VAT**: DEM, transport, FS and CES (NR, customer in Valencia, import from China) → 21% S; THC (EX, Spanish
   customer) → **VAT pending** with the reason. [[Send]] or [[Confirm]] say that only the THC VAT is missing.

## EU customer walkthrough (to acceptance)

1. Opportunity «[DEMO] Importación 1x40'HC … para cliente UE» › [[New quotation]] › Shipment as above with 1 × 40' HC
   and days 10.
2. [[Add services]]: THC, DEM, TTE-FCL and FS. VAT of every line: **0% EU S** (EX for an EU customer).
3. **[[Confirm]]** (do not use Send with real customers) → prices frozen, snapshot in **Pricing history** with each
   line's tax, [[Re-price]] button.

![Accepted quotation of an EU customer](img/13-oferta-aceptada.png)

## Air walkthrough

1. Opportunity «[DEMO] Importación aérea 500 kg…» › [[New quotation]] › Shipment: Import · Air · airport MAD · country
   China · date 04/11/2026 (Wednesday) · chargeable weight (AWB) 500.
2. [[Add services]]: ALM and HAN. ALM says **«Missing shipment data: days»** until days are given; HAN takes 500 kg from
   the AWB: 500 × 0.08 € = 40 €.
3. Days 4 → ALM 4 periods × 5 (100 kg) × 10 € = 200 € (past 48 h it is billed from day 1).
4. Date 07/11/2026 (Saturday) and days 3 → ALM 0 € (free until Monday included).

![Air test quotation: ALM and HAN](img/19-prueba-aereo.png)

## Checked on the server

The whole walkthrough was run on the server as a test salesperson and a test approver, inside a transaction rolled
back at the end (the database does not change): 28 checks passed, including acceptance of the EU customer's quotation
with the real VAT table.
