# ADR-012 — Data migration from Odoo 17: contacts first, one stable link, nothing merged or overwritten

Status: accepted, 03/11/2026 — contact scope approved and loaded on boss20 by Belal (4,237 Odoo 17 records). Detail and
figures: `docs/migracion.md`. Rules: Belal 28/10/2026 (link, no automatic exclusion or merge, every field's
destination, rolled-back sample before the scope) and 29/10/2026 (missing parents, ambiguous matches, exceptions).

## Context
- Production Odoo 17 has 21,921 contacts; only those with business since 2024 are needed in Odoo 20.
- boss20 already held contacts entered by hand (carriers, suppliers, a few customers), some carrying a reference
  «O17:<id>», and BOSS's own company and user contacts.
- Odoo 17 data has duplicates by VAT, several legal entities per carrier (MSC: five), address types Odoo 20 does not
  have («followup») and VATs Odoo 20 rejects.
- Reading tool: the MCP connector of Odoo 17 (read-only). A server-side XML-RPC client exists (`dev/o17_lib.py`), not
  used yet: it needs the connection details in a private file on the server.

## Decision
1. **Stable link:** one Odoo external id per contact, `o17_partner.res_partner_<Odoo 17 id>`, independent of `ref` and
   of the commercial codes. Every run finds the same target; a second run creates and changes nothing.
2. **Existing contacts are linked, never duplicated:** first the manual reference «O17:<id>», then the VAT with or
   without its country prefix, then the exact normalised name among companies without VAT. A child matches only with
   the same parent, type, name, street, postcode and city; an empty name never matches by itself.
3. **Several candidates are never resolved by picking one:** the record waits, listed for review.
4. **Only empty fields are filled** in a linked contact; differences are listed, nothing is overwritten.
5. **No automatic exclusion or merge:** no filter by city, postcode or missing phone or e-mail; two Odoo 17 contacts
   with the same VAT are both loaded and listed. Archived contacts linked to business are loaded archived.
6. **A child never travels alone:** without its parent it waits with a reason.
7. **BOSS's own company and the users' contacts are protected:** linked if they match, never written, no child added
   under them (decision pending).
8. **Every discarded or unloaded value is logged with its reason**; the private register with the original values
   stays outside Git (`.research/`). Bank accounts, credit limits, dunning levels and the KAM are not loaded until
   Ángel and Cristina decide.
9. **Mobile** goes to its own field (`boss_mobile`, «Móvil»), never merged into the phone.
10. **Proof before loading:** a rolled-back trial on the whole scope, then the permanent load, then an acceptance check
    (`dev/check_migration_accept.py`).

## Consequences
- The load can be repeated after new reads (pending files, line items, balances) without duplicates.
- Duplicates by VAT inherited from Odoo 17 remain visible on boss20 until someone decides each pair.
- Scripts: `dev/migrate_partners.py` (loader), `dev/check_migration_sample.py` (rolled-back trial),
  `dev/load_partners.py` (permanent load, boss20 only), `dev/check_migration_accept.py` (acceptance).
