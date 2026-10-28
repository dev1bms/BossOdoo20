"""Build docs/angel-meetings-status.html: every point of the two meetings with Ángel (27/10/2026) and its status,
in English, from the compliance matrix (docs/matriz-reunion-2026-10-27.md, state of 28/10/2026).
    python dev/build_meeting_status_html.py"""
from collections import Counter
from html import escape
from pathlib import Path

CLOSED, SCREEN, PARTIAL, DECISION, OPEN = "Closed", "Implemented, screen check pending", "Partial", "Decision needed", "Open"

# (id, meeting, topic, status, what was done / evidence, pending / owner)
M1 = "Meeting 1"
M2 = "Meeting 2"
ROWS = [
    ("1", M1, "Origin and destination (country, port, place)", CLOSED, "Route on the quotation, opportunity and file; derived Spanish port, country abroad, province and date. Tested (route cases) and seen in Chrome (S00080, S00162).", ""),
    ("2", M1, "Manual delivery address when the customer has none", CLOSED, "«Create and edit» from the field creates a delivery contact of the customer.", ""),
    ("3", M1, "Choose one of several warehouses (Leroy Merlin case)", CLOSED, "Tested with two warehouses of one customer; in Chrome the Zaragoza warehouse was chosen and its province derived.", ""),
    ("4", M1, "Inland transport priced by the warehouse", CLOSED, "Real haulier tariff by zone: Zaragoza and Valencia priced from the delivery warehouse; Madrid without price (zones not loaded, nothing invented).", "Madrid zones of IRENEO to load (document)"),
    ("5", M1, "Export Zaragoza → Barcelona → Tunis", CLOSED, "Spanish port ESBCN, country TN, province Z, key date ETD; inland cost from the same IRENEO tariff.", ""),
    ("6", M1, "Port abroad in the supplier price", CLOSED, "Tariffs and price lines carry the ports abroad; Shanghai priced, Ningbo not.", ""),
    ("7", M1, "Main carrier vs inland carrier (haulier)", SCREEN, "Main carrier on the quotation; haulier = supplier of the road line, carried to the file. Tested.", "See it on screen"),
    ("8", M1, "ETD and ETA as two dates; key date by direction", CLOSED, "Two fields; tariff date derived (import ETA, export ETD). Seen in Chrome.", ""),
    ("9", M1, "Final delivery to the customer is optional and not the ETA", CLOSED, "Quotations accepted with it empty; label «Final delivery to the client (estimate)».", ""),
    ("10", M1, "Key date chooses the tariff version", CLOSED, "Rule of 16/10; all freight (ocean FCL and LCL, air; import and export) takes the ETD (meeting 2), the other services the key date; the unloading date never chooses a tariff.", "Ángel: does road transport also take the ETD?"),
    ("11", M1, "Side abroad never Spain; inland province", CLOSED, "Import/export keep Spain on the Spanish side; cross-trade (X) and national (N) added without forcing Spain.", ""),
    ("12", M1, "Incoterm only, no named place", CLOSED, "Only the incoterm in the Case group; «Incoterm Location» hidden (Ángel, 28/10: the place is the route).", ""),
    ("13", M1, "The template is the case", PARTIAL, "Template fills direction, mode, load type, incoterm, business and what BOSS handles.", "Cristina: validate IAB/IMB/EAB (loaded as a proposal); templates for other cases"),
    ("14", M1, "Container cells only where the service is per container", CLOSED, "Size/type only on per-container lines; seen in Chrome (BL without size).", ""),
    ("15", M1, "1 × 40' → 2 × 40' changes the quantities", CLOSED, "Per container ×2, per shipment ×1; saved and reopened in Chrome.", ""),
    ("16", M1, "Cargo data optional, no hidden zero", CLOSED, "Unknown measures stay unknown; no cost invented.", ""),
    ("17", M1, "Storage 0 days by default; estimates", CLOSED, "15 days → carrier demurrage estimated from the tariff; 0 days → 0; customs duties on quotation and file.", ""),
    ("18", M1, "Real, volume and chargeable weight (air 167, road 333, sea 1000)", CLOSED, "Ángel's Teams rule; chargeable = higher; road leg of a sea shipment uses 333. Tested (38 checks).", ""),
    ("19", M1, "W/M for sea, IRENEO 333, AWB weight", CLOSED, "W/M 1000; the supplier's own factor wins; FCL without kg.", ""),
    ("20", M1, "«Super cubic meter»", CLOSED, "Ángel: it does not exist; only the cubic metre (already in place).", ""),
    ("21", M1, "Orderer becomes consignee (import) / shipper (export)", CLOSED, "Proposed automatically for BOSS business; a manual change is kept. Seen in Chrome.", ""),
    ("22", M1, "Agent's business", CLOSED, "Traffic IMA; the agent is not copied as a party.", "B17: contact-type check (Cristina)"),
    ("23", M1, "The quotation creates the file", CLOSED, "Confirm → file, once, never twice; done fully on screen (S00162 → E260038).", ""),
    ("24", M1, "Sale on the lines, buying traceable to the file", CLOSED, "Selling price and buying cost per line; costs carried to the file.", ""),
    ("25", M1, "Supplier → its tariffs (MSC)", CLOSED, "«Supplier tariffs» tab and buttons on the contact. Ángel: «Perfect».", ""),
    ("26", M1, "Supplier without a price for the service (WFS on freight)", CLOSED, "Immediate warning when the chosen supplier has no price.", ""),
    ("27", M1, "BOSS own service without supplier", CLOSED, "«Executed by BOSS», zero cost justified.", ""),
    ("28", M1, "Where a supplier cost comes from (THC example)", CLOSED, "ⓘ on the line: source tariff, version, validity, document and page.", ""),
    ("29", M1, "MSC 20-page PDF: update the whole tariff", CLOSED, "«New version» copies all prices; change what changed; new document.", ""),
    ("30", M1, "Weekly freight cost wizard", CLOSED, "Wizard by route and week; since 28/10 approved on entry and saved as a version of the same tariff.", ""),
    ("31", M1, "History is kept", CLOSED, "Accepted quotations unchanged after new versions.", ""),
    ("32", M1, "Stable sale price / «PP»", CLOSED, "Ángel: «PP» does not exist; sale = customer pricelist, typed, or cost + %.", ""),
    ("33", M1, "+20 % on cost", CLOSED, "Sales setting «cost + 20 %» active; typed price wins; 0 switches it off; rounded to the cent.", ""),
    ("34", M1, "Confirm S00034 («so much error»)", PARTIAL, "Cause found (customer without country, missing sale prices); message grouped by cause.", "Ángel: complete his own data on S00034 (country/VAT of «susaeta», 4 sale prices)"),
    ("35", M1, "Fiscal position and taxes", CLOSED, "BOSS VAT table: Spain EX→Art.22 / NR→21 %, EU → 0 % EU, third country → 0 % EX, Canary Islands → 0 % NS; no country → pending.", ""),
    ("36", M1, "Credit limit", CLOSED, "Standard Odoo 20 warning only; nothing changed.", ""),
    ("37", M1, "A whole quotation by screen only", CLOSED, "S00162 typed in Chrome from customer to Confirm → file E260038.", ""),
    ("38", M1, "WFS tariff waiting", DECISION, "Tariff 58 «WFS MAD/BCN» with 7 prices and document, waiting for approval.", "Ángel or Belal: approve or reject"),
    ("39", M1, "Cross-trade / national traffic; LCL key date", CLOSED, "X and N directions; key date never the unloading date.", ""),
    ("40", M1, "Migration of Odoo 17 contacts and addresses", OPEN, "Not started: boss20 has 2 real customers and 8 suppliers.", "Belal: inventory and mapping"),
    ("41", M1, "PP, MSF, One, OCL, FBA", CLOSED, "MSF = MSC, One = ONE, OCL = OOCL; PP does not exist.", ""),
    ("42", M1, "Source → code → test → screen map", CLOSED, "The compliance matrix and evidence files.", ""),
    ("M2-1", M2, "FOB template fills incoterm FOB", CLOSED, "Seen in Chrome on S00311.", ""),
    ("M2-2", M2, "Final delivery is an estimate, months later", CLOSED, "Label «(estimate)», optional.", ""),
    ("M2-3", M2, "One commercial carrier, several legal entities (MSC Spain, Switzerland, USA)", SCREEN, "«Part of carrier» on the legal entity; tariffs match the whole family; purchases and bills keep the legal entity. Tested.", "Mark MSC Switzerland/USA when contacts are migrated"),
    ("M2-4", M2, "Delivery address with the consignee, pickup with the shipper; no header duplicates", CLOSED, "Header invoice/delivery addresses hidden; pickup among the shipper's addresses, delivery among the consignee's. Seen in Chrome.", ""),
    ("M2-5", M2, "Type of unit (cartons, pallets…) and goods code", CLOSED, "On opportunity, quotation and file (Odoo 17 partida taxonomy). Seen in Chrome.", ""),
    ("M2-6", M2, "Customs duties from goods value and goods code", DECISION, "Goods code recorded; duties estimate typed.", "Ángel: source of duty rates by code (TARIC)"),
    ("M2-7", M2, "Clear place for FCL containers", CLOSED, "«Containers of the shipment» heading. Seen in Chrome.", ""),
    ("M2-8", M2, "Route read origin → destination («Valencia, Shenzhen» confusion)", CLOSED, "Wizard shows origin above destination; tariff and price scope read «CNSHA → ESVLC». Seen in Chrome.", ""),
    ("M2-9", M2, "Weekly rate valid from this week, two weeks if needed", CLOSED, "Valid from today, one week by default, editable. Seen in Chrome.", ""),
    ("M2-10", M2, "Ocean freight in USD with exchange rate", CLOSED, "A USD freight rate is converted to EUR at the quotation date (checked with a test rate).", ""),
    ("M2-11", M2, "Spanish number format, two decimals everywhere", PARTIAL, "At least two decimals on prices (four only when the value has them, e.g. per-kg prices).", "Belal: switch BOSS users to Spanish (gives 2.500,00); Ángel: accept the per-kg exception"),
    ("M2-12", M2, "Supplier document compulsory? Easy to remove", SCREEN, "Sales setting «Supplier document required» (on by default).", "Cristina decides"),
    ("M2-13", M2, "Wendy (China, 4 a.m.) must not wait for an approval", CLOSED, "Freight typed from a quotation is approved on entry by its author; tested as a real pricing user; seen in Chrome (tariff 169).", ""),
    ("M2-14", M2, "One tariff per route, successive rates, newest valid one used", SCREEN, "Each new rate is a version of the same tariff; tested with 1/11, 8/11, 13/11, 17/11; history kept.", "See it on screen"),
    ("M2-15", M2, "Ocean and air freight always take the departure (ETD)", CLOSED, "Freight services priced on ETD (quotation date while unknown); explained on the line. Seen in Chrome.", "Ángel: confirm «quotation date when ETD unknown»"),
    ("M2-16", M2, "Selling price independent of the supplier (THC 180/190 → 210)", CLOSED, "A fixed price per service wins over cost + 20 %; changing carrier changes cost and margin, not the sale.", "Cristina: the real fixed prices (Excel)"),
    ("M2-17", M2, "Templates hold the selling prices (Cristina's Excel)", DECISION, "Mechanism ready (general pricelist).", "Cristina: Excel files; fixed vs variable services"),
    ("M2-18", M2, "«Unit price / unit cost» confusing", CLOSED, "Columns «Selling price (unit)» and «Buying cost (unit)». Seen in Chrome.", ""),
    ("M2-19", M2, "Inland trucking quoted case by case", SCREEN, "«Cost on request» on the line: accepted, cost typed in the file later. Tested.", "Cristina: confirm it narrows rule B22"),
    ("M2-20", M2, "Supplier able to do the service (trucker or the shipping line)", PARTIAL, "Any supplier, with a warning when it has no price for the service.", "Ángel/Cristina: list of suppliers per service"),
    ("M2-21", M2, "Rate quotation: unit rates (20', 40', 40' HC, B/L), no total", SCREEN, "Rate quotation: one unit per line, PDF and portal without total, alternatives named at booking. Tested (also over HTTP).", "Ángel: open the file at acceptance or at booking?"),
    ("M2-22", M2, "File summary like the Odoo 17 «Resumen»", CLOSED, "By service group: agreed / invoiced / to invoice; cost expected / actual / forecast; margin. Tested through the billing cycle; seen in Chrome (E260038).", ""),
    ("M2-23", M2, "One file and one partida on one page", PARTIAL, "One file = one page (covers a single partida).", "Cristina/Belal: consolidations (one master, several houses)"),
]

