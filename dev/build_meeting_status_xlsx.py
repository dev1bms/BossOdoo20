"""Build docs/angel-meetings-followup.xlsx: one sheet for Ángel with every point of the two meetings of 27/10/2026,
its status on boss20 (28/10), what he will find in Odoo, what is pending and by whom, and two columns for him to fill
(verdict and notes). Business wording only: no internal codes, test names or commits (those stay in the HTML/matrix).
    python dev/build_meeting_status_xlsx.py"""
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

DONE, VERIFY, PARTIAL, DECISION, OPEN = "Done", "Done – please check on screen", "Partially done", "Decision needed", "Not started"
M1, M2 = "Meeting 1", "Meeting 2"
# (id, meeting, point raised, status, what you will find in Odoo, pending · who)
ROWS = [
    ("1", M1, "Origin and destination (country, port, place)", DONE, "Quotation, opportunity and file carry origin, destination, Spanish port, country abroad and province; the key date is derived from them.", ""),
    ("2", M1, "Manual delivery address when the customer has none", DONE, "«Create and edit» from the delivery field creates a delivery address of that customer.", ""),
    ("3", M1, "Choose one of several warehouses (Leroy Merlin case)", DONE, "The delivery warehouse is chosen among the customer's addresses; its province drives the inland zone.", ""),
    ("4", M1, "Inland transport priced by the warehouse", DONE, "Haulier tariff by zone from the delivery province (Zaragoza and Valencia priced); Madrid shows «no price» until its zones are loaded.", "Madrid zones of the haulier tariff: document needed"),
    ("5", M1, "Export Zaragoza → Barcelona → Tunis", DONE, "Export route: Spanish port Barcelona, country Tunisia, province Zaragoza, key date = departure; inland cost from the same haulier tariff.", ""),
    ("6", M1, "Port abroad in the supplier price", DONE, "Tariffs and prices can be limited to ports abroad (Shanghai priced, Ningbo not).", ""),
    ("7", M1, "Main carrier vs inland carrier (haulier)", VERIFY, "Main carrier on the quotation; the haulier is the supplier of the road line and is carried to the file.", "Ángel: check on a quotation with a road line"),
    ("8", M1, "ETD and ETA as two dates; key date by direction", DONE, "Two fields; the tariff date follows the direction (import: arrival, export: departure).", ""),
    ("9", M1, "Final delivery to the customer is optional, not the ETA", DONE, "Separate optional field «Final delivery to the client (estimate)».", ""),
    ("10", M1, "The key date chooses the tariff version", DONE, "All freight, ocean (FCL and LCL) and air, import and export, takes the tariff valid on the departure (ETD; the quotation date while it is unknown); the other services take the key date; the unloading date never chooses a tariff (see M2-15).", "Ángel: does road transport also take the departure?"),
    ("11", M1, "Side abroad never Spain; inland province", DONE, "Import/export keep Spain on the Spanish side; cross-trade and national traffic added without forcing Spain.", ""),
    ("12", M1, "Incoterm only, no named place", DONE, "Only the incoterm on the quotation; the place comes from the route (ports, province). The «Incoterm location» field was removed from the screen (28/10).", ""),
    ("13", M1, "The template is the case", PARTIAL, "A template fills direction, mode, load type, incoterm, business type and services. Three templates loaded as a proposal: air import FOB, sea import FCL FOB, air export.", "Cristina: validate the three templates; templates for sea export, LCL and road"),
    ("14", M1, "Container cells only where the service is per container", DONE, "Size/type shown only on per-container lines (not on the B/L, for example).", ""),
    ("15", M1, "1 × 40' → 2 × 40' changes the quantities", DONE, "Per-container lines ×2, per-shipment lines ×1; saved and reopened correctly.", ""),
    ("16", M1, "Cargo data optional, no hidden zero", DONE, "Unknown weight or volume stays unknown; no cost is invented from a zero.", ""),
    ("17", M1, "Storage 0 days by default; estimates", DONE, "0 storage days → no demurrage; a number of days → estimate from the carrier tariff; customs duties typed as an estimate.", ""),
    ("18", M1, "Real, volume and chargeable weight (air 167, road 333, sea 1000)", DONE, "Chargeable weight = the higher of real and volume weight with the factor of the mode; the road leg of a sea shipment uses 333.", ""),
    ("19", M1, "W/M for sea, haulier 333, AWB weight", DONE, "Sea W/M: 1 t = 1 m³; the supplier's own factor wins when its document states one; FCL never asks for kg.", ""),
    ("20", M1, "«Super cubic meter»", DONE, "Ángel: it does not exist; only the cubic metre is used.", ""),
    ("21", M1, "Orderer becomes consignee (import) / shipper (export)", DONE, "Proposed automatically for BOSS business; a manual change is kept.", ""),
    ("22", M1, "Agent's business", DONE, "Agent traffic: the agent is not copied as consignee or shipper; the orderer is invoiced.", "Cristina: confirm who is invoiced in agent business"),
    ("23", M1, "The quotation creates the file", DONE, "Confirm creates the file, once; no file is chosen beforehand.", ""),
    ("24", M1, "Sale on the lines, buying traceable to the file", DONE, "Each line shows selling price and buying cost; the costs go to the file to be purchased.", ""),
    ("25", M1, "Supplier → its tariffs (MSC)", DONE, "«Supplier tariffs» tab and buttons on the supplier contact.", ""),
    ("26", M1, "Supplier without a price for the service (WFS on freight)", DONE, "Immediate warning when the chosen supplier has no price for that service.", ""),
    ("27", M1, "BOSS own service without supplier", DONE, "«Executed by BOSS»: no supplier, no cost; the selling price is typed.", ""),
    ("28", M1, "Where a supplier cost comes from", DONE, "ⓘ on the line: tariff, version, validity, document and page.", ""),
    ("29", M1, "MSC 20-page PDF: update the whole tariff", DONE, "«New version» copies all prices; change only what changed; attach the new document.", ""),
    ("30", M1, "Weekly freight cost wizard", DONE, "⊕ on the freight line: route and week; the rate is approved on entry and stored as a new version of the route tariff.", ""),
    ("31", M1, "History is kept", DONE, "Accepted quotations and old tariff versions never change.", ""),
    ("32", M1, "Stable sale price / «PP»", DONE, "Ángel: «PP» does not exist; sale = customer pricelist, typed price, or cost + %.", ""),
    ("33", M1, "+20 % on cost", DONE, "Setting «sale = cost + 20 %» active; a typed price wins; 0 switches it off; rounded to the cent.", ""),
    ("34", M1, "Confirm S00034 («so much error»)", PARTIAL, "Causes identified: customer without country (VAT pending) and four lines without selling price; the message now groups the causes.", "Ángel: set country and VAT number on the customer and the four selling prices, then confirm"),
    ("35", M1, "Fiscal position and taxes", DONE, "BOSS VAT table by service class and customer zone (Spain, EU with VAT number, third country, Canary Islands); no country → VAT pending.", ""),
    ("36", M1, "Credit limit", DONE, "Standard Odoo warning only; nothing changed.", ""),
    ("37", M1, "A whole quotation by screen only", DONE, "A full quotation was typed on screen from customer to Confirm and created its file.", ""),
    ("38", M1, "WFS tariff waiting", DECISION, "WFS tariff (Madrid/Barcelona, 7 prices, document attached) waits for approval.", "Ángel: approve or reject the WFS tariff"),
    ("39", M1, "Cross-trade / national traffic; LCL key date", DONE, "Directions cross-trade (X) and national (N) added; LCL uses arrival or departure, never the unloading date.", ""),
    ("40", M1, "Migration of Odoo 17 contacts and addresses", OPEN, "Not started: the new system has only 2 real customers and 8 suppliers.", "Belal: inventory and mapping of the Odoo 17 contacts"),
    ("41", M1, "PP, MSF, One, OCL, FBA", DONE, "MSF = MSC, One = ONE, OCL = OOCL (carriers); PP does not exist.", ""),
    ("42", M1, "Traceability of every point (asked → built → tested → seen)", DONE, "This table and the compliance matrix.", ""),
    ("M2-1", M2, "FOB template fills incoterm FOB", DONE, "The template sets the incoterm.", ""),
    ("M2-2", M2, "Final delivery is an estimate, months later", DONE, "Label «(estimate)», optional.", ""),
    ("M2-3", M2, "One commercial carrier, several legal entities (MSC Spain, Switzerland, USA)", VERIFY, "«Part of carrier» on each legal entity: tariffs match the whole family; purchases and bills keep the legal entity.", "Mark MSC Switzerland/USA when the contacts are migrated"),
    ("M2-4", M2, "Delivery address with the consignee, pickup with the shipper; no header duplicates", DONE, "Header invoice/delivery addresses hidden; pickup among the shipper's addresses, delivery among the consignee's.", ""),
    ("M2-5", M2, "Type of unit (cartons, pallets…) and goods code", DONE, "«Type of unit» and «Goods code (HS)» on opportunity, quotation and file.", ""),
    ("M2-6", M2, "Customs duties from goods value and goods code", DECISION, "Goods code recorded; the duties estimate is typed.", "Ángel: source of duty rates by code (TARIC) if automatic duties are wanted"),
    ("M2-7", M2, "Clear place for FCL containers", DONE, "«Containers of the shipment» block (size, type, quantity).", ""),
    ("M2-8", M2, "Route read origin → destination («Valencia, Shenzhen» confusion)", DONE, "Origin above destination in the wizard; tariff scope reads «CNSHA → ESVLC».", ""),
    ("M2-9", M2, "Weekly rate valid from this week, two weeks if needed", DONE, "Valid from today, one week by default; both dates editable.", ""),
    ("M2-10", M2, "Ocean freight in USD with exchange rate", DONE, "A USD rate is converted to EUR at the quotation date.", ""),
    ("M2-11", M2, "Spanish number format, two decimals everywhere", PARTIAL, "At least two decimals on all prices (four only for per-kg prices that have them). Comma and thousands point follow the user's language.", "Belal: set BOSS users to Spanish; Ángel: accept the per-kg exception"),
    ("M2-12", M2, "Supplier document compulsory? Easy to remove", VERIFY, "Setting «Supplier document required», on by default; one click to switch off.", "Cristina decides"),
    ("M2-13", M2, "Wendy (China, 4 a.m.) must not wait for an approval", DONE, "Freight typed from a quotation is approved on entry by its author (setting on).", ""),
    ("M2-14", M2, "One tariff per route, successive rates, newest valid one used", VERIFY, "Each weekly rate is a new version of the same route tariff; the newest valid on the date is used; history kept.", "Ángel: check with two consecutive weekly rates"),
    ("M2-15", M2, "Ocean and air freight always take the departure (ETD)", DONE, "Freight services are priced on the departure date; the quotation date while the ETD is unknown.", "Ángel: confirm «quotation date while the ETD is unknown»"),
    ("M2-16", M2, "Selling price independent of the supplier (THC example)", DONE, "A fixed selling price per service wins over cost + 20 %; changing carrier changes cost and margin, not the sale.", "Cristina: the fixed selling prices (Excel)"),
    ("M2-17", M2, "Templates hold the selling prices (Cristina's Excel)", DECISION, "Mechanism ready (general pricelist per service).", "Cristina: Excel files; which services are fixed and which variable"),
    ("M2-18", M2, "«Unit price / unit cost» confusing", DONE, "Columns renamed «Selling price (unit)» and «Buying cost (unit)».", ""),
    ("M2-19", M2, "Inland trucking quoted case by case", VERIFY, "«Cost on request» on the line: the quotation is accepted and the cost typed in the file later.", "Cristina: confirm this rule for road transport"),
    ("M2-20", M2, "Supplier able to do the service (trucker or the shipping line)", PARTIAL, "Any supplier can be chosen, with a warning if it has no price for the service.", "Ángel/Cristina: list of allowed suppliers per service, if wanted"),
    ("M2-21", M2, "Rate quotation: unit rates (20', 40', 40' HC, B/L), no total", VERIFY, "«Rate quotation»: one unit per line; PDF, e-mail and customer portal without total; the booking names the alternatives.", "Ángel: open the file at acceptance or at booking?"),
    ("M2-22", M2, "File summary like the Odoo 17 «Resumen»", DONE, "By service group: agreed / invoiced / to invoice; cost expected / actual; margin.", ""),
    ("M2-23", M2, "One file and one partida on one page", PARTIAL, "One file = one page (covers a single partida).", "Cristina/Belal: how to handle consolidations (one master, several houses)"),
]
STATUSES = [(DONE, "1E7F4F", "E3F4EA"), (VERIFY, "2563A8", "E4EEFA"), (PARTIAL, "A15C07", "FDF0DC"),
            (DECISION, "7A3FA0", "F1E7F8"), (OPEN, "B42318", "FDE8E7")]
