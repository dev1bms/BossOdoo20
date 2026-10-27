A **tariff** = one supplier document: its validity, what it applies to and its prices. It is entered once and every
quotation uses it as soon as an approver approves it. Pricing & Suppliers › **Tariffs and documents** › [[New]].
**A PDF with several sections** (import, export, transport by zones…) **is still one tariff**: each price carries the
scope of its section.

## Step by step

1. **Header**: name (supplier + what it covers + edition, e.g. «MSC local charges import 09-12/2026»), **supplier**
   (who invoices BOSS; not necessarily the shipping line), **document** (the PDF), **document reference** (title and
   edition), **currency**, **valid from / to** (empty «to» = until a newer version).
2. **Applies to** tab: fill only what limits the **whole** document (direction, mode, load, carrier, ports,
   countries, provinces, customer). Empty fields show «Any …»: they apply to everything. When the scope matches the
   document, tick **Scope reviewed**. The one-line summary appears under the title.
3. **Prices** tab › [[Add a line]] for each service of the document ([[Save & New]] to go on with the next one).
   Each price is a **catalogue service on a charge basis**; a new supplier never creates a new service.
4. In each price choose the **calculation method**: only its fields appear, and next to each amount its unit
   («EUR per Container», «EUR per 100 chargeable kg … and day»). The **live example** prices an illustrative shipment
   with the pricing engine.
5. **Section of the document**: in the price, group **Applies to**, fill only what that section limits (direction,
   mode, load, ports, countries, provinces); empty = «As the tariff». **This price applies to** shows it in one line,
   and the price list shows it in the **Applies to** column. A price can narrow the tariff, never widen it.
6. The yellow notice **Before sending for approval** lists what is missing, and also two prices of the same service
   and unit that would apply to the same shipments (they would conflict: narrow «Applies to» on one).
   [[Send for approval]].
7. An approver checks against the PDF and clicks [[Approve]]. From then on the prices quote and no longer change: a
   change is a **new version**.

![Approved tariff: scope summary and prices with their unit](img/22-tarifa-aprobada.png)

![Draft: what is missing before sending, and the scope with «Any …»](img/23-tarifa-borrador-alcance.png)

## Three examples

| Document | Calculation | What to enter |
|---|---|---|
| MSC: THC per container | Per unit | Charge basis Container, size 40', type HC if the document distinguishes, **unit price** (EUR per Container) |
| WFS: storage by weight and day | Per day with free period | Charged on **air waybill chargeable kg**, unit size 100, **or fraction**; 48 free hours; mode «once exceeded, every day from day 1»; day tiers («Up to» = day number, 0 = no limit) |
| IRENEO: transport by weight brackets | Brackets | Charged on **chargeable kg (document factor)**, factor 333; «Up to» in kg with a fixed amount or a price per kg. The bracket that contains the whole quantity prices all of it |

**One document with sections** (IRENEO «Tarifas MAD»): one tariff «IRENEO Tarifas MAD 2026» with no direction or mode
on the header. The Barajas export package and the X-R screening carry *Export · Air*; the terminal pickup,
*Import · Air*; the zone-3 national distribution, its provinces; the export storage, *Export · Air · MAD*. Two prices
of the same service (import and export handling) live together because their scopes do not overlap. When the
supplier changes a price, **new version** of the same tariff with its date.

![Time price: units next to each amount and engine example](img/24-precio-tiempo.png)

![Weight brackets with volumetric factor](img/25-precio-tramos.png)

## Zero, empty and demo

- **A price without amount is a missing price**, never free: the tariff is not sent until it has an amount, is marked
  **On request** or **No cost (confirmed zero)**.
- **Minimum / maximum** apply to the cost of the **whole quotation line**; 0 = no minimum / maximum.
- Changing the calculation method clears the values that no longer apply, and a warning names them (Discard brings
  them back).
- **Demo tariff** («Demo» ribbon): it only prices customers marked as **Demo customer**; never a real customer, even
  when no other price exists. Only an approver marks demo customers.

## Loading many tariffs

The sample tariffs were loaded with the **importer** (structured file with supplier, document, page, validity, scope
and prices). It is idempotent, never approves, and marks the scope as reviewed because the file states it. See
[Maintenance](#/mantenimiento).
