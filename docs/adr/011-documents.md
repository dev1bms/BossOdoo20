# ADR-011 — BOSS documents: one layout, one shipment block, charge bases always printed

Status: accepted (technical), 28/10/2026 — module `boss_documents`, installed on boss20 (see
`docs/evidencias/20261028_documentos.md`). Requirement: Belal, 28/10/2026 («the design of the invoice and of every
document exported from BOSS Odoo 20 must suit BOSS: the business, Ángel's and Cristina's requests, international
practice»). Related: ADR-009 (rate quotation without totals, selling price / buying cost labels), ADR-010 (nothing of
BOSS's costs reaches the customer), meeting 2 M2-4 (header addresses), M2-11 (two decimals, Spanish format).

## Context (read on 28/10/2026)
- **boss20 had no document layout at all**: no template, no colours, no footer, no bank account; invoices printed
  the raw Odoo default, without units (the «Units of Measure» group has no user, so Odoo hid the charge base) and
  without any shipment data.
- **Production Odoo 17** prints the standard Odoo layout with the BOSS identity: teal `#64a8af`, navy `#003a5c`, Lato,
  footer «+34 914 90 01 12 boss@bosscontinental.com https://bosscontinental.com/», Santander IBAN on the invoice,
  30 days. Lines are free text that repeats the invoice number and the calculation («GESTION CON PROVEEDORES EN CHINA
  (160€ x 1 DIAS)»). No shipment block either: the operator writes the references by hand.
- Odoo 20 offers eight document templates (Light, Bubble, Wave, Folder, Center, Dual, Lines, Compact) and seven
  table designs (light, boxed, bold, striped, bubble, column, compact), all configured per company in Settings.
- What a forwarder's customer, agent or supplier expects on a document (industry practice: carriers' and NVOCC
  invoices, FIATA documents): the **file reference**, the **customer's reference**, shipper and consignee, **origin →
  destination** with UN/LOCODE, mode and load type, incoterm, vessel/voyage or flight, **B/L or AWB numbers (master
  and house)**, container numbers, ETD/ETA or actual dates, packages, gross weight, volume and chargeable weight,
  goods and HS code; charges listed with their **basis** (per container, per B/L, per kg, per shipment) and the VAT
  treatment per line; the legal mentions of a Spanish invoice (NIF of both parties, taxable base per rate, exemption
  article when 0 %), payment terms and bank account.

## Decisions
1. **Standard Odoo template, BOSS identity, set once.** Template «Light» (`web.external_layout_standard`), table
   design «striped» (long lists of charges stay readable), Lato, primary `#64a8af`, secondary `#003a5c`, footer with
   phone, e-mail and web. Applied by the installation hook only to a company that has **no** template yet; from then
   on Settings › General › Document layout is the single source (the module never overwrites it). On 28/10/2026 (14:13 UTC) Belal
   chose «Folder» with «bubble» tables there; colours, font and footer kept. No custom layout
   template: the standard one is maintained by Odoo and configurable by BOSS.
2. **One shipment block on every document**, built by one method per model (`_boss_document_block()` on
   `boss.expediente`, `sale.order`, `account.move`, `purchase.order`) and printed by one QWeb template
   (`boss_documents.shipment_block`) under the dates: header line «File E260038 · Quotation S00162 · Your reference
   PO-…», three columns **Route** (traffic, from, to, incoterm, shipper, consignee) · **Transport** (carrier,
   vessel/voyage, B/L or AWB master/house, booking, customs reference, departed or ETD, arrived or ETA, delivered) ·
   **Cargo** (containers with numbers, packages and type of unit, pallets, gross weight, volume, chargeable weight,
   goods, HS code), and the line «Services of BOSS: pickup, customs at origin, main carriage, delivery». Empty rows
   are not printed. The block comes from the **file** when the document has one (actual data), otherwise from the
   shipment data of the quotation; an order without shipment data (a non-BOSS sale) prints no block.
3. **Only operational data in the block**: never a cost, a margin, a supplier price, a tariff or an internal note
   (ADR-010). The purchase order variant drops the customer's reference, the quotation number and the scope line.
4. **Charge base always printed** next to the quantity on invoices, quotations and purchase orders (the group
   restriction of Odoo is removed: «1 Container», «1 B/L», «666 kg»), because the basis is part of the price.
5. **No shipping-address duplicate**: when a document has a shipment block, Odoo's «Shipping address / Invoicing
   address» block is not printed (the pickup and delivery places are in the block; M2-4). The standard «Source» column
   of the invoice is replaced by the quotation named in the block.
6. **Dates say what they are**: «Departed» / «Arrived» only for actual dates; otherwise «ETD» / «ETA» (ADR-010 §10).
7. **Legal mentions stay standard Odoo data**: the exemption text of each 0 % tax is the tax's «Legal notes»
   (`account.tax.invoice_legal_notes`, printed by Odoo under the lines); the NIF of both parties, the taxable base per
   rate, the payment term and the bank account are standard. Their **content is Ángel's**: see «Pending» below.

## Not done (on purpose)
- No redesign of the line text: the description stays the service name of the line (the calculation is visible as
  quantity × basis × unit price, not inside the text as in Odoo 17).
- No new document types (booking confirmation, arrival notice, file cover sheet, AWB/B/L print): candidates for a
  next ADR once Cristina lists the operational documents BOSS sends.
- The customer portal shows the same quotation document (ADR-010); the e-mail templates are untouched.

## Pending (data, not code)
- **Ángel**: bank account to print on invoices (Odoo 17 prints the Santander account; boss20 has none: Accounting ›
  Configuration › Bank accounts, then the journal); the legal notes of the 0 % sale taxes («0% EX S», «0% S NS»,
  «0% UE S» already has the EU reverse-charge text; the Spanish export/transport exemption articles — Ley 37/1992
  art. 21/22/64 — are his call); payment term text; company registry line for the footer («Inscrita en el Registro
  Mercantil de Madrid…») if wanted.
- **Belal/Cristina**: a higher-resolution logo if the current one prints soft; the choice between «striped» and
  «light» tables after seeing both on paper (one click in Settings).

## Checks
`dev/check_documents.py`: WIP mode 9/9 (xpaths, builder, block template); installed mode renders the quotation,
invoice and purchase order of a complete [PRUEBA] file as HTML and PDF in a rolled-back transaction (see the
evidence file for the figures and the PDFs seen).
