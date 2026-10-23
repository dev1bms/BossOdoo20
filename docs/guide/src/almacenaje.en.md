Airport storage (**ALM**): what the system covers, which data it needs, how purchase and sale are computed and what is
still waiting for a decision. **Illustrative** amounts (real supplier prices are not published).

## Status on 23/10/2026

| Case | Supplier document | In the system | Status |
|---|---|---|---|
| WFS MAD/BCN import, general cargo | WFS V 2026-02 (from 01/06/2026) p.5 item 1 | Sample tariff waiting for approval | **Partly automatic**: only when the readings not decided (P29, P40, P41) give the same amount |
| WFS MAD/BCN export, general cargo | Same item (export prices and minimum) | Sample tariff waiting for approval | **Partly automatic**, like the import (FOH → ETD) |
| WFS VLC | p.5 (per calendar day, 3 days; Friday with a Monday exit, 4) | No tariff | Mechanics ready (calendar days); tariff missing |
| WFS cold room, dangerous, valuable goods, live animals | Items 2–6 (other free hours, prices and minimums) | No cargo-type condition | **Manual cost** (P44) |
| IRENEO warehouse MAD/BCN | 2025 tariffs (per 100 kg or fraction and calendar day, 333 kg/m³) | No tariff | 2026 validity unconfirmed (P28) |
| Warehouse outside the airport (pallet, m³, entry/exit) | — | Not ALM | Own code pending Cristina and Ángel (P44) |
| Storage included in a package (e.g. IRENEO export: 3 calendar days inside the handling) | IRENEO p.4 | The package is HAN | The included days are entered as the free period of that supplier's ALM tariff (as IRENEO writes it): only the days after are charged. Without that tariff there is no automatic check: do not add ALM for the package days |
| Storage at the port (containers) | Carriers | DEM / OCU / DET | Not ALM |

Sale: **no automatic rule**. Cristina (08/10) asked for one ALM sale price for every customer; the values are not
approved (P43). Meanwhile the sale price is typed on the line.

## 1. Data it needs

| Data | Where | What for |
|---|---|---|
| AWB chargeable weight | Quotation, Shipment tab; file | WFS charges on «el peso cargable indicado en el AWB». Without it: «Missing shipment data» (167 or 333 are never assumed) |
| Airport, direction and planned date | Quotation, Shipment tab | They choose the tariff (MAD/BCN, import or export) and its version |
| Storage days (estimate) | Quotation, Shipment tab (or the line) | Estimated cost on the quotation. Not indicated: data missing; 0 indicated is a valid estimate |
| Period start and end | File, ALM line (and «Test pricing») | Cost of the actual period: import NOA → pickup; export FOH (warehouse entry) → ETD (Cristina 25/09) |

Times are typed in Madrid time (Canary Islands: Canary time). The system subtracts both moments in exact hours, also
across the change of time.

## 2. How the tariff is defined

On the supplier price (Pricing & Suppliers → Prices), service ALM, charge basis **Shipment**:

| Field | WFS MAD/BCN general cargo | Why |
|---|---|---|
| Calculation | Per day with free period | — |
| Priced on | AWB chargeable kg · size 100 | «por 100 kg» |
| Or fraction / not decided | «Or fraction» unticked · **«Or fraction not decided»** ticked | 2026 does not say «o fracción» (P41) |
| Days counted as | **Not decided** (24 h or calendar days) | «por 24 horas» against the note of 10/09 (P40) |
| Free hours | 48 · **Threshold** mode | «Franquicia de 48 horas … se facturará desde el NOA, incluido» |
| Free if Friday to Monday | 72 | «viernes y salida en lunes, 72 horas» |
| Saturday until Monday | Ticked | «en sábado, franquicia hasta el lunes incluido» |
| Tiers | Up to 7 · More (0) · **Not decided** mode | «Hasta 7 días / Más de 7 días» (P29) |
| Minimum | The document's · «Minimum per day» unticked | No unit printed: per stay (P42) |

Once Cristina decides a reading, that field is changed in a **new version** of the tariff and the calculation becomes
automatic in every case.

![Demo ALM price: free hours, Friday to Monday, Saturday until Monday and the three readings «not decided»](img/37-alm-precio.png)

