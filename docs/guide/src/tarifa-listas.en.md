One entry point for prices, tariffs, services and suppliers: the **Pricing & Suppliers** app of the main menu. It
uses the same data as quotations (service products, contacts, supplier tariffs) and the same calculation.

| Menu | What it holds |
|---|---|
| **Prices** | Main screen: one supplier price per row |
| **Tariffs and documents** | Each supplier document with its validity, scope, version and approval |
| **Services** | BOSS service products with their suppliers, calculations and readiness |
| **Suppliers** | Contacts with tariffs (shipping lines, handlers, hauliers, warehouses…) |
| **Test pricing** | The calculation of a quotation line on a shipment typed in |

## Prices

Each row: code and service, supplier, **what it applies to** (direction, mode, load, ports, container size and
type, customer), **price with its unit** (e.g. «260 EUR / Container», «0.05 EUR / chargeable kg · min. 20 EUR» or
the bracket summary), «until» and the **status**: Valid, Expires soon (30 days), Expired, Replaced by a newer version,
Draft, Waiting for approval. Row buttons: test, open the document, copy (draft only).

- Search accepts **service or code**, **supplier**, **tariff or document** and **port**.
- It opens on **valid**, **draft** and **waiting** prices. Remove filters to see everything; «Expired» and
  «Archived tariffs» give the history.
- Direction, mode and load filters include prices valid for any (empty field on the tariff).
- «Real tariffs» / «Demo tariffs» separate training prices (optional «Demo» column).
- Group by supplier, service, tariff or approval.

![Prices: charge basis, price with its unit, validity and status](img/21-precios-lista.png)

[[New]] opens the price form in sections: **service, supplier and source** (the draft tariff gives supplier,
document, currency, validity and scope), **applies to**, **calculation** (only the fields of the chosen method;
changing it clears values that no longer apply) and a **live example** computed by the engine: an illustrative
shipment (2 containers, 500 kg, 2 m³, 10 days from a Wednesday) with its steps, or what is missing to compute it.

## Tariff with several services

One tariff = one document: supplier, PDF, currency, validity and scope are set once for all its lines. Before sending
it for approval, a notice lists what is missing (prices, PDF, reference) and **repeated prices** (same service, basis
and container) that would conflict. Below it, the scope fields left **empty = applies to any** are named, so they are
not mistaken for forgotten data. Changing the transport mode clears a load type of another mode (e.g. FCL when
switching to air).

## Services and suppliers

**Services** shows per service: cost source, calculations used (they may differ per supplier), suppliers, valid and
waiting prices, and the readiness: Priced, No supplier price, Prices waiting for approval, Prices expired, Not priced
from tariffs, with a filter for each status («No supplier price» = what is left to price). The product has the **Supplier prices** and **Guide** buttons. A new service is a new product: search
before creating it (never one per supplier).

![Services: readiness with filters](img/26-servicios-lista.png)

On the service, tab **BOSS pricing** › **Ready to quote**: readiness, suppliers, calculations used and
[[Add supplier price]] (a new price of an existing service). «Usual calculation» is only the proposal for new
prices.

![Service ready to quote](img/27-servicio-listo.png)

**Suppliers** lists contacts with tariffs: tariffs, services, prices waiting and expired or expiring. On the contact,
the **Supplier tariffs** and **Supplier prices** buttons. A supplier is not necessarily the carrier: the shipment
carrier only changes on the quotation. On the contact, the **Supplier tariffs** tab shows its documents, versions,
validity, scope and status, with [[New tariff]].

![Supplier with its tariffs](img/28-proveedor-tarifas.png)

## Test pricing

Same calculation as a quotation line, nothing saved. Choose service and charge basis, supplier (empty = any), the
shipment data and the measures. Result: status, quantity, cost, the price used and **why** (valid on the date,
applies to the shipment, most specific, newest version), or what is missing, which prices are waiting or in conflict.

- **Simulate drafts**: a tariff not approved yet counts as approved in this test only. Quotations never use it.
- **Customer** or **pricelist** (optional): sale price per unit, sale and profit, with the pricelist rule.
- Open it from the menu, from a **Prices** row (with its scope, simulated if draft), from the tariff and from the ⓘ
  icon of a quotation line (the line's service, supplier and shipment).

## From a quotation

In the ⓘ icon of a line: [[Test pricing]], [[Add supplier price]] when there is no price and [[Review the supplier
price]] when it is waiting or in conflict. The price is saved in a tariff of the **line's supplier**; once approved,
the quotation recomputes itself. Accepted lines do not change (only with [[Re-price]]).
