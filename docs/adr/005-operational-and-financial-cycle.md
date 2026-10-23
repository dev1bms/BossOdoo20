# ADR-005 — Operational and financial cycle: contacts, CRM, expediente, purchase, invoicing, profitability

Status: accepted (Belal's mandate of 23/10/2026: «the cycle Contacts → CRM when needed → Quotation → Sales Order →
Expediente → Purchase Orders → Invoices / Bills → Expenses / Credits → cost and profitability» is in scope now;
purchase orders are required for services bought from suppliers). Business rules not documented stay explicit
open decisions (`docs/preguntas-abiertas.md`), never defaults.

## Context
- ADR-001 kept operations and invoicing for later addons that consume `boss_pricing` and the accepted snapshot.
- ADR-001 rejected `product.supplierinfo`: standard seller selection crosses charge bases and ignores the shipment;
  the standard «subcontract» RFQ of `sale_purchase` needs it (verified 23/10: «Defina el proveedor…» without
  supplierinfo) and prices from it, or from `standard_price` (0) when the quantity changes
  (`purchase/models/purchase_order_line.py:545-590`).
- Odoo 17 production has no Purchase app: supplier bills are entered directly (WFS 93 bills). Odoo 19 drafted vendor
  bills from expediente cost lines. Purchase orders are therefore a NEW practice decided by Belal (23/10); who confirms
  them and when stays a human step (no automatic confirmation or sending).
- boss20 (23/10): `purchase`, `sale_purchase`, `account_accountant`, `analytic`, `documents` installed;
  `project`, `hr_expense`, `stock` not installed.

## Decision
One new addon **`boss_expediente`** (depends on `boss_pricing_sale`, `purchase`, `sale_purchase`), plus small
extensions of the existing addons. Odoo documents carry every amount; BOSS adds links, the purchase need and
read-only summaries.