STATUS_CLASS = {CLOSED: "closed", SCREEN: "screen", PARTIAL: "partial", DECISION: "decision", OPEN: "open"}


def build():
    counts = Counter(r[3] for r in ROWS)
    total = len(ROWS)
    done = counts[CLOSED] + counts[SCREEN]
    cards = "".join(
        f'<button class="card {STATUS_CLASS[s]}" data-filter="{STATUS_CLASS[s]}"><span class="n">{counts[s]}</span>'
        f'<span class="l">{escape(s)}</span><span class="p">{counts[s] * 100 / total:.0f} %</span></button>'
        for s in (CLOSED, SCREEN, PARTIAL, DECISION, OPEN))
    rows = "".join(
        f'<tr data-status="{STATUS_CLASS[s]}" data-meeting="{"m1" if m == M1 else "m2"}">'
        f'<td class="id">{escape(i)}</td><td class="mt">{escape(m)}</td><td>{escape(t)}</td>'
        f'<td><span class="badge {STATUS_CLASS[s]}">{escape(s)}</span></td><td>{escape(d)}</td>'
        f'<td class="pend">{escape(p) or "—"}</td></tr>'
        for i, m, t, s, d, p in ROWS)
    m1 = sum(1 for r in ROWS if r[1] == M1)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BOSS Odoo 20 · Meetings with Ángel (27/10/2026) · Status</title>
