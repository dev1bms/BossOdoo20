## Tests

- Engine without Odoo: `python -m unittest discover -s addons/boss_pricing/engine/tests -t addons/boss_pricing`.
- Odoo on a throw-away database (local Docker, deleted afterwards): `dev/test.sh init` once and
  `dev/test.sh run boss_pricing_sale "/boss_pricing,/boss_pricing_sale"`.
- **Reference examples**: 45 cases hand-computed from supplier documents (MSC, Hapag, CMA, WFS, IRENEO) are compared with
  the calculation. Real amounts live in a private file, never in the repository.

## Deployment

`dev/deploy.sh update <modules>`: checks the target is the BOSS Odoo 20 environment, ships only what is committed in
Git, updates with the web service stopped and starts it again. It never touches Odoo 17 or Odoo 19.

## Server environment

Scripts in `dev/` run with `dev/server_shell.sh <script> [private file]` (checks the target is the `boss20` database;
the private file is mounted only during the run and deleted):

| Script | What it does |
|---|---|
| `setup_company.py` | Company data (from Odoo 17), EUR, PGC PYMEs chart, pricelists, languages. Does not choose taxes per VAT class |
| `server_trial.py` | [Guided trial](#/prueba) data marked [DEMO]; tariffs sent for approval, never approved |
| `server_trial_verify.py` | Whole walkthrough as a test salesperson and approver; rolled back at the end |
| `verify_references.py` | Reference examples on the loaded tariffs; rolled back at the end |

## Bulk tariffs

The importer (`boss.tariff._boss_import_tariffs`) creates tariffs from a structured file: supplier, document, page,
validity, scope and prices. It is idempotent (fixed key per tariff; never rewrites existing records), attaches the PDF,
sends for approval and **never approves**. `dev/verify_references.py` checks the examples on a database without changing
it (everything is rolled back at the end).

## Translations

Source texts in English; Spanish in each module's `i18n/es.po` (`dev/test.sh pot <module>` and `dev/po_merge.py`).
