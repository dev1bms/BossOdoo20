Each line looks for the **approved supplier price** that fits the service, its charge basis, the shipment and the
planned date. The result shows in the **Cost** column; the ⓘ icon opens the explanation.

![Calculation explanation of a line](img/04-detalle-calculo.png)

The explanation shows the arithmetic ("1 × 200.00 € per Container = 200.00 €"), the tariff and version, supplier,
validity, **document and page**. The unit cost goes into Odoo's standard cost field, so line and quotation margins are
Odoo's own.

## Cost statuses

| Status | Meaning | What to do |
|---|---|---|
| Priced (Cotizado) | An approved price was found and computed | — |
| Missing shipment data | A datum the tariff needs is empty (carrier, date, containers, weight…) | Complete the Shipment tab |
| No supplier price | No approved tariff applies | [[Añadir precio de proveedor]] (see step 5) |
| Price waiting for approval | A price was entered but not approved | An approver approves it |
| On request | The document says "on request" | Ask the supplier |
| Several prices apply | Two tariffs with the same scope | Choose the carrier, narrow a tariff or set a priority |
| Not priced automatically | Service pending a business decision | Manual cost if needed |
| Manual amount | Service priced by offer (freight) or at cost (paid on behalf) | Type the unit cost and its reference |
| Other currency, no policy | The tariff currency differs from the quotation | See [VAT and currencies](#/iva-moneda) |

> A **zero** cost only appears when justified (BOSS own fee, or days inside the free period); never because a price is
> missing.
