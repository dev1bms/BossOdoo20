# ADR-002 — Pricing model: services, charge bases, supplier tariffs and one engine

Status: accepted (technical). Business values are not decided here: they are tariff **data** or
open questions (`docs/preguntas-abiertas.md`).

## Context (evidence)
- Odoo 19 keyed prices by *concept* (siblings borrowed prices: OAL-PAL took OAL-CON's price),
  had ≥ 5 different selection rules, only used *active* tariff versions and kept business numbers
  in Python (`.research/02_calc_methods.md` §11, local file).
- Spike on Odoo 20 (`spikes/boss_spike_adr002`) and code reading (`.research/04_odoo20_standard.md`):
  - pricelist rules: right price per unit when units are independent (T1); silent fallback to the
    product price (T2a); a rule without unit applies to any unit (T2b); two rules → newest wins
    silently (T3); related units multiply fixed prices (T4); unrelated units convert 1:1 (T4b);
  - `product.supplierinfo._select_seller` returns the cheapest price across units and ignores
    shipment conditions (T5) → not usable for supplier tariffs;
  - markup is standard, margin and per-line minimum are not (T6); confirmed orders are re-priced when
    qty/cost change (T7c/d).

## Decision

### 1. Service and charge basis
- A service is a standard `product.product` (type service), keyed by its original code
  (`default_code`) and its Odoo 17 concept id (`boss_o17_concept_id`). 77 services in
  `boss_services/data/product_data.xml`, `list_price = 0`, taxes empty until Ángel maps VAT.
- A **charge basis** is a `uom.uom` with no reference unit (`relative_factor = 1`): container 20',
  40', 45', TEU, shipment, B/L, AWB, declaration, document, gross kg, chargeable kg air/road, tonne,
  m³, W/M, pallet, hour. Each declares where its quantity comes from (`boss_quantity_source`:
  container counts, TEU, one per shipment, or entered on the line).
- The code **never converts between bases** (Odoo would convert 1:1 silently). Load form
  (FCL/LCL/air) is a shipment condition, not a unit.
- Each service says how it is priced: `boss_pricing_mode` (supplier tariff / manual amount / BOSS
  own fee / pending business decision) and its usual `boss_cost_method`.

### 2. Supplier tariff (custom model, justified by T5)
- `boss.tariff` = one supplier document: supplier, PDF + reference, currency, validity, version
  (lineage), priority, **scope** (direction, mode, load type, carrier, ports, customer) and state
  draft → waiting for approval → approved. Approved tariffs never change (prices are locked by
  `ir.access` domains, header by code); a change is a **new version**. Priority may be changed by an
  approver to resolve a conflict (tracked).
- `boss.tariff.line` = one price of **one service in one charge basis**: method, unit price,
  minimum/maximum of the line total, "on request", page of the document. Unique per
  (tariff, service, basis).

### 3. One engine, one selection rule (`boss_pricing/engine`, pure Python)
Order: valid on the tariff date (any version, not only the newest state) → approved → conditions →
priority (lower wins) → newest version of the same tariff → most specific (a rule whose condition set
strictly contains another's wins, e.g. customer price over general price) → anything left = conflict.
A condition whose shipment input is empty makes the result `missing_input` (never a guess, never
"the cheapest").

Explicit results: `ok`, `missing_input`, `no_tariff`, `pending_approval`, `on_request`, `conflict`,
plus, from the Odoo layer, `not_ready` (pending decision / method not built), `manual`, `currency`.
Zero is only "free" when it is a justified result (BOSS own fee) or confirmed by a person.

`boss.pricing.price_cost()` is the only entry point; `boss.pricing.explain()` turns a result into
plain language (quantity × unit price, minimum applied, tariff, version, document and page).

### 4. Methods
Implemented: `per_unit` (unit price × quantity, then minimum and maximum **of the line total**,
rounded half-up to the currency). Next, as data-driven methods of the same engine: max of bases
(THC-LCL), brackets (route/weight), time with free period (DEM/OCU/ALM), percentage (CAU/SEG/QBR/FS).
A service whose method is not built yet is `not_ready` and accepts a manual cost.

### 5. Sale price
- Approved rule: the sale price is entered or confirmed by a person; no general sale price.
- Standard `product.pricelist` holds **agreed** sale prices (customer agreements, fixed per service
  and charge basis), guarded: a BOSS price must have its unit; two overlapping prices for the same
  case are rejected (spike T2b/T3).
- A zero sale price is "missing" unless "free of charge" is ticked.
- Margin (Odoo, on sale) and markup (on cost) are shown separately. Rule-based proposals (markup /
  margin %) and minimums per line or per quotation are **not built** until P01/P02 are answered.

### 6. Currency
A cost in another currency than the quotation is `currency` (pending) unless the company policy says
otherwise (`boss_fx_policy`: none by default; "Odoo rate of the quotation date" available). P03.

## Alternatives rejected
- `product.supplierinfo` for supplier prices (T5); per-concept prices (Odoo 19 bug); variants per
  container type (multiplies products, still no W/M); one rule per screen (Odoo 19).

## Consequences
- Adding a supplier = data. Adding a method = one function in `engine/methods.py` + tests.
- Quotations and, later, expedientes share `price_cost()` and the explanation.
