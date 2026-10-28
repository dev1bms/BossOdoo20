# CLAUDE.md — BOSS on Odoo 20

Odoo 20 Enterprise addons for BOSS Continental (Spanish freight forwarder: sea FCL/LCL, air, road;
import/export; customs). First goal: pricing (supplier cost + sale price on quotations), then operations.

## Sources and boundaries
- Odoo 20 source (read-only, never in Git): `odoo-20.0+e.20261020/`. Verify every field/API there.
- Knowledge only (read-only, never deploy, never copy modules): Odoo 19 project
  `C:\Users\BelalAlswerki\Documents\BossOdoo19`, production Odoo 17.
- Target environment: `boss@100.87.98.15:~/BossOdoo20`, DB `boss20`, https://system.bosscontinental.com.
- Supplier PDFs and real prices: never in Git. Research notes with real figures live in `.research/` (ignored).
- Business rules are approved by Cristina (services, pricing, operations) or Ángel (finance, VAT). Code
  never invents one: an undecided rule stays an explicit status (`pending decision`), never a guess.

## Architecture (see docs/adr/)
- `boss_services`: service catalogue = standard `product.product` (type service) + charge bases (`uom.uom`).
- `boss_pricing`: supplier tariffs (document, validity, approval) + pure-Python engine (`engine/`) + one
  matching/compute service. No dependency on sales.
- `boss_pricing_sale`: shipment inputs on the quotation, cost/sale per line, missing-price actions,
  acceptance snapshot and explicit re-pricing.
- `boss_web`: web client only (chatter below the form on every screen size); no models.
- `boss_portal`: customer portal on the standard Odoo portal (roles granted by BOSS, scope per legal entity, rate
  quotations without totals, booking requests, My Shipments, tracking link); BOSS costs never reach it (ADR-010).

## Rules
- Standard Odoo first; every customisation is justified in an ADR (docs/adr).
- One matching + compute function used by every screen. Results are explicit: `ok`, `missing_input`,
  `no_tariff`, `pending_approval`, `conflict`, `not_ready`. Zero is never "free" by default.
- Charge bases are independent units: never convert between container, weight, W/M, document…
- Languages: Spanish (main, for the BOSS team) and English (second UI language, code, technical names).
  Source strings in English, translations in `i18n/es.po`. No new Arabic content (existing `ar.po` left as is).
- Business-owner docs and the user guide in Spanish and English.
- Commits: Conventional Commits, no `Co-Authored-By` trailer.
- Tests at the strict minimum that protects the work. **Policy of Belal, 27/10/2026: all work, execution, trials and
  checks happen on the server database `boss20` only.** No test of any kind on the local machine (no Odoo, Docker,
  databases, builds or test suites, the engine unit tests included; locally only read, edit, `python -m py_compile`, Git
  and Chrome). No throw-away or copy databases on the server either (`dev/server_test.sh`, `boss20_test_*` and the UAT copy
  `boss20_uat` are no longer used). On boss20 it is allowed to create, change and delete clearly named test records,
  confirm sales and purchases, perform services, post customer and vendor bills and credit notes, register payments and
  reconcile inside Odoo; test entries may consume document numbers and stay in boss20. Test records are cancelled or
  deleted only the ways Odoo supports, never by disabling accounting safety rules. Module updates, settings, deploys and
  restarts on boss20 need no new approval. External effects stay off: no real bank transfer, no documents to tax
  authorities, no messages to customers or suppliers (outgoing mail and external connectors disabled during tests).
  Odoo 17 and Odoo 19 stay read-only. This permission covers execution and testing: it never turns a business proposal or
  a tariff into a decision approved by Cristina or Ángel.

## Interface
- UI decisions (Odoo-standard patterns, units next to amounts, badges, widths, icon names): `.interface-design/system.md`.
  Assistant skills (development aids, not Odoo modules) installed locally in `.claude/skills/` (not in Git); sources and
  commits listed in `.interface-design/system.md`.

## Commands
- Deploy: `dev/deploy.sh update <modules>` (ships committed files, upgrades boss20 with the web stopped).
- Checks with evidence on boss20: `dev/uat_run.sh <script> boss20` (saves the output with the tested commit in
  `docs/evidencias/`); scripts via `dev/server_shell.sh` (DB boss20). UI checks with Chrome on
  https://system.bosscontinental.com.
- `dev/server_test.sh`, `dev/server_uat.sh`, `dev/test.sh`, `dev/uat.sh`: kept for reference only, not used (policy 27/10).