FONT, NAVY, INPUT = "Arial", "14324A", "FFF9C4"
thin = Side(style="thin", color="D5DBE1")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="top")

wb = Workbook()
ws = wb.active
ws.title = "Meeting points"
ws.sheet_view.showGridLines = False
ws["A1"] = "BOSS Odoo 20 · Points of the meetings of 27/10/2026 · Status for Ángel's follow-up"
ws["A1"].font = Font(name=FONT, size=14, bold=True, color=NAVY)
ws["A2"] = ("Status on the server on 28/10/2026. Please test the points on https://system.bosscontinental.com and write your "
            "verdict and remarks in the two yellow columns (G, H); return the file to Belal.")
ws["A2"].font = Font(name=FONT, size=9, italic=True, color="6B7785")

HEADER_ROW, FIRST = 12, 13
LAST = FIRST + len(ROWS) - 1
status_range = f"$D${FIRST}:$D${LAST}"
ws["A4"], ws["C4"], ws["D4"] = "Status", "Points", "Share"
ws.merge_cells("A4:B4")
for ref in ("A4", "C4", "D4"):
    ws[ref].font = Font(name=FONT, bold=True, color="FFFFFF")
    ws[ref].fill = PatternFill("solid", fgColor=NAVY)
for i, (status, ink, bg) in enumerate(STATUSES, start=5):
    ws.merge_cells(f"A{i}:B{i}")
    ws[f"A{i}"] = status
    ws[f"A{i}"].font = Font(name=FONT, bold=True, color=ink)
    ws[f"A{i}"].fill = PatternFill("solid", fgColor=bg)
    ws[f"C{i}"] = f"=COUNTIF({status_range},A{i})"
    ws[f"D{i}"] = f"=IF($C$10=0,0,C{i}/$C$10)"
