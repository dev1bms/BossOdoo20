Each **supplier price** has a calculation method; the same service may be computed differently by different suppliers
(e.g. HAN per AWB chargeable kg at one handler and with factor 333 at another). Minimum and maximum always apply to the
**line total**; results are rounded to cents. Examples with illustrative amounts.

## 1. Price per unit

Price × quantity in the charge basis (containers, B/L, kg, m³, hours…).

- 3 containers × 200 € = **600 €**.
- "Per 100 kg or fraction", minimum 20 €: 450 kg → 5 units × 3 € = 15 € → **20 €** (minimum).

## 2. Larger of two bases

Two amounts are computed and the larger is taken (typical of groupage: tonnes or m³).

- 2.5 t × 20 €/t = 50 € versus 4 m³ × 10 €/m³ = 40 € → **50 €**.

## 3. Brackets

The bracket whose "up to" (included) holds the quantity is used. A bracket has a fixed amount and/or a unit price that
multiplies the **whole** quantity. "Up to 0" is the open bracket. Above the last closed bracket there is no price (ask
the supplier).

| Up to | Fixed | Per kg |
|---|---|---|
| 100 kg | 50 € | — |
| 500 kg | — | 0.40 € |
| 1,000 kg | — | 0.30 € |

- 100 kg → **50.00 €**; 101 kg → 101 × 0.40 = **40.40 €**; 1,001 kg → **no price**.
- Option "Not below the previous bracket": 501 kg → 501 × 0.30 = 150.30 € < 500 × 0.40 = 200 € → **200.00 €**.
- Option "Bracket price per container": the bracket amount is multiplied by the containers.

## 4. Percentage

Rate % of a base: goods value, customs duties, or the **cost of other services of the same supplier** in the same
currency (fuel or insurance on transport).

- Insurance 5 % of transport 300.00 € = **15.00 €** (minimum 1 €).

## 5. Per day with free period

Quantity per period (containers, 100 kg…) × price of each charged period. It is computed with the **actual period**
(start and end with date and time) when known, otherwise with an **estimate in days**.

- **How days are counted** (set on each price): **24-hour periods** from the start («por 24 horas»: a part of a period
  counts as a whole period) or **calendar days** with the entry and the exit day («por día», «se contabiliza el día de
  entrada y el de salida»). Example: Monday 10:00 → Saturday 10:00 = 120 h = 5 periods of 24 h, but 6 calendar days.
- **Free days deducted**: only the periods after the free period are paid.
- **Threshold**: once the free period is exceeded, every period is paid **from the start** (usual at airport
  warehouses). Free hours are compared with the **exact hours**: 48 h 00 min is free; 48 h 01 min is charged in full.
- **Tiers**: by day number since the start ("day 5 to 7"), by days after the free period ("5 days at X, then Y") or
  every day at the tier reached by the whole stay.
- **Minimum**: on the stay (line total) or, when the document says «/día», on each charged day. A stay inside the free
  period costs 0, never the minimum.
- **Weekday exceptions**, when the document gives them: start on a **Friday with a Monday exit** → another free period
  (WFS: 72 h); start on a **Saturday** → free until **Monday included** (by date, not 72 h: Saturday 09:00 → Tuesday 08:00
  is 71 h and is charged). They depend on the exit day: applied only with the actual period; the quotation estimate does
  not assume them and says so. «Friday +1 free day» (any exit) exists for documents worded that way.
- **Readings not decided**: when a document can be read two ways and the business has not decided (24-hour periods or
  calendar days, tier on the following days or on the whole stay, «per 100 kg» with or without fraction), the price
  marks it «not decided». The system computes every reading: when they give the same amount the cost is automatic;
  otherwise the line shows **«Not priced automatically»** with every amount, and the cost is typed by hand (supplier bill
  or quote).

Example (illustrative amounts): 7 free days, "5 days at 30 €, then 80 €", 15 days, 1 container: days 8-12 = 5 × 30 = 150;
days 13-15 = 3 × 80 = 240 → **390 €**. 48 h threshold, 500 kg per 100 kg at 10 € per period: NOA Monday 10:00 → pickup
Wednesday 10:00 → **0 €**; Wednesday 10:01 → 3 × 5 × 10 = **150 €**. Tiers not decided (10 € up to 7 days, 20 € after),
10 days: day by day 7 × 5 × 10 + 3 × 5 × 20 = 650 €; whole stay 10 × 5 × 20 = 1,000 € → manual cost until decided.

- The quotation days are entered once in the Shipment tab and apply to every time-based service (DEM, OCU, ALM); a line
  can have its own estimate. Without **days indicated** the line says «Missing shipment data»; 0 days indicated is a
  valid estimate.
- In «Test pricing» the **start and end of the period** can be typed (Madrid time; Canary Islands, Canary time) to see
  the actual cost with the exceptions.

> On a quotation the result is an **estimate**; with the actual start and end the system recomputes the cost of the
> period, and the supplier bill is what counts in accounting. Full guide to airport storage:
> [ALM step by step](#/almacenaje).
