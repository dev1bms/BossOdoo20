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

### Cases still pending (Ángel's decision, P17)

| Case | Why | Example |
|---|---|---|
| EX for a **Spanish or Canary** customer | Ángel calls it exempt; Odoo 17 uses «0% S», which the localization defines as **subject at 0 %** (box 150), neither exempt nor not subject. The exempt tax with its article, or Odoo 17's practice, is still to be chosen | THC of an import from China for a customer in Valencia |
| NS that is **not paid on behalf** (CAU, QBR) | Odoo 17 invoices them on a normal invoice with the customer-based zero rate, not as not subject | Customs guarantee fee |
| Customer in **Ceuta or Melilla** | No zone in the rules | — |

In those cases the line says «VAT pending» with the reason, and the quotation cannot be sent or confirmed. Quotations
whose cases are decided (for example, an EU customer) go all the way to acceptance.

## Supplier cost in another currency

- **Do not convert** (default): a line priced in another currency shows «Other currency, no policy» and does not add to
  the quotation cost.
- **Odoo rate of the quotation date**: converted with Odoo's rate; the rate used is kept in the acceptance snapshot.

> The exchange policy and the bank-loss rule (QBR) are pending (P03).
