## Sale price

The sale price is the standard **unit price** of the line. Its status (column **Sale**) is independent of the cost
status (column **Cost**): a line may have its cost computed and the sale pending, or the other way round.

| Source | How it is set up | «Sale» status |
|---|---|---|
| Price agreed with the customer | Customer pricelist, **Fixed price** rule per service and **charge basis** | Agreed price |
| On the line cost | Customer pricelist, **Surcharge** rule «% on **Expected cost of the quotation line (BOSS)**», or **Margin on sale (%)**; optional: rounding, extra fee and minimum/maximum margin | From the expected cost |
| Typed by the salesperson | Type the unit price (wins over the pricelist) | Entered by a person |
| Free of charge | Tick «Free of charge» (intended zero price) | Free of charge (confirmed) |
| — | Zero price not ticked, or a rule on a cost not known yet | **Sale price missing** |

In the line details (ⓘ icon of the Cost column), the block **How the sale price is set** gives the pricelist, the rule
and the calculation: «Pricelist Customer X, rule «Expected cost of the line + 15 %»: expected cost 150.00 € per
Container gives 180.00 €. The minimum margin of 30.00 € per unit applies».

![Line details: how the cost is computed and how the sale is set](img/16-detalle-venta.png)

### Rules on the cost

![Pricelist rule on the expected cost of the line](img/17-regla-coste.png)

- **Markup** = (sale − cost) / cost; **margin** = (sale − cost) / sale. Illustrative, cost 100 €: markup 20 % → 120 €;
  margin 20 % → 125 €. Use one or the other, not both.
- Odoo's **minimum margin** is **per unit of the charge basis** (container, shipment, kg…). Avoid it on per-kg services
  (15 € per kg would be absurd). A minimum per line or per quotation is a pending decision (P02).
- While the cost is unknown (no tariff, waiting for approval, missing data) the sale stays **«missing»**: never computed
  on a zero cost.
- On a draft, a change of shipment data or a tariff approval recomputes the cost and the sale built on it; a price typed
  by a person is kept and an accepted quotation does not change.
- Per-kg prices keep their decimals (0.092 € per kg × 500 kg = 46.00 €); the line amount is rounded to cents.

> Commercial policy: there is no approved general sale rule; prices are agreed per customer (Cristina). A sales manager
> creates each customer's rules. The unified ALM sale and the minimum margin are pending (see [Decisions](#/preguntas)).

## VAT

Each line's VAT comes from the **BOSS VAT rules** (Ángel, 31/08/2026):

1. Base class of the service: **NS** (not subject) and **EX** (exempt) are final.
2. **NR**: by origin → destination (zones PRO mainland and Balearics, CAN Canaries, COM rest of EU, TER third
   countries); only PRO→PRO, CAN→PRO, COM→PRO, COM→COM, TER→PRO and TER→COM stay NR; the rest becomes EX.
3. If still NR, by **customer**: PRO keeps NR; CAN, COM and TER become EX.
4. If a zone is missing, VAT is **pending**.

The Odoo tax of each class is chosen in **Settings › Sales** (see [VAT and currencies](#/iva-moneda)). Until Ángel
decides, every line has VAT pending.

## The quotation is not sent or confirmed if…

… a line has **VAT pending** or a **sale price missing**. The system explains it line by line:

![Sending blocked with the list of what is missing](img/06-envio-bloqueado.png)
