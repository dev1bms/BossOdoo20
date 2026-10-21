# ADR-001 — Architecture and modules for BOSS pricing on Odoo 20

Status: accepted (technical decision, Belal's mandate of 21/10/2026). Business rules referenced here
are listed with their owner and status in `docs/preguntas-abiertas.md`.

## Context
- Odoo 17 (production) prices with Studio models (`x_concept`, `x_lines`); Odoo 19 (frozen) grew to
  14 modules / ~45k lines and priced by *concept*, not service (siblings borrowed prices), with at
  least six different selection rules and data copied across four shipment representations.
- A focused spike on Odoo 20 (`spikes/boss_spike_adr002`, 7 characterisation tests, 0 failures)
  showed what standard Odoo does with BOSS cases (summary in ADR-002).
- The service catalogue already decided: a BOSS service is a standard `product.product` of type
  `service` (Belal, 21/10/2026).

## Decision
Three addons with one-way dependencies:

| Addon | Responsibility | Depends on |
|---|---|---|
| `boss_services` | Service catalogue (products), charge bases (`uom.uom`), Odoo 17 identity (concept id/code), pricing readiness of each service, ES/AR translations | `product`, `uom`, `account` (only to keep taxes explicitly empty until Ángel maps VAT) |
| `boss_pricing` | Supplier tariffs (document + page, validity, versions, approval), pure-Python engine, the single matching + compute service | `boss_services`, `mail` |
| `boss_pricing_sale` | Shipment inputs on the quotation, cost and sale per line with explanation, missing-price actions, sale-price base "BOSS cost", lock + snapshot on acceptance, explicit re-pricing | `boss_pricing`, `sale_management`, `sale_crm`, `sale_margin` |

- No module per service. Differences between services are **data** (tariff lines with a method and
  conditions); shared arithmetic lives once in `boss_pricing/engine`.
- A service-specific addon is created only when a service needs behaviour that data cannot express,
  and only with a written ADR (e.g. time-based storage with supplier events, if needed).
- Operations (expediente) and invoicing come later as separate addons that consume
  `boss_pricing` and the accepted snapshot; nothing in these three addons depends on them.

## Alternatives considered
1. **One big `boss_pricing` addon** with sales integration: fewer manifests, but tariffs and engine
   would depend on `sale`, and operations would inherit sales screens. Rejected.
2. **Extend `product.supplierinfo` for supplier prices**: rejected by spike T5 — standard seller
   selection crosses units (asked 40′, returned W/M), ignores shipment conditions and is used
   automatically by purchase flows.
3. **One addon per service family**: rejected; it re-creates the Odoo 19 sprawl. Families are engine
   methods, not addons.

## Consequences
- Every screen (quotation now, expediente later) calls `boss.pricing.service` and gets the same
  answer and explanation.
- The engine is testable without Odoo; Odoo tests only cover integration risks.
- Catalogue data (codes, names, translations) is versioned in `boss_services`; prices never are.
