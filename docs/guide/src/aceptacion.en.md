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

## Afterwards

Accepting opens the **shipment file** (see "The shipment file"). The accepted snapshot is its commercial baseline: each
supplier service goes to **Services and costs** with its expected cost, to be ordered from the supplier and compared
with its bill (actual cost). A supplier service with an **unknown** cost prevents acceptance, unless a sales manager
writes the reason. A service added after acceptance only enters through **Re-invoice to the customer** (reason and
snapshot) or a new quotation linked to the file.
