A **tariff** = one supplier document, its validity and what it applies to. Pricing & Suppliers ›
**Tariffs and documents** › [[New]].

![Supplier tariff](img/07-tarifa.png)

## Header

| Field | What to enter |
|---|---|
| Name | Supplier + what it covers + edition, e.g. "MSC import local charges 09-12/2026" |
| Supplier | Who invoices BOSS |
| Supplier document | The **PDF** received (required to send for approval) |
| Document reference | Title and edition of the PDF |
| Currency | The document's (EUR, USD…) |
| Valid from / to | As in the document; empty "to" = until another version starts |
| Priority | Usually 10; a lower number wins when two tariffs apply to the same shipment |

## Applies to (empty = any)

Direction, transport mode, load type, **carrier**, **ports**, **countries abroad**, **provinces** (hauliers' zones)
and **customer** (price agreed only for that customer: it wins over general prices).

## Prices

Each line is **one service in one charge basis**: service, charge basis (container, B/L, shipment, kg…), container
size and types when the document distinguishes them, **calculation method**, amounts, minimum/maximum, "on request"
and the **page** of the document. Opening a line shows the parameters of its method:

![Per-day price with free period and tiers](img/08-precio-tiempo.png)

Methods are explained in [The five calculation methods](#/metodos).

## Loading many tariffs

Sample tariffs were loaded with the **importer** (a structured file with supplier, document, page, validity, scope
and prices). It is idempotent: it never duplicates nor overwrites manual changes, and never approves. See
[Maintenance](#/mantenimiento).