ws.merge_cells("A10:B10")
ws["A10"], ws["C10"], ws["D10"] = "Total", "=SUM(C5:C9)", "=SUM(D5:D9)"
ws.merge_cells("A11:B11")
ws["A11"], ws["D11"] = "Done (including «please check on screen»)", "=IF($C$10=0,0,(C5+C6)/$C$10)"
for r in range(5, 12):
    for c in "ABCD":
        ws[f"{c}{r}"].border = border
        if c != "A" or r >= 10:
            ws[f"{c}{r}"].font = Font(name=FONT, bold=r >= 10)
    ws[f"D{r}"].number_format = "0%"
    ws[f"C{r}"].alignment = Alignment(horizontal="center")
ws["D11"].font = Font(name=FONT, bold=True, size=12, color="1E7F4F")
ws["F4"] = "Your verdicts (column G)"
ws["F4"].font = Font(name=FONT, bold=True, color="FFFFFF")
ws["F4"].fill = PatternFill("solid", fgColor=NAVY)
for i, verdict in enumerate(("OK", "Not OK", "To discuss"), start=5):
    ws[f"F{i}"] = verdict
    ws[f"G{i}"] = f"=COUNTIF($G${FIRST}:$G${LAST},F{i})"
    ws[f"F{i}"].border = ws[f"G{i}"].border = border
    ws[f"F{i}"].font = ws[f"G{i}"].font = Font(name=FONT)
    ws[f"G{i}"].alignment = Alignment(horizontal="center")

