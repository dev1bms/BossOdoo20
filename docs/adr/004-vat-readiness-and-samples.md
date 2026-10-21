# ADR-004 — VAT treatment, quotation readiness and reference samples

Status: accepted (technical). Business values pending: P17 (tax mapping), P05 (pending costs).

## VAT
- Ángel's rules (final, 31/08/2026) are implemented as pure functions (`boss_pricing_sale/models/vat_rules.py`):
  base class NS/EX/NR per service; NR goes through the origin/destination zone pair and the customer zone; a
  missing zone is pending. Zones come from the Spanish port (Canary flag), the country abroad and the customer.
- No file maps the classes to Odoo taxes (checked: calculator, concepts workbook, Odoo 19). The mapping is a
  company setting (three taxes). Empty = the line VAT is **pending**; product default taxes are not used for
  BOSS services (they would be a guess).

## Readiness
A quotation cannot be **sent or confirmed** while a BOSS line has VAT pending or a sale price missing (zero
without «free of charge»). A pending cost only warns (P05 open). The check runs in the server methods, so it
also applies to portal acceptance and RPC.

## Reference samples
- Real supplier tariffs used for validation live in a private file (never in Git). `boss.tariff.
  _boss_import_tariffs()` loads them idempotently (key in `ir.model.data`, existing records never rewritten),
  attaches the PDF and submits them; it never approves.
- Expected results are hand-computed from the documents by an independent reading, then compared with
  `boss.pricing` (test and server check with rollback). Expected values are never changed to make a test pass.
