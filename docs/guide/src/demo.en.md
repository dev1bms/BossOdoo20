> **27/10/2026:** the demo tariffs and the demo pricelist are archived (the test quotations that used them still show them). The walk-through with real data is in [Quick start](#/inicio-rapido).

Demonstration on **https://system.bosscontinental.com** with the three suppliers of the system (**MSC**, **WFS**,
**IRENEO**). **[DEMO]** tariffs, customers and sale rules: illustrative amounts, approved only for this demonstration and
limited to the [DEMO] customers; they never price real quotations: they are **demo tariffs** («Demo» ribbon) and the
engine applies them to **demo customers** only, even when a real customer has no other price. The [MUESTRA] tariffs (real documents) still wait for
approval.

## Records

| What | Link |
|---|---|
| Opportunity for the live quotation | [Meeting with Ángel](https://system.bosscontinental.com/odoo/crm/9) |
| MSC: opportunity · accepted quotation · tariff | [CRM 4](https://system.bosscontinental.com/odoo/crm/4) · [S00009](https://system.bosscontinental.com/odoo/sales/9) · [tariff 20](https://system.bosscontinental.com/odoo/action-boss_pricing.boss_tariff_action/20) |
| WFS: opportunity · quotation · tariff | [CRM 5](https://system.bosscontinental.com/odoo/crm/5) · [S00010](https://system.bosscontinental.com/odoo/sales/10) · [tariff 22](https://system.bosscontinental.com/odoo/action-boss_pricing.boss_tariff_action/22) |
| IRENEO: opportunity · quotation · tariff | [CRM 6](https://system.bosscontinental.com/odoo/crm/6) · [S00011](https://system.bosscontinental.com/odoo/sales/11) · [tariff 23](https://system.bosscontinental.com/odoo/action-boss_pricing.boss_tariff_action/23) |
| VAT conflict (Spanish customer) | [CRM 7](https://system.bosscontinental.com/odoo/crm/7) · [S00012](https://system.bosscontinental.com/odoo/sales/12) |
| Quotation made in the interface (CES price added, accepted) | [S00013](https://system.bosscontinental.com/odoo/sales/13) |
| Sale rules of the [DEMO] customers | [Pricelist](https://system.bosscontinental.com/odoo/action-product.product_pricelist_action2/3) |

## Expected results (EU customer, VAT 0% EU S)

| Example | Input | Cost | Sale |
|---|---|---|---|
| MSC THC | 1 × 20' DV, 1 × 40' HC | 180 € and 240 € per container (40' RF: 300) | 280 € agreed per container |
| MSC BL | 1 per shipment | 60 € | 75 € (20 % margin on sale) |
| MSC DEM | 10 days, 7 free, «5 days at 30 €, then 60 €» | 3 × 30 = 90 € per container | 120 € (cost + 15 % with 30 € minimum margin) |
| ARA (paid on behalf) | customs declaration in «Cost reference» | 350 € manual | 350 € at cost; VAT 0% EXEMPT NS |
| WFS ALM | AWB 500 kg, 4 days (line estimate), Wednesday arrival | 4 × 5 × 10 = 200 € (past 48 h: from day 1) | 230 € |
| WFS HAN | 500 chargeable kg | 500 × 0.05 = 25 € (minimum 20 €) | 0.0575 €/kg → 28.75 € |
| WFS AWB | 1 air waybill | 30 € | 34.50 € |
| IRENEO TTE-CON | Madrid, 450 kg and 1 m³ (factor 333) | chargeable 450 kg, «up to 500» bracket × 0.20 = 90 € | 103.50 € |
| IRENEO FS | 5 % of the same supplier's transport | 4.50 € | 5.18 € |

## 10–15 minute walkthrough

1. **Tariff** (Pricing & Suppliers › Tariffs and documents): open MSC's: supplier, document, validity, scope (direction, mode,
   port, customer) and prices by size and type; status **Approved** with user and date.
2. **CRM**: open [Meeting with Ángel](https://system.bosscontinental.com/odoo/crm/9) › [[New quotation]].
3. **Shipment**: Import · Sea · FCL · ESVLC · China · MSC · date 04/11/2026 · days 12 · containers 2 × 40' HC. Save.
4. [[Add services]]: THC, DEM and **VGM**, supplier **MSC** › Add. Result: THC cost 240 € and sale 280 € per container;
   DEM 5 days × 30 € = 150 € per container; VGM **No supplier price**.
5. **Missing price**: ⊕ icon of VGM › supplier MSC already set · name «[DEMO] MSC VGM 2026» · 25 € · page 1 · tick
   **Only this customer** · attach a test PDF › [[Save price]] → «Waiting for approval».
6. **Approve**: review icon of the line › [[Approve]] › OK. The line is priced (25 € → 28.75 €).
7. **Data change**: days 12 → 15 in Shipment › save: DEM becomes 5 × 30 + 3 × 60 = 330 € per container.
8. **Details**: ⓘ icon of a line: how the cost is computed (tariff, version, document, page) and how the sale is set
   (pricelist rule, minimum margin).
9. [[Confirm]] → prices frozen, **Pricing history**; [[Re-price]] requires the **reason**.
10. **VAT for Ángel**: open [S00012](https://system.bosscontinental.com/odoo/sales/12) › Confirm: the system explains
    that THC's tax is missing (EX, Spanish customer).

## Decisions for Ángel

| Case | Today | Question |
|---|---|---|
| EX for a Spanish or Canary customer (THC, T3, freight, SEG…) | Approved by Belal on 23/10 (P17), Ángel pending: «0% Exent Art.22»; Canaries «0% S NS» | Exempt tax with its article (21/22 → «Exempt Art.22», box 60) or Odoo 17's practice «0% S» (subject at 0 %, box 150)? Canaries as not subject by place of supply? |
| NS that is not paid on behalf (CAU, QBR) | VAT pending | Not subject (0% EXEMPT NS) or the customer-based 0 % as in Odoo 17? |
| Ceuta and Melilla | Zone CAN (approved by Belal on 23/10, P17; Ángel pending) | — |
| EU customer without VAT number | VAT pending | Invoice with Spanish VAT (business rule does not apply)? |
| Paid on behalf without declaration | VAT pending | Confirm that the declaration in the customer's name is the condition |

Already decided and applied: NR → 21% S; EX of EU customers with VAT number → 0% EU S; EX of third-country customers →
0% EX S; paid on behalf with declaration → 0% EXEMPT NS (Ángel's rules 31/08/2026 and Odoo 17 invoicing).

## Limits of this version

- Demonstration and controlled use, **not** full production: real approved tariffs, the VAT decisions above and the
  currency policy are missing (USD costs stay «Other currency»).
- The minimum margin is per unit of the charge basis; per line or quotation is pending (P02).
- WFS's Friday rule (72 h with a Monday exit) is not applied on quotations.
- On screens narrower than about 1,900 px the lines table may need horizontal scrolling.
