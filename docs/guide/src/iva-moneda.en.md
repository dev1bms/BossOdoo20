## Company

The system company is set up with the Odoo 17 production data: **Boss Continental S.L.**, Spain, currency **EUR** and
chart of accounts **PGC PYMEs 2008** (Odoo's Spanish localization, with its taxes). Pricelists are enabled: one
**General pricelist (EUR)** without prices and, when agreed, one pricelist per customer.

## VAT of BOSS services

Two steps:

1. **VAT class** of the line, with Ángel's rules (31/08/2026): **NS** = not subject by nature (never VAT), **EX** =
   exempt, **NR** = carries VAT; an NR becomes EX by origin/destination and by the customer zone
   ([details](#/venta-iva)).
2. **Odoo tax**: the **BOSS VAT table** (Sales › Configuration › BOSS VAT table, or from Settings) gives the tax of
   each case: class × customer zone × paid on behalf or not. Each row states its **source**.

![BOSS VAT table](img/20-tabla-iva.png)

| Case | Tax | Sources |
|---|---|---|
| NR (customer in mainland Spain or the Balearics) | 21% S | Ángel: NR carries VAT · Odoo 17: NR = 21 % → «21% S» · 303 boxes [07]/[09] |
| EX, EU customer | 0% EU S | Ángel: EU customer → EX · Odoo 17: EU customer → «0% EU S» · not subject by place of supply, 303 [59] and 349 |
| EX, third-country customer | 0% EX S | Ángel: third-country customer → EX · Odoo 17: «0% EX S» · not subject by place of supply, 303 [120] |
| NS paid on behalf (ARA, IVA, PLA, DUM) | 0% EXEMPT NS | Ángel: not subject by nature · Odoo 17: tax invoice with «0% EXEMPT NS» · not declared |

«Odoo 17» is its invoicing assistant (action «Create Invoice»), which picks the tax by class, customer type and
invoice type. A row exists only where Ángel's rules, Odoo 17 and the legal nature of the tax agree.

### Approved by Belal on 23/10/2026, Ángel's ratification pending (P17)

| Case | Tax | Source |
|---|---|---|
| EX of a **Spanish** customer (mainland and Balearics) | 0% Exent Art.22 | Exempt, art. 22 LIVA, 303 [60] (proposal approved by Belal) |
| EX of a customer in the **Canaries, Ceuta or Melilla** (zone CAN) | 0% S NS | Not subject by place of supply, 303 [120] |

### Case still pending

| Case | Why | Example |
|---|---|---|
| NS that is **not paid on behalf** (CAU, QBR) for a Spanish customer | Odoo 17 invoices them on a normal invoice at 0 % by customer, not as not subject | Customs guarantee fee |

In that case the line says «VAT pending» with the reason, and the quotation cannot be sent or confirmed.

## Supplier cost in another currency

- **Do not convert** (default): a line priced in another currency shows «Other currency, no policy» and does not add to
  the quotation cost.
- **Odoo rate of the quotation date**: converted with Odoo's rate; the rate used is kept in the acceptance snapshot.

> Policy approved by Belal on 23/10/2026, Ángel's ratification pending (P03): Odoo exchange rate of the quotation date, active on the server. The bank-loss
> charge (QBR) applies only when a USD quotation is invoiced in EUR: in development (phase B).
