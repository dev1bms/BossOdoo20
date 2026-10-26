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

## Rules
- Standard Odoo first; every customisation is justified in an ADR (docs/adr).
- One matching + compute function used by every screen. Results are explicit: `ok`, `missing_input`,
  `no_tariff`, `pending_approval`, `conflict`, `not_ready`. Zero is never "free" by default.
- Charge bases are independent units: never convert between container, weight, W/M, document…
- Languages: Spanish (main, for the BOSS team) and English (second UI language, code, technical names).
  Source strings in English, translations in `i18n/es.po`. No new Arabic content (existing `ar.po` left as is).
- Business-owner docs and the user guide in Spanish and English.
- Commits: Conventional Commits, no `Co-Authored-By` trailer.
- Tests at the strict minimum that protects the work. **No test of any kind runs on the local machine** (Belal,
  26/10/2026, confirmed 26/10 evening: no Odoo, Docker, databases, builds or test suites, the engine unit tests
  included). Locally: read, edit, `python -m py_compile`, Git and Chrome only. Commit, push to GitHub, then run the tests
  on the server: `dev/server_test.sh <modules>` (throw-away DB `boss20_test_*`, engine tests included), deploy with
  `dev/deploy.sh`, persistent UAT copy `boss20_uat` (`dev/server_uat.sh`) for posting and payments.

## Interface
- UI decisions (Odoo-standard patterns, units next to amounts, badges, widths, icon names): `.interface-design/system.md`.
  Assistant skills (development aids, not Odoo modules) installed locally in `.claude/skills/` (not in Git); sources and
  commits listed in `.interface-design/system.md`.

## Commands
- Tests (server only): `dev/server_test.sh boss_expediente` (Odoo tests, throw-away DB); engine tests run on the server
  with `dev/server_test.sh --engine`. Never `python -m unittest`, `dev/test.sh` or `dev/uat.sh` locally (kept for
  reference only).
- Deploy: `dev/deploy.sh update <modules>` (ships committed files, upgrades with the web stopped), then
  `dev/server_uat.sh update <modules>`.
- UAT checks with evidence: `dev/uat_run.sh <script>` (runs on boss20_uat, saves the output with the tested commit in
  `docs/evidencias/`).
