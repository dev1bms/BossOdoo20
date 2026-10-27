# ADR-007 — Supplier cost from the quotation: route-specific rates with validity, history kept, one Confirm

Status: accepted (technical), 27/10/2026. Requirements: `docs/reunion-angel-2026-10-27-parte2.md` (meeting Belal–Ángel–
Cristina, part 2). Builds on ADR-002 (tariffs), ADR-003 (quotation, freeze) and ADR-006 (route).

## Context
- Ángel and Cristina: the quotation lines are **selling** prices; the **buying** cost must be visible and traceable;
  freight costs change every week and per route («hundreds of thousands of different fletes every week»), so they must
  be entered **from the quotation, in a small wizard, for one origin port and one destination port, valid for a week**,
  and «go to the pricing engine» while **the old costs stay as history**. Selling tariffs are stable for a year
  (templates) and some customer prices are agreed separately.
- Ángel wants supplier-centric access (MSC → all its prices) as well as service-centric; he found the supplier tab on
  the contact («Perfect. That was everything»).
- P0: Confirm on S00034 showed «so much error». Reproduced (`.research/probe_p0.py`, server log 13:20:49): our own
  readiness check listed 7 services, each with the full VAT trace; the cause was one: the contact «susaeta», created
  during the demo, has **no country**, so the customer VAT zone is unknown (ADR-004: VAT pending blocks sending and
  accepting), plus 4 sale prices not typed. Rejected: credit limit (Odoo 20 only warns), cost check (not reached), a
  traceback (none in the log).
- Tariffs had no **port abroad** in their scope: a freight rate Shanghai → Valencia could not be told from Ningbo →
  Valencia.

## Decision
1. **Port abroad in the tariff scope** (`foreign_port_ids` on the tariff, `line_foreign_port_ids` on a price; engine
   key `foreign_port_id`): the origin port of an import, the destination port of an export, taken from the route of the
   quotation and of the file (ADR-006). Empty = any.
2. **Weekly rate from the quotation**: the «Add supplier price» wizard is offered on lines without supplier price and on
   **manual-amount** services (freight). It pre-fills supplier, Spanish port, **port abroad**, direction, mode, load type
   and, for a manual-amount service, **validity of one week** (valid_from … +6 days). It creates a draft tariff (or a
   price in a draft tariff) with the carrier's offer as document; approval stays a separate step (P19). Nothing is
   written on the quotation.
3. **Manual-amount services use an approved rate when one applies**: `price_cost` tries the tariffs first for a
   manual-amount service; with no applicable approved rate the cost stays a manual amount typed on the line. Freight
   keeps both paths: typed per quotation, or a rate entered once for the route and the week.
4. **History**: tariffs are never edited once approved (ADR-002); a new rate is a new tariff or version with its own
   validity; accepted quotations keep their frozen costs and the name of their source (ADR-003). Draft quotations
   recompute against current tariffs whenever they are edited — by design; drafts are not customer documents.
5. **Readiness message grouped by cause**: Confirm/Send refuse with one paragraph per cause («sale price missing on 4
   services: …», «VAT pending on 8 services because the customer has no country: set it on the contact»); the pricing
   banner says the same. The rule itself (no acceptance with VAT pending or sale price missing) does not change.
6. **Orderer → party**: BOSS business, the orderer is proposed as consignee (import) or shipper (export) when the field
   is empty; an agent's business copies nothing (Ángel). Explicit choices are never overwritten.
7. **Supplier chosen for a service it has no price for** (WFS on an ocean freight): an immediate warning; the line shows
   «no supplier price» until a price of that supplier exists. No supplier is forced on BOSS own fees.
8. The «File» field of the quotation is labelled «Link to an existing file» with its purpose; the file is opened by the
   acceptance, never chosen first.

## Consequences
- A rate entered from a quotation prices every quotation of that route during its week, and only those.
- The quotation shows selling prices (`price_unit`) and, per line, the buying cost with its source; the file receives
  the costs to buy with the supplier at acceptance (ADR-005).
- Open: markup vs margin for a default sale price (the 20 % of the demo is not active); who approves weekly rates and
  whether a one-off typed cost should also become a reusable rate (R2-A1/A2 in `docs/preguntas-abiertas.md`).
