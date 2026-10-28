# ADR-010 — Customer portal: roles granted by BOSS, scope per legal entity, BOSS costs never reach the customer

Status: accepted (technical), 28/10/2026 — first version, **installed on boss20 28/10 12:10** (Belal's approval;
`docs/evidencias/20261028_1222_portal_instalacion.md`). Requirement:
Belal, 28/10/2026 (project owner: portal direction approved for development); confidentiality of costs and margins:
Ángel, meeting of 27/10/2026, and ADR-009 (rate quotations without a total). Module `boss_portal` (depends on
`boss_expediente`, `portal`, `sale`, `account`); the cost-field protection lives in `boss_pricing_sale` and
`boss_expediente` so that it holds with or without the portal module.

## Context (checked in the code and on boss20, 28/10)
- Installed: `portal`, `sale`, `sale_management`, `sale_margin`, `account`, `account_payment`, `payment`, `documents`.
  **Not installed: `website`** (the portal pages work without it; a public website is a separate decision).
  0 portal users on boss20.
- Odoo 20 replaced record rules and model access by one model, `ir.access` (`group_id` empty = **restriction**,
  AND-ed for everybody; with a group = permission, OR-ed).
- Standard portal rules are broad: every portal user of a company sees **all** its quotations
  (`partner_id child_of commercial partner`), all its invoices **and vendor bills**
  (`account_invoice_rule_portal`), and **the purchase orders where the company is the vendor**
  (`portal_purchase_order_user_rule`) — a customer that is also a BOSS supplier (agents) would read BOSS purchases.
  Checked: `dev/check_portal.py` 1 (purchase order visible today).
- Anyone holding the e-mailed token link can sign, accept and start a payment (`/my/orders/<id>/accept`,
  `/transaction`; the latter does not even check `_has_to_be_paid`).
- `purchase_price`, `margin`, `margin_percent` are internal (`sale_margin`), but every `boss_cost_*` field, the supplier,
  the explanations, the markup and the allocations were readable over RPC by any portal user of the line.
- Shipments: `boss.expediente` with containers and events; events have an internal `note`. No tracking integration
  exists in Odoo 20 nor in Odoo 17 (no MSC Track & Trace or BFirst model, field or cron found, read 28/10).
- `boss_web` is the back-office chatter layout, not a customer portal.

## Decisions
1. **Roles on the contact, granted by BOSS** (`res.partner.boss_portal_role`, `boss_portal_customer_id`; only a sales
   manager writes them; the portal account itself is the standard «Grant portal access»):

   | Capability | No role | Tracking | Commercial | Authorised representative | Tracking link (no login) |
   |---|---|---|---|---|---|
   | My Shipments: list, detail, published events | – | ✔ | ✔ | ✔ | one shipment, short view |
   | Published documents of his shipments | – | ✔ | ✔ | ✔ | – |
   | Quotations and orders, selling prices | – | – | ✔ | ✔ | – (token e-mail link: view only) |
   | Customer invoices and credit notes (posted) | – | – | ✔ | ✔ | – |
   | Accept / sign / decline / pay a quotation | – | – | – | ✔ (not a rate quotation) | – |
   | Request a booking of a rate quotation | – | – | – | ✔ | – |
   | BOSS costs, margins, suppliers, tariffs, purchases, vendor bills, files' finances, internal notes | – | – | – | – | – |