headers = ["#", "Meeting", "Point raised", "Status", "What you will find in Odoo", "Pending · who", "Your verdict", "Your notes"]
for col, text in enumerate(headers, start=1):
    cell = ws.cell(row=HEADER_ROW, column=col, value=text)
    cell.font = Font(name=FONT, bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=NAVY if col < 7 else "8A7A00")
    cell.alignment = Alignment(vertical="center", wrap_text=True)
    cell.border = border
for r, (pid, meeting, topic, status, found, pending) in enumerate(ROWS, start=FIRST):
    for col, value in enumerate([pid, meeting, topic, status, found, pending or "—", None, None], start=1):
        cell = ws.cell(row=r, column=col, value=value)
        cell.font = Font(name=FONT, size=10, bold=(col == 1))
        cell.alignment = wrap
        cell.border = border
        if col >= 7:
            cell.fill = PatternFill("solid", fgColor=INPUT)
for status, ink, bg in STATUSES:
    ws.conditional_formatting.add(f"D{FIRST}:D{LAST}", CellIsRule(
        operator="equal", formula=[f'"{status}"'], font=Font(name=FONT, bold=True, color=ink),
        fill=PatternFill("solid", fgColor=bg)))
dv = DataValidation(type="list", formula1='"OK,Not OK,To discuss"', allow_blank=True, showDropDown=False)
dv.error, dv.errorTitle = "Choose OK, Not OK or To discuss", "Verdict"
ws.add_data_validation(dv)
dv.add(f"G{FIRST}:G{LAST}")
for col, width in zip("ABCDEFGH", (6, 10, 38, 20, 52, 36, 12, 40)):
    ws.column_dimensions[col].width = width
ws.freeze_panes = f"C{FIRST}"
ws.auto_filter.ref = f"A{HEADER_ROW}:H{LAST}"
ws.print_title_rows = f"{HEADER_ROW}:{HEADER_ROW}"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.cell(row=LAST + 2, column=1,
        value="Done = built, tested and seen on screen · Done – please check on screen = built and tested, your look on screen "
              "is welcome · Partially done = a business condition is still open · Decision needed = Ángel or Cristina · "
              "Not started. The yellow columns are yours.").font = Font(name=FONT, size=8, italic=True, color="6B7785")

out = Path(__file__).resolve().parent.parent / "docs" / "angel-meetings-followup.xlsx"
wb.save(out)
print(out.name, len(ROWS), "rows", dict(Counter(r[3] for r in ROWS)))
