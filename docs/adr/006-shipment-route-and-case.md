# ADR-006 — Shipment route as origin → destination, ETD/ETA, who orders, the template as the case

Status: accepted (technical), 27/10/2026. Requirements: `docs/reunion-angel-2026-10-27.md` (meeting Belal–Ángel).

## Context
- Ángel (27/10/2026, reviewing an FCL import quotation on boss20): a shipment is described as **origin → destination**
  (country, port or airport, place), with the **port abroad**; the Spanish side is the destination of an import and the
  origin of an export; the province of the inland leg comes from the **delivery (import) or pickup (export) address**,
  a customer may have several warehouses; **ETD and ETA are two fields** (the key one: ETA for an import, ETD for an
  export); the party who orders is a client or an **agent** (third letter of the traffic code, B/A); the **quotation
  template is the case** and must fill direction, mode, load type, incoterm and what BOSS handles; air chargeable weight
  = the higher of gross weight and volume × **167**; storage estimate is **0** unless the customer says otherwise.
- Odoo 17 (production, read only) works that way: `x_spot` has origin/destination port and country and one
  pickup/delivery address (delivery contacts of the customer); `x_dashboard` has ETD/ETA, an «important date»
  (import ETA/ATA, export ETD/ATD) and the «Orderer»; `x_traficos` holds I/E/X/N × M/A/T × A/B; chargeable weight uses
  fixed factors by mode.
- Odoo 20 had, since ADR-003, the **pricing inputs** on the quotation: Spanish port, country abroad, inland province and
  one planned date. Tariffs (ADR-002), VAT (ADR-004) and the file (ADR-005) read those names.

## Decision
1. **One route model** `boss.shipment.route` (abstract, `boss_pricing_sale`) used by the quotation and the opportunity;
   the file has the same fields without prefix. Stored inputs: whose business (`boss_business`: BOSS client / agent's
   client), direction, mode, load type, main carrier, origin country / port / pickup address / place, destination
   country / port / delivery address / place, ETD, ETA, gross weight, volume, AWB weight.
2. **Pricing inputs are derived**, never typed twice: Spanish port = destination port (import) or origin port
   (export); country abroad = the other side's country; inland province = province of the Spanish-side address; tariff
   date = ETA (import) or ETD (export), the other one if the key one is empty. They stay stored fields with the same
   names, so tariffs, VAT, snapshots and files keep one meaning per name. Records written before this ADR (no origin or
   destination) keep their values; the migration fills origin/destination from them.
3. **Traffic code** computed from direction, mode and business (IMB, EAB, IMA…, decision B13). Cross-trade (X) and
   national (N) traffic are not modelled yet (open A2).
4. **The template is the case**: `sale.order.template` gets direction, mode, load type, incoterm and business (and, in
   `boss_expediente`, what BOSS handles). Choosing it fills the quotation; what it leaves empty stays.
5. **Air chargeable weight**: volume weight = volume × 167 (IATA 1:6000), chargeable = max(gross, volume weight). Until
   the AWB exists, prices «per chargeable kg of the AWB» use it and the explanation says «ESTIMATED». Prices with their
   own volumetric factor (supplier documents) keep it. No general factor for road or sea (open A1).
6. **Storage estimate** = 0 days by default (the «Days indicated» box leaves the screen).
7. **Ports and airports abroad** come from Odoo 17 `x_puertos` (via the Odoo 19 import, 9,528 records): master data,
   loaded by `dev/load_ports.py`.
8. Labels: «Ordered by» (partner of the quotation and file), «Main carrier», «Final delivery to the client».

## Consequences
- The user describes the shipment once, as the business does; pricing receives the same inputs as before.
- A quotation changed after this ADR recomputes its Spanish port, country abroad, province and tariff date from the
  route: changing an origin or destination can change costs (as changing the port did before).
- The lead form shows the same route; its quotation receives it unchanged.
- Open: A2 X/N traffic, A3 orderer of an agent file (B17), A4 contact migration, A5 LCL key date. A1 resolved below.

## Amendment (27/10/2026): chargeable weight for every transport mode — A1 resolved

Ángel, Teams message of 27/10/2026 («Peso real, Peso volumen y peso cargable»): real weight in kg; volume weight =
CBM × factor of the mode, **air 1 CBM = 167 kg, road 1 CBM = 333 kg, sea 1 CBM = 1000 kg**; chargeable weight =
**always the higher of the two**; suppliers charge BOSS on the chargeable weight and BOSS charges its customers on it.

Decision (replaces §5 for the factor): one source of truth, `MODE_VOLUMETRIC_FACTORS` and `chargeable_kg()` in
`boss.shipment.route`, used by the quotation, the opportunity and the file (volume weight and chargeable weight stored
per record) and passed to the pricing engine as the input `chargeable_kg`.
- **Buying**: a supplier price «per chargeable kg» (basis `chargeable_kg`) uses the factor stated by its document when
  there is one (ADR-002: the document rules, e.g. IRENEO 333) and otherwise the shipment's chargeable weight (factor
  of the mode). Air handlers that charge on the AWB figure keep the basis `awb_kg` (the chargeable weight estimates it
  until the AWB exists). Sea W/M (1 t ↔ 1 m³) is the same rule as 1000 kg/CBM.
- **Selling**: the quantity of a line in a weight-based charge basis is the chargeable weight of the shipment (unit
  «kg tasable terrestre»: quantity source `chargeable_kg`, applied by `dev/setup_chargeable_uom.py`; «kg tasable
  aéreo» keeps the AWB weight); the customer's price per kg is applied to it. Containers, shipment, documents and
  other bases are untouched.
- **Unknown is not zero**: with the gross weight or the volume unknown, no chargeable weight exists (0 shown = not
  known), weight-based supplier prices report «missing shipment data» and the line quantity is not changed; the
  measures can be completed later on the file, which computes the same figures.
- **History**: accepted quotations are frozen (ADR-003) and existing tariffs are not touched; the earlier air-only
  estimate with one measure known no longer applies (both measures are needed), which only affects drafts when they
  are edited.