2. **Scope = one legal entity**, and it must be the contact's own company (`commercial_partner_id ==
   boss_portal_customer_id`); otherwise nothing (a group company or a third party is a decision, not a default).
   Being a follower, the shipper, the consignee, a notify party, or another contact of the same company grants
   nothing. Stored on the contact as `boss_portal_scope_id` / `boss_portal_sales_scope_id` and read by **restrictions**
   (`security/ir.access.csv`): portal users (`user.share`) only reach quotations, lines, customer invoices and their
   lines of their sales scope; no purchase orders at all (v1). Internal users are not affected (`[] if not user.share`).
3. **Costs are refused at field level** (`base.group_user` on 24 line fields and 4 quotation fields: supplier,
   execution, cost status/amount/currency/kind/steps/missing/estimate/explanation, supplier price, candidates, manual
   cost and its note, on-request, unknown-cost reason, sale status and explanation, markup, VAT trace, file
   allocations; haulier, snapshots, pricing alert; plus the standard `purchase_price`/`margin`). The ORM refuses them on
   read, search, `search_read`, export and `fields_get` to any non-internal user. Snapshots, tariffs, tariff prices,
   files and cost needs have no portal access at all.
4. **Pages send a whitelist, never a record**: `boss.expediente._boss_portal_values("account"|"public")` builds the
   only data a shipment page receives (reference, status, mode, ports and countries, carrier family, vessel/voyage,
   house B/L or AWB, ETD/ETA, ATD/ATA, delivery, containers, published events, published documents). The master B/L /
   AWB, the booking, parties, addresses, amounts, internal notes are not in it. `sudo()` is used only after the
   role and customer check in the controller.
5. **Rate quotation** (ADR-009): own portal page (`sale_order_portal_content_rate`: service, basis «Container 40' HC»,
   unit price, currency, validity, incoterm, route, terms), no quantity, no amount per line, no total (also removed
   from the sidebar, the mobile price row and the page's data attribute), «Rates per unit» in the quotation list,
   own e-mail without amount (`email_template_rate_quotation`), PDF as ADR-009. Never signed or paid
   (`_has_to_be_signed` / `_has_to_be_paid` false). A shipment quotation keeps its quantities, totals and flow.
6. **Accept, sign, decline, pay only by an authorised representative of that customer** (or an internal user): the
   controller passes the viewer to the order (`boss_portal_viewer_uid`); a token link (public), a tracking or
   commercial user only views. The `/transaction` route is guarded too.
7. **Booking request ≠ confirmation** (the timing of the file stays decision M2-C): an authorised representative
   chooses, among the per-container rates of an open, valid rate quotation, how many containers of each (0–99); the
   request is checked on the server (lines of this quotation only, bookable rates only, no price, currency or tax from
   the browser, one pending request at a time), stored on the quotation (`boss_booking_*`), posted as an internal note
   and as an activity for the salesperson. It never confirms, opens a file, invoices or asks for a payment. The
   salesperson enters the containers and accepts through the existing internal flow (or marks the request handled);
   accepting marks it handled.
8. **Events and documents are published explicitly**: an event reaches the customer only with `portal_published` and a
   customer text (`portal_text`); the internal note never; events recorded before stay internal. Documents: only the
   attachments chosen in `portal_attachment_ids` (constraint: attachments of that file only); downloaded through the
   portal route after the scope check; the attachment stays private (`public` false); a master document is published
   only when it is that customer's (warning on the form).
9. **Tracking link**: `portal_tracking_token` (192-bit random, unique per file, compared in constant time), created and
   revoked by staff (a new link stops the earlier one), `/boss/track/<token>` shows the short view (no parties,
   references, container numbers or documents). A file number, B/L or container number never opens anything.
10. **Estimated vs actual**: ETD/ETA are labelled «Estimated»; ATD/ATA/delivery «Actual» only when recorded; a passed
    ETA is never shown as an arrival; unknown values say «Not known yet». No live position: the page says updates come
    from BOSS's records.

## Consequences and limits
- Odoo 20 caches the evaluated access domain per user (`BaseModel._access_domain`): changing a portal role, its
  customer or the contact's company invalidates the ORM cache (signalled to the other workers on commit), otherwise a
  removed role kept working (found on boss20 by `check_portal` 9 and fixed).
- Revocation: removing the role (or archiving the portal user with the standard wizard) cuts quotations, invoices and
  shipments at once; a token e-mail link to a quotation still shows it (standard Odoo; view only) until the quotation
  token is reset. Sharing a quotation by e-mail remains a staff action.
- `website` is not required; installing it later adds the public site, not more data.
- Consolidations (one master, several houses): the portal shows one file = one shipment of one customer; master
  documents are never published automatically (decision M2-I).
- Next phase (automatic tracking): `docs/portal-seguimiento-integraciones.md`.
- Checks on boss20 after installation: `dev/check_portal.py` 46/46 (ORM, real portal users), `dev/check_portal_http.py`
  25/25 (real portal sessions over HTTP), `dev/check_portal_qweb.py` 4/4; tracking link seen in Chrome and revoked (404).