**What is shown and what is computed.** The quotation and file line is **1 Shipment** with the total storage amount;
the internal calculation is «units of 100 kg × periods × price». The total is computed once and is not multiplied again
when it goes to the sale or to the purchase order (1 × total).

## 3. How the purchase is computed

Illustrative tariff with the same fields as the WFS one (readings not decided included): 500 kg = 5 units, 10 € per unit
and period up to 7, 20 € after, 48 h free, minimum 50 €.

| Arrival (NOA) → exit | Hours | Result | Why |
|---|---|---|---|
| Mon 10:00 → Wed 10:00 | 48 h 00 | **0 €** | Does not exceed 48 h (truly free: no minimum) |
| Mon 10:00 → Wed 10:01 | 48 h 01 | **150 €** | Exceeded: from the NOA, 3 periods (and 3 calendar days) × 5 × 10 |
| Fri 09:00 → Mon 08:00 | 71 h | **0 €** | Friday with a Monday exit: 72 h free |
| Fri 09:00 → Mon 10:00 | 73 h | **200 €** | Over 72 h: 4 periods from the NOA |
| Fri 09:00 → Sun 11:00 | 50 h | **150 €** | Leaves on Sunday: the 48 h apply |
| Sat 09:00 → Mon 23:59 | 63 h | **0 €** | Saturday: free until Monday included |
| Sat 09:00 → Tue 08:00 | 71 h | **no automatic price** | Outside the exception: 3 periods of 24 h (150 €) or 4 calendar days (200 €), P40 |
| Mon 10:00 → Thu 22/10 10:00 | 240 h | **no automatic price** | 10 periods: day by day 650 €; whole stay 1,000 € (and two other amounts with calendar days), P29 |
| 80 kg, Mon 10:00 → Thu 09:00 | 71 h | **minimum** | Every reading stays below the minimum |

With «no automatic price» the line says **«Not priced automatically»**, shows each possible amount and the cost is
typed by hand (supplier bill or quote). On a quotation such a line is not accepted without a cost: it is a supplier
service with an unknown cost.

**Quotation estimate.** With days, no hours: 48 h free = up to 2 days; the Friday and Saturday exceptions are not
assumed (they depend on the exit day) and the explanation says so. Example: planned arrival on a Saturday, 3 days →
estimated as charged; with the actual period the exception applies if it leaves on Monday.

![Quotation: estimate of 3 days from a Friday; the Friday exception is not assumed and it says so](img/38-alm-oferta-estimacion.png)

![Quotation of 10 days: «Not priced automatically», one amount per reading that changes it (here, the tiers)](img/39-alm-sin-precio-automatico.png)

![Test pricing with the actual period: Friday 09:00 → Monday 10:00 = 73 h, 72 h exceeded, 4 periods from the start](img/40-alm-probar-periodo-real.png)

## 4. Sale

- The ALM sale is **not computed by itself**: there are no approved values for the single price (P43). The sale price is
  typed on the line (or a customer pricelist is used if one was agreed).
- The accepted price does not change when the stay changes: the cost difference shows on the file and is decided
  (charge the customer with «Re-invoice to the customer», or BOSS bears it).
- «Highest supplier cost + %» is a proposal not approved: the system does not apply it.

## 5. From quotation to bill: three different amounts

| Amount | Where | What it is |
|---|---|---|
| **Estimate** | Quotation (and snapshot at acceptance) | Assumed days; not a real cost |
| **Computed with the actual period** | File, «Services and costs» tab, after «Recompute expected cost» | Actual start and end with the tariff; kept in «Cost recalculations» with its data |
| **Accounting cost** | Posted supplier bill | What counts in the final profitability |

Steps:

1. **Quotation**: enter the chargeable weight, airport and estimated days; ALM shows the estimate and its assumptions.
2. **Accept**: the quotation snapshot (cost, sale and days) is kept and the file opens with the purchase need.
3. **File**, «Services and costs» tab: on the ALM line type the **Period start** (NOA or FOH) and the **Period end**
   (pickup or ETD) and click **Recompute expected cost**. The expected cost and the days change; the accepted sale does
   not; the change is kept in «Cost recalculations». When the readings not decided give different amounts, the expected
   cost does not change and the recalculation shows every amount: type the «Expected unit cost» by hand.
