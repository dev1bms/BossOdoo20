## Sale price

The sale price is the standard **unit price** of the line. It may come from:

| Source | How | "Sale" status |
|---|---|---|
| Typed by the salesperson | Type the unit price | Entered by a person |
| Price agreed with the customer | Customer pricelist (Sales › Products › Pricelists), per service and **charge basis** | Agreed price |
| Free of charge | Tick "Free of charge" (intended zero) | Free of charge (confirmed) |
| — | Zero price, not ticked | **Sale price missing** |

- Odoo's **margin** is (sale − cost) / sale; the **markup on cost** is (sale − cost) / cost. Both show in the line
  explanation.
- Pricelists of BOSS services require the charge basis and reject two overlapping prices for the same case.
- Automatic sale rules (markup or margin per service) and a minimum margin are pending (P01, P02).

## VAT

The VAT of each line comes from the **BOSS VAT rules** (Ángel, 31/08/2026):

1. Base class of the service: **NS** (not subject) and **EX** (exempt) are final.
2. **NR**: by origin → destination (zones PRO mainland Spain and Balearics, CAN Canaries, COM rest of the EU, TER third
   countries); only PRO→PRO, CAN→PRO, COM→PRO, COM→COM, TER→PRO and TER→COM stay NR; the rest becomes EX.
3. If still NR, by **customer**: PRO keeps NR; CAN, COM and TER become EX.
4. A missing zone leaves the VAT **pending**.

The Odoo tax of each class is chosen in **Settings › Sales** (see [VAT and currencies](#/iva-moneda)).

## The quotation is not sent when…

… a line has **VAT pending** or **sale price missing**. The system lists them line by line:

![Sending blocked with the list of what is missing](img/06-envio-bloqueado.png)
