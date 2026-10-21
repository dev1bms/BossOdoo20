## Send

[[Enviar]] (Send) uses Odoo's standard email (template, quotation PDF, online signature if enabled). Before that, the
system checks VAT and sale prices (step 6).

## Accept

When the customer accepts, click [[Confirmar]] (Confirm) — or the customer signs on the portal. Then:

- Every line is **frozen**: quantities, units, prices, costs, taxes. Neither a tariff change nor a change of the
  shipment data modifies them.
- A **snapshot** is kept in the **Pricing history** tab: shipment data, containers, currency policy and, per line,
  sale, cost, currency, exchange rate (if used), tariff, version, document, page, VAT and explanation.

![Accepted quotation: frozen prices and history](img/13-oferta-aceptada.png)

## Re-price

A sales manager clicks [[Recotizar]] (Re-price): gives the **reason**, may recompute costs from the current tariffs and
type new sale prices. Another snapshot keeps the previous values, date and user, and the reason is posted on the order.

![Re-price an accepted quotation](img/14-recotizar.png)

## Afterwards (next phases)

The accepted snapshot is the commercial baseline of the **shipment file** (operations) and of the **invoice**: the
expected cost of each line will be compared with supplier invoices (actual cost). Time-based services move from estimate
to actual cost with the file dates.