4. **Purchase**: «Create RFQs» creates one ALM line per file (1 × total) to the supplier; while the RFQ is a draft the
   recalculation updates it; once the order is confirmed it is not changed and is flagged «Order to review».
5. **Supplier bill**: from the order. Only **posted** bills count (a draft is not a cost); a credit note lowers the
   billed amount. The file compares the billed amount with the ordered or expected one («Variance»).
6. **Difference**: if the bill is higher because of more days, «Re-invoice to the customer» with a reason, or leave it
   as borne by BOSS («Variance reviewed» and its note). Recomputing again creates no new costs, orders or repeated
   recalculations.

![File: ALM line with the period start and end, counted days and expected cost](img/41-alm-expediente-periodo.png)

![Cost recalculations: 150 → 0 (Friday to Monday, 71 h), 0 → 200 (73 h) and «no automatic calculation» when the stay goes on](img/42-alm-recalculos.png)

Screenshots of the local test database with [DEMO] data (fictitious amounts; that database's currency is USD).

## 6. What is automatic and what needs a person

- Automatic: choosing the tariff, counting hours and days, the 48 h franchise, the Friday and Saturday exceptions with
  the actual dates, the minimum, the history of recalculations, the order-to-review flag and the comparison with the
  bill.
- Needs a person: approving the tariff (P19), typing the cost when the readings not decided differ, the ALM sale (P43),
  special cargo (P44) and deciding what to do with a difference.
- Needs a decision by Cristina: P29 (tiers), P40 (24 h or calendar days), P41 (fraction of 100 kg), P42 (unit of the
  minimum), P43 (single sale), P44 (special storage and warehouse outside the airport).

## 7. Try it yourself ([DEMO] on the server)

Fictitious records ([DEMO] customer, handler and prices; nothing posted or sent):

| Record | What it shows |
|---|---|
| [Tariff [DEMO] Handler ALM 2026](https://system.bosscontinental.com/odoo/action-boss_pricing.boss_tariff_action/29) | The fields of section 2 with readings «not decided» |
| [Quotation S00020](https://system.bosscontinental.com/odoo/action-sale.action_quotations_with_onboarding/20) | Accepted: estimate of 3 days from a Friday (150) and a typed sale (180) |
| [File E260011](https://system.bosscontinental.com/odoo/action-boss_expediente.boss_expediente_action/11) | Period Friday 16/10 09:00 → Monday 19/10 08:00 (0), 10:00 (200), RFQ P00004; extended to 26/10 (no automatic calculation) |
| [Quotation S00021](https://system.bosscontinental.com/odoo/action-sale.action_quotations_with_onboarding/21) | 10 days: «Not priced automatically» with both amounts |

Steps to try:

1. In **E260011**, «Services and costs» tab, change the **Period end** of the ALM line (for example Monday 19/10
   08:00) and click **Recompute expected cost**: the expected cost becomes 0 and a new recalculation appears.
2. Change the end to **Sunday 18/10 11:00** (50 h, leaves on Sunday): it is charged (the 48 h apply).
3. Try a **Saturday**: start Saturday 17/10 09:00 and end Monday 19/10 23:00 → 0; end Tuesday 20/10 10:00 → charged.
4. In **Pricing & Suppliers → Test pricing**, service ALM, airport MAD, a [DEMO] customer, AWB weight 500 and the
   period start and end: the same calculation without saving anything.
5. In **S00021**, the detail button of the ALM line: the amount of each reading not decided.

## 8. How it was checked

- Engine, without Odoo: 21 tests with hand-computed amounts (48 h 00 / 48 h 01, 120 h = 5 periods or 6 days, change of
  time, Friday → Monday / Sunday / Tuesday, Saturday → Monday / Tuesday, tiers of 7, 8 and 10 days, minimum per stay
  and per day, «or fraction» at 100, 100.01, 400 and 401 kg, factor 333, missing or inconsistent data).
- Odoo (throw-away test database): quotation, «Test pricing» with the actual period, file with a period,
  recalculations without duplicates, RFQ and order, supplier bill in draft (not counted) and posted, credit note, and an
  operations user who can neither change nor approve a tariff.
- Reference examples from the WFS document (private amounts, not published): 57 examples without differences on the
  test database and on the server (rolled back).
