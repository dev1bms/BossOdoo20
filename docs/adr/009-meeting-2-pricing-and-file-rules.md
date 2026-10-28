# ADR-009 — Rules confirmed in the second meeting with Ángel: freight date, one tariff per route, approval on entry, carrier family, rate quotations, cost on request, cargo units, file summary by group

Status: accepted (technical), 28/10/2026. Requirements: seven recovered segments of the meeting of 27/10/2026
(transcript given by Belal on 28/10, with his notes). Builds on ADR-002 (tariffs), ADR-003 (quotation), ADR-005 (file
figures), ADR-006 (route), ADR-007 (weekly rates), ADR-008 (default sale price).

## Context (what Ángel said, segment by segment)
1. The template is the case: choosing «IMB FOB» must give incoterm FOB (it did). The final delivery is an estimate,
   months after the quotation. MSC has several legal entities (Spain, Switzerland, USA) that invoice separately, but
   the quotation names **one carrier**: «it's like carrier: one carrier can be several contacts» (Belal) — «that's what
   we need». The delivery address belongs with the consignee, the pickup address with the shipper; both may be
   unknown; the header fields are duplicates.
2. The invoice address is the customer's fiscal address: no header field. Cargo: packages with their **type of unit**
   (cartons, pallets, crates, packages, bottles — the partida of Odoo 17). Customs duties depend on the goods value and
   the **goods code**. FCL needs a visible place for the containers. The wizard showed «Valencia, Shenzhen» for an
   import: read it origin → destination. Weekly validity must start **this week**, and may be two weeks. Ocean freight
   is normally in **USD**. Numbers **the Spanish way, two decimals everywhere**. The supplier document: compulsory or
   not — **ask Cristina**, make it easy to remove. Wendy in China at 4 a.m. cannot wait for an approver in Madrid:
   **«it shouldn't be waiting for approval»**; auto-approval accepted.
3. «The tariff is the same, just the price changes»: one tariff Shenzhen → Valencia with successive rates (1/11,
   8/11, 13/11, 17/11…), the newest valid one used, the old ones kept.
4. **Ocean freight always takes the departure (ETD)**, import or export; air freight too; the other services keep
   the ETA/ETD rule. The selling price is independent of the supplier: THC bought at 180 (MSC) or 190 (CMA), **sold
   at 210**; the templates (the Excel of Cristina) hold the selling rates; the selling price can be changed by hand.
5. BOSS quotes from Excel with fixed selling prices, except the volatile ones (ocean freight: 200 € one day, 25 000 €
   six months later). The selling rates are Cristina's.
6. «Unit price / unit cost» confuse: say selling and buying. Inland trucking is often quoted **case by case**: keep
   the service, accept the quotation, type the cost in the file («have it on zero if necessary»). The supplier must
   be one that does the job (a trucker, or the shipping line). The client is sent **rates per unit** (per container
   of each size, per B/L), not a total: «the client has to make the calculation».
7. The file summary must be the Odoo 17 «Resumen»: buying and selling, **by service group** (Flete, Transporte…),
   buying split into **pending** (no supplier invoice yet) and **definitive** (invoice in the system), selling into
   **pending** and **invoiced**. One file with one partida on one page.

## Decisions
1. **Tariff date per service** (`product.template.boss_tariff_date`): ocean and air freight (FMI, FMI-LCL, FME,
   FME-LCL, FAI, FAE) take the **departure**: the ETD of the quotation, else the **quotation date** (the rate
   available today — «use for quoting the last one available we have»); in the file the ATD, else the ETD, else the
   date of the accepted quotation. Every other service keeps the key date of the shipment (ADR-006). The line
   explanation names the date used and why. *Applied reading to confirm: «quotation date while the ETD is unknown».*
2. **One tariff per supplier, service and route; a new rate is a new version** (`boss.supplier.price.wizard`): the
   wizard finds the latest version of the tariff with the same supplier, scope (direction, mode, load type, carrier,
   Spanish ports, ports abroad, countries, customer, currency) and service, and saves the rate as its next version
   (copy of the prices, new validity, the replaced price updated). The engine already picks «the newest version of
   the same tariff valid on the date», so a rate of 8/11 supersedes the one of 1/11 from 8/11 on while the earlier
   one still prices 5/11. The tariff name carries the route (`MSC FMI CNSHA → ESVLC 2026`). Validity defaults to
   **today + 6 days** and is edited freely (two weeks, a month).
