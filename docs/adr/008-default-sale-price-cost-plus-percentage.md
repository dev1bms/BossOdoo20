# ADR-008 — Default sale price = expected cost + a percentage (one setting, one pricelist rule)

Status: accepted (technical), 27/10/2026. Requirement: Belal, 27/10/2026 (after talking to Ángel): «activate the
automatic +20 % calculation, allow the sale price to be edited by hand, and let me switch it off». Builds on ADR-003
(sale price sources: agreed pricelist, typed, cost-based rule; frozen on acceptance).

## Context
- Meeting part 2 (R2-A3): Ángel said the +20 % rule was «not active»; the question was whether «20 %» meant a surcharge
  on the cost or a margin on the sale. Belal's instruction says **+20 %**: a surcharge on the expected cost.
- The mechanism already existed since ADR-003 as a standard pricelist rule «Based on: expected cost of the quotation
  line» (`product.pricelist.item.base = boss_line_cost`) with a surcharge (`price_markup`), optional rounding, extra
  fee and minimum/maximum margin per unit. Nothing used it on boss20 (only an archived demo pricelist).
- boss20: 14 companies are on the default pricelist «Tarifa general (EUR)»; COFITEL has its own pricelist with three
  agreed prices (AWB, CSA, ETX).

## Decision
1. **One setting** (Sales › Settings › Pricing › «Default sale price of BOSS services: cost + %») reads and writes **one
   global rule** on the pricelist a new customer gets by default (`_get_partner_pricelist_multi` of the company
   partner: country group, generic default, else the first pricelist). Odoo 20 stores the surcharge as
   `compute_price = markup`, `price_markup = 20`. 0 removes the rule (**switched off**). The rule stays a normal
   pricelist rule: rounding, extra fee or a minimum margin per unit can be added on it by a sales manager.
2. **What it gives**: every service line whose cost is **known** (supplier price, justified 0 or manual cost) gets
   sale = cost + 20 %, status «From the expected cost (pricelist rule)», explanation «Pricelist Tarifa general (EUR),
   rule 'Expected cost of the line + 20 %': expected cost 253,00 € per Container gives 303,60 €». A line whose cost is
   not known gets **no** sale price (never built on zero) and stays «Sale price missing» (ADR-003).
3. **A price typed on the line wins** and is kept when the cost changes afterwards (standard Odoo: the typed price
   differs from the technical price of the rule, so it is not recomputed); explicit re-pricing keeps it too.
4. **A customer's own pricelist wins**: its agreed prices apply; its other services get no automatic price (the global
   rule lives on the default pricelist only). Chaining a customer pricelist to the default one is possible in standard
   Odoo but not set up.
5. A product that is not a BOSS service under the global rule keeps its **list price** (the rule says nothing about it).
6. Accepted quotations are frozen (ADR-003) and never move.

## Consequences
- The percentage is a business parameter owned by Ángel/Cristina; the setting makes it visible and reversible. The
  figure 20 % is Belal's instruction of 27/10/2026, not a documented approval by Cristina.
- Defect fixed on the way: the sale status read the technical price before the (pending) sale price recompute, so a
  manual cost just typed showed the price as «typed by a person» for an instant (`_compute_boss_sale_status`).
- Checks: `dev/check_default_markup.py` (22 checks: setting on/off, cost + 20 %, missing cost, typed price kept, agreed
  pricelist first, non-BOSS product, frozen quotation unchanged).

## Enmienda 28/10/2026 (Belal, F0-A00)
La regla por defecto no se aplica a los servicios marcados «Pagado por cuenta del cliente»: se proponen por el importe
pagado, sin margen. Un precio pactado en la lista del cliente o tecleado se respeta. Detalle y condiciones del suplido
fiscal: `docs/cuentas-suplidos.md`.
