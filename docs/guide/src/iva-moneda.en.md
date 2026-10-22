## Company

The system company is set up with the Odoo 17 production data: **Boss Continental S.L.**, Spain, currency **EUR** and
chart of accounts **PGC PYMEs 2008** (Odoo's Spanish localization, with its taxes). Pricelists are enabled: one
**General pricelist (EUR)** without prices and, when agreed, one pricelist per customer.

## VAT of BOSS services

Settings › **Sales** › **Pricing** block: one Odoo tax for each class given by the rules: **NR**, **EX** (exempt) and
**NS** (not subject).

![VAT and currency settings](img/15-ajustes-iva.png)

While a tax is empty, lines of that class have VAT **pending** and the quotation cannot be sent or confirmed.

> **Ángel's decision (P17)**: which PGC tax matches each class, with which exemption article. Installing the
> localization does not decide how each service is taxed. For reference, Odoo 17 uses «21% S», «0% EX S» and
> «0% EXEMPT NS». Ceuta and Melilla: zone pending.

## Supplier cost in another currency

- **Do not convert** (default): a line priced in another currency shows «Other currency, no policy» and does not add to
  the quotation cost.
- **Odoo rate of the quotation date**: converted with Odoo's rate; the rate used is kept in the acceptance snapshot.

> The exchange policy and the bank-loss rule (QBR) are pending (P03).