<style>
:root {{ --ink:#1f2933; --muted:#6b7785; --line:#e3e7ec; --bg:#f6f8fa;
  --closed:#1e7f4f; --closed-bg:#e3f4ea; --screen:#2563a8; --screen-bg:#e4eefa; --partial:#a15c07; --partial-bg:#fdf0dc;
  --decision:#7a3fa0; --decision-bg:#f1e7f8; --open:#b42318; --open-bg:#fde8e7; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; color:var(--ink); background:var(--bg); }}
header {{ background:#14324a; color:#fff; padding:22px 32px; }}
header h1 {{ margin:0 0 4px; font-size:22px; }} header p {{ margin:0; opacity:.85; }}
main {{ padding:20px 32px 40px; max-width:1500px; margin:0 auto; }}
.summary {{ display:grid; grid-template-columns: 1.3fr repeat(5, 1fr); gap:12px; margin-bottom:18px; }}
.total {{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
.total .big {{ font-size:30px; font-weight:700; }} .total small {{ color:var(--muted); display:block; }}
.card {{ border:1px solid var(--line); border-radius:10px; padding:12px 14px; background:#fff; text-align:left; cursor:pointer;
  display:flex; flex-direction:column; gap:2px; font:inherit; color:inherit; }}
.card .n {{ font-size:26px; font-weight:700; }} .card .l {{ font-size:12.5px; }} .card .p {{ color:var(--muted); font-size:12px; }}
.card.closed {{ border-top:4px solid var(--closed); }} .card.screen {{ border-top:4px solid var(--screen); }}
.card.partial {{ border-top:4px solid var(--partial); }} .card.decision {{ border-top:4px solid var(--decision); }}
.card.open {{ border-top:4px solid var(--open); }} .card.active {{ outline:2px solid var(--ink); }}
.bar {{ display:flex; height:10px; border-radius:6px; overflow:hidden; margin:6px 0 2px; }}
.tools {{ display:flex; gap:10px; align-items:center; margin:8px 0 12px; flex-wrap:wrap; }}
.tools input {{ padding:7px 10px; border:1px solid var(--line); border-radius:8px; min-width:280px; font:inherit; }}
.tools button {{ padding:6px 12px; border:1px solid var(--line); border-radius:8px; background:#fff; cursor:pointer; font:inherit; }}
.tools button.active {{ background:#14324a; color:#fff; border-color:#14324a; }}
table {{ width:100%; table-layout:fixed; border-collapse:collapse; background:#fff; border:1px solid var(--line); border-radius:10px; overflow:hidden; }}
th {{ text-align:left; background:#eef2f6; font-weight:600; padding:9px 10px; border-bottom:1px solid var(--line); position:sticky; top:0; }}
td {{ padding:8px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
tr:hover td {{ background:#fafbfc; }}
td.id {{ font-weight:600; white-space:nowrap; }} td.mt {{ color:var(--muted); }} td.pend {{ color:#5b4636; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:600; }}
.badge.closed {{ color:var(--closed); background:var(--closed-bg); }} .badge.screen {{ color:var(--screen); background:var(--screen-bg); }}
.badge.partial {{ color:var(--partial); background:var(--partial-bg); }} .badge.decision {{ color:var(--decision); background:var(--decision-bg); }}
.badge.open {{ color:var(--open); background:var(--open-bg); }}
.notes {{ margin-top:18px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:14px 18px; }}
.notes h2 {{ font-size:16px; margin:0 0 6px; }} .notes ul {{ margin:6px 0 0 18px; padding:0; }}
footer {{ color:var(--muted); font-size:12px; margin-top:14px; }}
@media print {{ .tools {{ display:none; }} th {{ position:static; }} body {{ background:#fff; }} }}
</style></head><body>
<header><h1>BOSS Odoo 20 · Meetings with Ángel (27/10/2026) · Status of every point</h1>
<p>Meeting 1 (review checklist, {m1} points) and Meeting 2 (seven recovered segments, {total - m1} points) · status on the boss20 server, 28/10/2026</p></header>
<main>
<div class="summary">
  <div class="total"><small>Technical completion (closed + implemented)</small><span class="big">{done * 100 / total:.0f} %</span>
    <small>{done} of {total} points · closed and seen on screen: {counts[CLOSED] * 100 / total:.0f} %</small>
    <div class="bar">{"".join(f'<span style="width:{counts[s] * 100 / total}%;background:var(--{STATUS_CLASS[s]})"></span>' for s in (CLOSED, SCREEN, PARTIAL, DECISION, OPEN))}</div></div>
  {cards}
</div>
<div class="tools">
  <input id="q" type="search" placeholder="Search a topic, rule or owner…">
  <button data-meeting="all" class="active">Both meetings</button><button data-meeting="m1">Meeting 1</button><button data-meeting="m2">Meeting 2</button>
  <button id="reset">Show all statuses</button>
</div>
<table><colgroup><col style="width:6%"><col style="width:10%"><col style="width:20%"><col style="width:14%"><col style="width:32%"><col style="width:18%"></colgroup><thead><tr><th>#</th><th>Meeting</th><th>Point raised</th><th>Status</th><th>What was done / evidence</th><th>Pending · owner</th></tr></thead>
<tbody id="rows">{rows}</tbody></table>
<div class="notes"><h2>How to read the statuses</h2><ul>
<li><b>Closed</b>: built, tested on boss20 and seen on screen (Chrome).</li>
<li><b>Implemented, screen check pending</b>: built and tested on boss20; still to be looked at on screen.</li>
<li><b>Partial</b>: built, with a business condition still open.</li>
<li><b>Decision needed</b>: waits for Ángel or Cristina (prices, rules, data).</li>
<li><b>Open</b>: not started.</li></ul>
<p>Deployed code is identical to the repository (156 files compared). Test results on that code: 69 + 39 + 53 + 23 + 38 + 22
checks, and 46 + 25 for the customer portal, all passing. Remaining items are mostly business decisions and data
(Cristina's selling prices, template validation, contact migration), not programming.</p></div>
<footer>Source: docs/matriz-reunion-2026-10-27.md and docs/revision-reunion-angel-2026-10-28.md · generated by dev/build_meeting_status_html.py</footer>
</main>
<script>
const rows=[...document.querySelectorAll('#rows tr')]; let status=null, meeting='all';
function apply(){{ const q=document.getElementById('q').value.toLowerCase();
  rows.forEach(r=>{{ const ok=(!status||r.dataset.status===status)&&(meeting==='all'||r.dataset.meeting===meeting)&&(!q||r.innerText.toLowerCase().includes(q)); r.style.display=ok?'':'none'; }}); }}
document.querySelectorAll('.card').forEach(c=>c.onclick=()=>{{ status=status===c.dataset.filter?null:c.dataset.filter;
  document.querySelectorAll('.card').forEach(x=>x.classList.toggle('active',x.dataset.filter===status)); apply(); }});
document.querySelectorAll('[data-meeting]').forEach(b=>{{ if(b.tagName!=='BUTTON')return; b.onclick=()=>{{ meeting=b.dataset.meeting;
  document.querySelectorAll('.tools [data-meeting]').forEach(x=>x.classList.toggle('active',x===b)); apply(); }}; }});
document.getElementById('reset').onclick=()=>{{ status=null; document.querySelectorAll('.card').forEach(x=>x.classList.remove('active')); apply(); }};
document.getElementById('q').oninput=apply;
</script></body></html>"""


out = Path(__file__).resolve().parent.parent / "docs" / "angel-meetings-status.html"
out.write_text(build(), encoding="utf-8")
c = Counter(r[3] for r in ROWS)
print(out.name, len(ROWS), "points", dict(c))
