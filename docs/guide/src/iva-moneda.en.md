Settings › **Sales** › **Pricing** block:

![VAT and currency settings](img/15-ajustes-iva.png)

## VAT of BOSS services

One Odoo tax for each class given by the rules: **NR**, **EX** (exempt) and **NS** (not subject). While a tax is empty,
lines of that class have VAT **pending** and the quotation cannot be sent or confirmed.

> Choosing the taxes (and the Spanish accounting localisation) is Ángel's decision (P17).

## Supplier cost in another currency

- **Do not convert** (default): a line whose tariff is in another currency shows "Other currency, no conversion policy"
  and does not add to the quotation cost.
- **Odoo exchange rate of the quotation date**: converted with Odoo's rate; the rate used is kept in the snapshot on
  acceptance.

> The exchange-rate policy and the bank-loss rule (QBR) are pending (P03).
