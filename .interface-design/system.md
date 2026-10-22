# BOSS on Odoo 20 — interface system

Decisions for the BOSS screens (pricing workspace, tariffs, quotations). Read before changing any BOSS view.
Source skills: `.claude/skills/` (interface-design for intent and hierarchy, odoo-20.0 / odoo-code-review for the
implementation, web-design-guidelines for review). Odoo 20 source in `odoo-20.0+e.*/` is the technical reference.

## Direction

**Who:** Cristina and the pricing team (enter supplier documents, approve), sales (quote from CRM), Ángel (finance
review). At a desk, with a supplier PDF open next to Odoo, 1366×768 laptops and 1920×1080 screens.
**What they do:** turn a supplier document into prices; know whether a service can be quoted; quote a shipment and
understand every number.
**Feel:** a pricing ledger — dense, exact, traceable. Every number says its unit and its source; nothing guessed.

**Personality:** Utility & Data. **Foundation:** Odoo's own theme (no custom colours, fonts or CSS).
**Depth:** Odoo standard (borders, sheet). **Spacing:** Odoo standard; no hand-written CSS in views except
`white-space: pre-line` for engine explanations.

Rejected defaults: a custom OWL dashboard (→ standard list/form/search with filters), colour-only status (→ badges
with words), one giant screen (→ linked screens, details on open), a second calculation in the UI (→ engine text).

## Signature

**The unit travels with the number.** A price is never shown alone: «260 EUR / Contenedor», «0,05 EUR / kg tasable ·
mín. 20 EUR», «hasta 5: 8; más: 20 (EUR por 100 kg … y día)». Inputs show their basis next to the field
(«EUR por Contenedor», «EUR sobre el coste de toda la línea»). Examples and explanations come from the engine.

## Components (Odoo standard only)

| Need | Pattern | Where |
|---|---|---|
| Status | `widget="badge"` with words + decoration (success/warning/danger/muted); never colour alone | prices, services, tariffs, quotation lines |
| Demo vs real | `web_ribbon` «Demo» (warning) on tariff and price forms; «Real/Demo» filters | tariff, price |
| What blocks an action | `alert alert-warning` checklist at the top of the draft, same rules enforced on the server | tariff |
| Simulation | `alert alert-warning` «Simulación…» above the result | Test pricing |
| Unit of an amount | `o_row`: field + muted computed label | price form |
| Empty vs any | placeholders «Cualquier …» on scope fields + «Alcance revisado» checkbox required to send | tariff |
| Missing vs zero | «Sin coste (cero confirmado)»; empty price row in red (`decoration-danger`) and blocked at sending | price, tariff |
| Long text | computed one-line summary (`scope_summary`, `price_display`), full text on open; `widget="text"` to wrap | lists, forms |
| Row actions | icon buttons with `title` (Material Symbols names: `science`, `picture_as_pdf`, `content_copy`, `format_list_bulleted`, `add_circle`, `info`, `help`, `check_box`) — `fa-*` names do not render in Odoo 20 | lists |
| Navigation | one app «Tarifas y proveedores»: Precios · Tarifas y documentos · Servicios · Proveedores · Probar tarifa | menu |

## Screen order

- **Tariff form:** header (supplier, document, reference, currency | validity, version, demo) → scope summary line →
  tabs **Precios** (first) · **Se aplica a** · **Revisión y aprobación** · **Notas**. Workflow buttons in the header.
- **Price form:** Servicio y origen → Se aplica a → Cálculo (only the method's fields, unit beside each amount) →
  Controles del importe (mín./máx., a consultar, sin coste) → Ejemplo vivo (engine).
- **Prices list:** Código · Servicio · Proveedor · Se aplica a · Base de cobro · Precio (con unidad) · Hasta ·
  Vigencia; currency, dates, document, version optional. Default filter: vigentes + borradores + pendientes.
- **Service (product):** «Listo para cotizar» (estado, proveedores, cálculos usados, «Añadir precio de proveedor»).
  A new supplier is a new price, never a new product (product field `no_create` on the price form).
- **Supplier (contact):** tab «Tarifas de proveedor» (documents, versions, validity, scope, status).

## Widths (list columns, px)

Fixed widths on code 64 · supplier 110 · scope 200 · basis 90 · until 76 · status 150 (readiness 190); service and
price have no width so they share the free space (with no width at all, Odoo gives the space to the longest text, the
scope). Measured cut cells: 1366 px and 1920 px after the change in the report.
Checked at 1366×768: quotation lines 1318/1318 px, no horizontal scroll.

## Decisions

| Decision | Rationale | Date |
|---|---|---|
| Standard views only, no OWL | Every need met by list/form/search, badges, ribbons, alerts; keeps upgrades safe | 2026-10-22 |
| Material Symbols icon names | Odoo 20 renders `icon=` as a Material ligature; `fa-*` shows a dash | 2026-10-22 |
| Demo isolation in the engine | A tariff flag + customer flag, always sent as input: a real customer can never get a demo price | 2026-10-22 |
| «Alcance revisado» required to send | Distinguishes «applies to any» from «not filled in» | 2026-10-22 |
| Zero needs «Sin coste» | A missing price is never a valid zero | 2026-10-22 |
| Readiness not stored | It depends on today's date; searchable through a search method | 2026-10-22 |

## Performance note

Measured on boss20 (22/10/2026, pane visible): full load to list 0.5–2.1 s, menu switch 0.3–0.9 s, every RPC
< 200 ms, no long tasks. Slow loads seen earlier came from a hidden browser pane (background throttling), not Odoo.
The server runs `workers = 0` (threaded); revisit if several users work at the same time.

## Assistant skills used (local, `.claude/` is not in Git)

Installed by hand in `.claude/skills/` (development aids, never Odoo modules):

| Skill | Source | Commit (date) | Licence |
|---|---|---|---|
| interface-design (+ `reference/`, commands in `.claude/commands/interface-design/`) | github.com/Dammyjay93/interface-design `.claude/skills/interface-design` | 2f9be3206855bcb2d1d0af262c8bae25cba6658d (2026-06-20) | MIT (LICENSE) |
| odoo-20.0 | github.com/mart337i/odoo-skills `skills/odoo-20.0` | 634b2db69c0ffb9766a5d16cff09a81ff1df54f4 (2026-10-01) | MIT (package.json) |
| odoo-code-review | github.com/mart337i/odoo-skills `skills/odoo-code-review` | 634b2db69c0ffb9766a5d16cff09a81ff1df54f4 (2026-10-01) | MIT (package.json) |
| web-design-guidelines | github.com/vercel-labs/agent-skills `skills/web-design-guidelines` | 063bee94c3f4df8453406c830b0a7df0f2860278 (2026-08-28) | see upstream |

Guidelines snapshot: vercel-labs/web-interface-guidelines `command.md` @ 434b7f91364665f2f733b310ec54809bf8f37937.
Re-install: copy the same folders from those commits; details in `.claude/skills/SOURCES.md`.
