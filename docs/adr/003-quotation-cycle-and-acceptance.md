# ADR-003 — From CRM opportunity to accepted quotation; freeze and explicit re-pricing

Status: accepted (technical). The commercial cycle itself is described for the owners in
`docs/ciclo-crm-oferta.md`.

## Context
- Cristina (A, "exacto"): the comercial builds the offer from the service catalogue, each line with
  sale price and expected cost; only on acceptance the expediente opens with those lines; nothing is
  re-typed; the invoice comes from the same lines.
- Complaints about Odoo 19: hidden standard CRM/Sales, a second entry path ("Nuevo envío"), pricing
  spread over many screens, test data in the user database.
- Odoo 20 confirmed orders are re-priced silently (spike T7c/d) and an unassigned stored compute is
  written as empty by the ORM (`odoo/orm/fields.py`, "fallback to null"), found by our test.

## Decision
1. **Standard path only**: CRM opportunity → "New quotation" (`sale_crm`) → `sale.order`. No second
   entry point. The shipment data needed to price live **on the quotation** (tab "Shipment"):
   direction, mode, load type, Spanish port/airport, carrier, planned date (ETA import / ETD export:
   it picks the tariff version) and planned containers (size × quantity).
2. **Lines = services**. "Add services" creates one line per service and charge basis (one per
   container size present); container quantities come from the shipment. Each line shows the cost
   status, the expected cost (`purchase_price` of `sale_margin`, so margins are standard) and a
   one-click explanation.
3. **Missing price → the right form, then back**: no tariff → "Add supplier price" (pre-filled from
   the shipment, saved into a supplier tariff, sent for approval; never on the quotation); waiting for
   approval / conflict → open the tariffs involved; pending decision → open the service. Dialogs
   return to the quotation, which reloads; approving a tariff refreshes open quotations.
4. **Acceptance = evidence**: on confirm, pending computations are finished (`flush_all`), every
   line is frozen (`boss_price_frozen`) and a `boss.pricing.snapshot` stores shipment inputs, policy
   and, per line, sale price and source, cost, currency, tariff line/version/document/page and
   explanation. Frozen lines skip all price computations and keep their stored values.
5. **Re-pricing is explicit**: only the "Re-price" wizard (sales managers until P07 is answered)
   changes an accepted line, with a mandatory reason, optional cost recomputation and new sale
   prices; it stores a second snapshot with the "before" values and posts the reason.
6. Hooks prepared for later phases (not built): the snapshot is the commercial baseline for the
   expediente; `boss_tariff_line_id` + `boss_cost_amount` are the **expected** cost to compare with
   vendor bills (actual cost); one order may later feed several expedientes and several invoices.

## Consequences
- Business owners stay in standard CRM/Sales screens.
- No re-typing: shipment data, prices and sources travel from the accepted quotation.
- Changing accepted prices leaves a trace (who, when, why, before/after).
