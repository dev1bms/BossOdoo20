# ADR-014 — House documents (HBL, HAWB) and cargo manifest

Status: accepted (roadmap item 11, 03/11/2026). Source: F0-C45 (BOSS issues its own house B/Ls as NVOCC, about 280 in
Odoo 17, and the cargo manifest); Odoo 17 reports 1387 *HBL*, 1143 *WB Template* and 1193 *Cargo Manifest* and server
action 1543 (read-only, 03/11/2026); Odoo 19 analysis `BossOdoo19/docs/boss_reports_brief.md`.

## Context

Odoo 17 kept each document in its own Studio model (`x_bill_of_lading`, `x_air_waybill`) hanging from a «partida», with
one record per type: a consolidation with several houses could not be represented, buttons committed half-way, and the
printed boxes were patched per file. Since ADR-013 a house is a file of its own (`master_id`), so the house *is* the
partida.

## Decision

- No new document model. The house documents are reports of the file (`boss_documents`), with the data the file
  already holds (parties, ports, vessel or flight, containers, packages, weight, volume, goods, HS code) and three new
  fields: freight **prepaid / collect** (proposed from the incoterm: C and D terms prepaid, E and F collect; editable),
  **marks and numbers**, and the **date of issue**.
- A sea file that is not a master has a **house B/L**, an air one a **house air waybill**. It prints as a **DRAFT** for
  the shipper to check until «Issue house document», which refuses while a box is empty (shipper, consignee, ports,
  vessel or flight, packages, gross weight, goods, freight; container numbers on FCL; the master AWB on air) and then
  gives the document the file's number (as Odoo 17 printed the partida's) unless one is typed, and today's date.
  Express B/L (zero originals) when the B/L release is «sea waybill», otherwise three originals.
- The **cargo manifest** is printed from a master (one line per house) or a single file (one line); without the agent
  abroad it prints a red warning in the consignee box, as the Odoo 17 report did.
- The documents keep the boxes of the Odoo 17 reports and are printed in English whatever the user's language
  (international transport documents), on A4 low margins.
- The three documents are in the file's ⋮ › Print menu (Belal looked for them there, 03/11/2026); the header only
  keeps «Issue HBL» / «Issue HAWB» until issued. A file without that document prints one line saying why and where.
- Nothing is sent from Odoo: the operator prints and sends.

## Not done (reversible, later)

The IATA air waybill on its pre-printed form and its conditions, the B/L clauses on the reverse, a check that long
party texts fit their box (Odoo 17 `_print_length_warning`), and locking a B/L once issued (today it can be reprinted
after a change, and the change stays in the file's history).