3. **Approval on entry** of freight rates (`res.company.boss_spot_rate_auto_approve`, Sales › Settings, default
   **on**): a rate of a «manual amount» service (freight) typed from a quotation is approved at once by its author
   (who and when recorded, a note «Approved on entry» in the tariff's chatter) and prices the quotation immediately,
   no refresh. Off: the rate waits for a tariff approver as before (R2-A2). Document tariffs (local charges, from a
   PDF) keep the approval flow.
4. **Supplier document required** (`res.company.boss_tariff_document_required`, default **on** = ADR-002 as it
   was): off, tariffs are sent and approved without the file (Cristina decides; nothing to code to change it).
5. **Carrier family** (`res.partner.boss_carrier_group_id`, «Part of carrier»): a legal entity points to its
   commercial carrier; the quotation names the carrier (group or any entity) and tariffs match on the **family**
   (carrier conditions compare families on both sides; airline handlers too). The supplier of the line, the purchase
   and the bill keep the **legal entity** of the tariff. No contact is merged. Data: when MSC Switzerland / USA are
   created (contact migration, R-A4), they get «Part of carrier: MSC».
6. **Rate quotation** (`sale.order.boss_rate_quotation`): per-container lines without shipment containers are priced
   for **one** container of the size on the line; the customer document shows the basis («Container 40'», «B/L»)
   instead of quantities, no amounts per line and **no total**; acceptance waits until the containers are entered
   (the file needs them). The document never shows buying prices (standard document, checked). *Open: whether
   acceptance of a rate list should open the file at once or wait for the booking (Ángel did not say).*
7. **Cost on request** (`sale.order.line.boss_cost_on_request`): a supplier that quotes case by case (trucker)
   gives the line the status «on request»; the quotation is accepted without a manager's exception (B22 kept for
   really unknown costs), the file shows the cost as unknown until a person types it, and the margin follows. The
   service is sold with its own selling price as any other.
8. **Cargo**: `boss_package_type` (CT cartons, PL pallets, CR crates, PC packages, BT bottles, BG bags = Odoo 17
   `x_studio_unit_type`) and `boss_hs_code` (goods code) on the opportunity, the quotation and the file. Duties are
   still an estimate typed by a person: a duty table by goods code is not available (open).
9. **Screen**: header invoice and delivery address hidden (Odoo keeps them: fiscal address and, for the delivery,
   the Spanish-side address chosen in the Shipment tab); pickup address chosen among the **shipper's** addresses,
   delivery among the **consignee's**; «Final delivery to the client (estimate)»; «Selling price (unit)» and «Buying
   cost (unit)»; a «Containers of the shipment» heading; the wizard shows origin above destination and the tariff
   scope reads `CNSZX → ESVLC`.
10. **Two decimals**: selling price, buying cost and supplier price amounts display at least two decimals and only
    more when the value has them (0,3779 €/kg keeps four); stored precision unchanged. The decimal comma and the
    thousands point come from the user's language: BOSS users in Spanish (`es_ES`) see `2.500,00` — a user
    preference, not code (Belal to set it for the BOSS users).
11. **File summary by service group** (`boss.expediente.summary_html`, Summary tab, managers and accounting): the
    product categories of Odoo 17 (`All / Comercial / Flete, Flete terrestre, Locales, Aduana, Almacén, Seguro +
    Courrier, Profit Share`) become child categories of «BOSS services» (Freight, Inland transport, Local charges,
    Customs, Storage and warehouse, Insurance and courier, Profit share, plus Duties and taxes paid on behalf); every
    service is assigned by code on install and upgrade (`boss_services/models/service_groups.py`). The table gives,
    per group and in total: agreed sale, invoiced (posted customer invoices less credit notes), to invoice; cost
    still expected (services not billed), actual cost (posted vendor bills and credit notes), forecast cost; forecast
    margin — the same documents and rules as the file figures, so the total row equals them. One file = one page
    (Odoo 20 has no separate partida screen; a groupage with several houses is several files).

## Consequences
- The existing weekly rate of Ángel (tariff 98, CNSZX → ESVLC, 27/10–7/11) prices an import whose **ETD** or, failing
  that, whose quotation date is in that week; S00311 (origin Shanghai) is still not priced by it: the route differs.
- `check_quote_flow` 5 changed with the rule: the rate is approved on entry and the departure chooses it.
- Checks: `dev/check_meeting2.py` (47 checks on boss20 with the code mounted; the quotation form and the rate document
  are checked after the deploy). Regressions: quote flow, route cases, meeting matrix, chargeable weight, default
  markup.

## Open (decisions, not code)
- Cristina: the Excel selling prices → fixed rules of the general pricelist (the mechanism is ADR-003/008; the
  figures are hers); whether the supplier document is compulsory; which services are «fixed price» and which
  «variable».
- Ángel: acceptance of a rate list (file at once, or at the booking); a duty table by goods code; supplier
  eligibility per service (today: any supplier, with a warning when it has no tariff for the service).
- Belal: Spanish language for the BOSS users (number format); who may approve document tariffs besides Ángel.
