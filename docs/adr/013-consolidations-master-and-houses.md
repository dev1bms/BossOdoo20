# ADR-013 — Consolidations: a master file with house files

Status: accepted (technical), 03/11/2026. Roadmap item 8 (`docs/hoja-de-ruta.md`). Requirement: Belal, 03/11/2026
(«gather everything, do not break BOSS's work, document it so I understand before and after»). Builds on ADR-005
(file), ADR-009 (review 2 §7: options A and B, «not built»), ADR-010 (portal: one file = one customer), ADR-011
(documents).

## Context: what the sources say

- **Cristina** (e-mail of 28/09/2026, «Plan detallado previsiones» › Explicaciones previsiones A92–A120; «Nuevo Odoo»
  › OPS- exptes A27, A62, sheet «partidas»): the master B/L or AWB belongs to the file («charged per E»); «if one E
  but various P inside that E, we have special costs per partida… 3 HBLs and 3 partidas, one FAD per each partida»;
  cargo, weights and the customs block belong to the partida; staff never know whether a line goes on the E or the P:
  she wants «each item only in its own place» or «one screen with a block for each P and one for the E».
- **Ángel** (27/10, segment 7): one file with one partida on one page; nothing about consolidations (M2-23 «partial»).
- **Odoo 17** (read on 03/11/2026): 20,792 files for 22,063 partidas, so almost every file has one partida. The file
  holds the master document and the shared purchases (22 % of the lines carry no partida); each partida holds its
  HBL, shipper, consignee, cargo, customs (DUA, channel, release), its sales and its invoices. Real case **E260468**:
  one 40' container, five HBLs of five shippers for one importer; the freight, local charges and haulage bought on the
  file; each partida with its own DUA, its customs costs, its ten sale lines and two invoices; the operator split the
  sale of the shared services by hand («Line Distributor», logic undocumented).
- **Odoo 19** built a partida model inside the file with five allocation methods (manual, weight, volume, value,
  chargeable weight); the LCL walkthrough with Flor never closed. Its docstring: «Cristina has not decided real vs
  chargeable weight: the method is always an explicit choice».
- **Industry** (CargoWise, Linbis, Magaya, the Odoo freight apps): a parent «consol» / master shipment with child
  house shipments; the master's transport data flows down to the houses; costs of the consol are apportioned to the
  houses by weight, volume or a set share; P&L per house and per master; one invoice per house.

## Decision: option A, a master file with house files

A **master** is a `boss.expediente` with houses; a **house** is a `boss.expediente` with a `master_id`; a file with
neither is a **single shipment** and behaves exactly as before (94 %+ of BOSS's files).

| | Master | House |
|---|---|---|
| Holds | the master B/L or AWB, carrier, vessel/voyage, booking, dates, containers; the **shared purchases** (freight, local charges, carrier haulage…); `allocation_basis` | its customer, quotation and sale lines; shipper and consignee; HBL/HAWB and its release; cargo and weights; **customs** (DUA, channel, release, guarantee); pickup/delivery; its own purchases (customs, duties); its invoices; `master_share` |
| Transport data | typed here | **copied from the master** (`MASTER_FIELDS`), read-only on the house, re-copied at every change |
| Purchases | ordered here once | services the master buys are **covered** on the house («Bought on the master»: no second order); the house bears `master_share` × the master's cost (forecast and billed) |
| Figures | own figures + consolidated view (sale of the houses, their own costs, consolidated margin) | own sale − (own costs + share of the master) = margin per house |
| Status | «In transit» on the master puts its houses in transit | «Delivered» per house with its own conditions (ADR step 5) |
| Close | financial close only when every house is closed financially | financial close waits for the master's costs (its share is «cost not billed yet») |
| Next step | a master sells nothing itself: never «link the accepted quotation» | as any file |

Shares (`master_share`, stored, computed from the master's `allocation_basis`): chargeable weight (W/M, default: the
basis the carriers charge on), gross weight, volume, equal parts, or manual; largest-remainder rounding so the shares
add up to 100. Houses with no cargo data yet share equally until the data arrives.

Covering (`_boss_cover_house_services`): the purchase needs of a house whose service group (freight, local charges,
inland transport…) is bought on the master are closed with «Bought on the master» and a reason; the house's customs
and its own services keep their needs. Run when a house is linked, and with «Cover the houses' shared services» on the
master; a person can untick it on a need the house really buys itself.

## Why A and not B (partida inside the file)

1. **Nothing moves.** Customs (step 5), delivery conditions, invoicing per customer, next step, margin, portal and
   documents already work per file; option B would have to move them to a new level (XL, plan F16) and touch the
   single-house flow.
2. **Cristina's «each item in its own place»**: the shared data and purchases live on the master, the per-house data
   on the house; nothing can be filed in the wrong place because the two are different records.
3. **Several customers in one consolidation** (groupage) are natural: one house per customer, its quotation, its
   invoice, its portal access; the «same customer» constraint of a file is kept.
4. **The industry model** is a parent shipment with child shipments, not sub-records of one record.
5. **Odoo 17's practice is kept**: shared buys on the E, sales and customs per P, one invoice per P. What changes is
   that the split of the shared cost is computed and explained, not done by hand.

Costs of A, accepted: a house repeats some fields of the master (copied, read-only); a consolidation is two or more
records to open instead of one page (the master's «Houses» tab lists them with their figures and next steps).

## What is not decided (owners) and what is not built

- The basis of the split is a default (chargeable weight) with the alternatives one click away: Cristina never chose
  real vs chargeable weight (Odoo 19 docstring); the master records who changed it.
- The reduced customs fee for several houses in one file (Cristina A120, «check with Laura»): a selling price per
  house, not a rule here.
- The analytic accounting stays per file: the share is a figure of the house (its margin), not an analytic entry on
  the master's bills (Ángel decides if the ledger must carry it).
- Not built: HBL/HAWB and cargo manifest documents (F0-C45), portal pages of a consolidation, migration of Odoo 17
  files with several partidas (F0-C74).

## Checks

`dev/check_file_consolidation.py` (22 checks on boss20, rolled back): a master with one 40' container and three shared
purchases, two houses of two customers sold per W/M, transport data copied and re-copied, shared services covered
and customs kept, shares by chargeable weight / equal / manual that add up to 100, the share in each house's cost,
margin and explanation, the consolidated view of the master, in transit for all, one invoice per customer, the two
financial closes refused in the wrong order, a house cannot be a master, «New house» from the master, and a single
file unchanged. Regressions: `check_file_e2e.py`, `check_work_queue.py`. User guide: `docs/consolidaciones.html`.