| Need | Odoo standard used | BOSS extension (why) |
|---|---|---|
| Customer / supplier | `res.partner`, `customer_rank` / `supplier_rank`, Customers / Vendors menus | «Customer» / «Supplier» switches that set the rank at once (a new partner is listed before its first document), logistic roles as records (`boss.partner.role`: used in domains, not free text), EORI, contact purpose, «missing data» per role |
| CRM optional | `crm.lead` → «New Quotation» (`_prepare_opportunity_quotation_context`) | shipment fields on the lead, transferred to the quotation once; quotation can start in Sales without a lead |
| Repeat shipment | Sales «Duplicate» | the copy keeps route and services, re-prices from today's tariffs and pricelist, never copies frozen prices, snapshots, expediente, BL/AWB or purchase links |
| Who executes a service | — | `boss_execution` on the sale line: BOSS or supplier (default from the product); a BOSS line has no purchase need and no supplier cost |
| Unknown cost | — | `boss_cost_kind`: BOSS / known / estimate / approved zero / unknown. A supplier line with unknown cost blocks confirmation (Odoo 19 decision B22: pending lines cannot be accepted) |
| Shipment file | no `project` (not installed; its tasks/timesheets are not a shipment) | `boss.expediente` (number `E%(y)s` + 4 digits, as in Odoo 19): parties, route, cargo, containers, references, dates, events, states; one analytic account per file (plan «Shipment files»); links to every document; read-only summaries computed from the documents. A file can be opened before the quotation (pre-alert) and linked later. One accepted quotation may feed several files (owner decision 26/08): `boss.expediente.allocation` gives each file part of each accepted line, never more than accepted; needs, analytic distribution and invoices follow the parts |
| Purchase need | `purchase.order(.line)`, `sale_line_id` (sale_purchase), manual `qty_received` for services | `boss.expediente.cost`: one purchase need per bought service (or extra cost), with its own purchase basis, quantity, unit and currency (sale and purchase never forced to the same unit), accepted cost kept for comparison, ordered / received / billed quantities from the PO lines; its purchase unit can change before ordering (bought per kg while sold per shipment) |
| RFQ creation | draft `purchase.order`, grouped by supplier and currency | action «Create RFQs»: remaining quantity only, rows locked (no duplicates on double click), price from the BOSS expectation and protected from the supplierinfo/standard_price recompute |
| Service performed | manual received quantity on the PO line, bill control «on received quantities» for BOSS services | button «Mark as performed» on the need |
| Customer invoices | `sale.order._create_invoices`, credit notes, analytic from the sale line | invoice selected services (milestones) by filtering `_get_invoiceable_lines`; partial quantities on the draft invoice |
| Supplier bills, credits, expenses | bills from the PO, credit notes, bills without PO on the expediente's analytic account | — |
| Extra cost after acceptance | — | extra need with a classification (covered / re-invoice / needs customer approval / BOSS bears it / disputed); «Re-invoice» adds a priced sale line through the sale manager with a reason and a snapshot (no standard expense re-invoicing: it would create a second sale line for a service already sold) |
| VAT not decided | taxes, fiscal positions | posting a customer invoice is refused while a line's BOSS VAT is pending; posting a supplier bill needs the tax of the supplier document on each BOSS service line (no purchase VAT rule exists yet) |
| Invoice data | `res.partner`, Spanish localization identification (`_l10n_es_has_identification`) | a customer invoice of BOSS services is not posted with its VAT pending (Ángel: a missing zone is never guessed) nor for a customer in Spain (or without country) without NIF or other identification (Odoo 17 practice). The address is shown as missing, not blocking (no decision) — P31 |
| Supplier bill vs customer invoice | company setting | Cristina's written requirement (P30, not confirmed): «warn» by default (vendor bill banner, file to-do); «block» stops posting and payment registration. Exceptions: cost covered or borne by BOSS; freight paid in advance to an agent (sale line enough). Only posted customer invoices count |
| Paid on behalf (duties, import VAT) | vendor bill without purchase order on the file's analytic account | documented exception to the purchase order (Odoo 17/19 practice): the need is «billed without purchase order», defaults to the file's customs broker and is matched to the bill by service and analytic account |
| Expected cost from actual data | — | «Recompute expected cost» on the file runs the same engine with the file's containers, weights, volume, days per service, actual dates and supplier; each change is a `boss.expediente.cost.revision`; the sale and the acceptance snapshot never change; draft RFQs follow, confirmed orders are flagged |
| Changes after acceptance | — | «Add a service» (sales manager, reason, snapshot «addition»; executed by BOSS or a supplier) and «Re-invoice» of an extra cost; lines flagged «added after acceptance» stay out of the margin at acceptance |
| Who sees which figure | field `groups` + `ir.access` domains | figures computed as superuser, each readable by the roles that read its documents in standard Odoo: sales the sale side and the cost shown on the quotation (own files only), purchasing the vendor side, sales managers and accounting everything; company rule on every model (P35, standard until decided) |
| Profitability | analytic items, account move lines, purchase lines | expediente summary from posted documents and open needs, drafts shown apart (not counted): agreed sale, accepted sale and cost, committed purchases, actual cost, cost still expected, forecast cost, margin at acceptance, forecast margin (final only when every cost is billed or closed), invoiced, collected, paid, and «Where the figures come from» |

## Consequences
- One place per fact: request on the lead, agreement on the quotation (+ acceptance snapshot), operational reality
  on the expediente, money in Odoo documents. Moves between them are explicit actions, never silent sync.
- The pricing engine stays the only calculation; the expediente recomputes expected costs with it from actual data,
  never the agreed sale price.
- Margins are «after external costs»; internal (staff) cost is not modelled until Ángel decides a policy.
- Accounts (700/705/600/607/624/suplidos), purchase VAT and approval limits are not invented: they stay open
  decisions listed in `docs/preguntas-abiertas.md`; the system blocks only what would post a wrong VAT.
