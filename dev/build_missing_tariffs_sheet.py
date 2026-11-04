"""Build the sheet of supplier tariffs still missing on boss20, to ask Cristina (Belal, 04/11/2026). Coverage read from
the ACTIVE tariffs on boss20 on 04/11/2026 (archived [DEMO] tariffs excluded). No prices. Excel stays out of Git:
    python dev/build_missing_tariffs_sheet.py "<NEW ODOO folder>/missing-tariffs-2026-11-04.xlsx"
"""
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROWS = [
    # (group, codes, missing, already in Odoo, what we need)
    ("Shipping lines – local charges", "THC, T3, GLO, BL",
     "Local charges of MSC from origins other than China and for export, and of the other lines.",
     "MSC, import from China only.",
     "The current local charges of MSC (other origins, export) and of ONE, Maersk, OOCL, ZIM, CMA CGM, Hapag-Lloyd."),
    ("Shipping lines – local charges", "CES",
     "Container release: no tariff at all.", "Nothing.",
     "The CES price of each line and port, import and export."),
    ("Demurrage and storage", "DEM, OCU",
     "ZIM, and every line for export.",
     "Import: MSC, ONE, Maersk, OOCL, CMA CGM, Hapag-Lloyd (Valencia, Barcelona, Algeciras).",
     "ZIM tariff (import) and the export tariffs of the lines we use."),
    ("Detention", "DET",
     "Export detention: nothing loaded.", "Nothing.",
     "The detention tariff (free days and daily price) of each line we use for export."),
    ("LCL", "THC-LCL",
     "Transglory THC for LCL.", "The calculation is ready (the higher of tonnes and m³).",
     "Transglory's tariff document."),
    ("LCL", "T3 (per tonne)",
     "T3 per tonne for LCL, import and export.", "Only T3 per container (MSC).",
     "Who charges it and the price per tonne, and whether it is «per tonne or fraction»."),
    ("Customs", "DEX",
     "Export customs clearance.", "Import clearance (FAD) of Ramos Vila and Aducex.",
     "The export clearance prices of Ramos Vila and Aducex."),
    ("Customs", "FAD",
     "Special price per partida when one shipment has several house B/Ls.", "Normal FAD price per declaration.",
     "Confirmation with Laura of the price per partida (around 59 €?)."),
    ("Customs", "ROH, SOI, INS, SAN",
     "No fixed price.", "The operator types the cost per shipment, as you said.",
     "Only if the brokers have a fixed price per document: that list."),
    ("Inland transport", "TTE-FCL",
     "Container haulage.", "Conventional road transport of IRENEO (by kg).",
     "The haulier tariffs for containers, by zone or city."),
    ("Inland transport", "TTE-CON, FS",
     "Madrid zones of the haulier tariff, and the fuel surcharge.", "IRENEO road tariff without the Madrid zones.",
     "The Madrid zones and the current fuel surcharge % of each haulier."),
    ("Air handling", "HAN, ETX, ALM, AWB",
     "WFS export ETX and AWB; WFS tariff waiting for approval.", "WFS Madrid and Barcelona (waiting for Ángel); IRENEO Madrid.",
     "WFS export ETX and AWB, if they charge them."),
    ("Air handling", "HAN, ETX, ALM, AWB",
     "Swissport, IAS, SAASA and Iberia: nothing loaded.", "Which handler serves each airline at each airport (from Odoo 17).",
     "Their import and export prices at Madrid, Barcelona, Valencia, Málaga and Bilbao."),
    ("Agents", "PFT",
     "Agent agreements (profit share).", "The calculation is ready (air per kg, FCL per container, LCL per m³).",
     "The agreement of each agent we use most, with minimum and maximum."),
]

wb = Workbook()
ws = wb.active
ws.title = "Missing tariffs"
navy = PatternFill("solid", fgColor="FF14324A")
gold = PatternFill("solid", fgColor="FF8A7A00")
yellow = PatternFill("solid", fgColor="FFFFF9C4")
white = Font(bold=True, color="FFFFFFFF")
top = Alignment(wrap_text=True, vertical="top")
ws["A1"] = "BOSS Odoo 20 · Supplier tariffs still missing (04/11/2026)"
ws["A1"].font = Font(bold=True, size=14)
ws["A2"] = ("Hi Cristina: these services are set up in the new Odoo but have no supplier price yet, so the operator types "
            "the cost by hand. Please send the documents (PDF or Excel) or a short answer, and fill in the yellow columns. "
            "Freight is not here: it changes every week and is entered from the quotation. Thanks, Belal")
ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
ws.merge_cells("A2:H2")
ws.row_dimensions[2].height = 45
headers = ["#", "Group", "Codes", "What is missing", "Already in Odoo", "What we need from you", "Sent?", "Your notes"]
for col, title in enumerate(headers, start=1):
    c = ws.cell(3, col, title)
    c.fill = gold if col >= 7 else navy
    c.font, c.alignment = white, Alignment(wrap_text=True, vertical="center")
for i, row in enumerate(ROWS, start=1):
    r = 3 + i
    for col, value in enumerate((i,) + row, start=1):
        ws.cell(r, col, value).alignment = top
    for col in (7, 8):
        ws.cell(r, col).fill = yellow
        ws.cell(r, col).alignment = top
last = 3 + len(ROWS)
dv = DataValidation(type="list", formula1='"Sent,Coming,Not needed"', allow_blank=True)
dv.add(f"G4:G{last}")
ws.add_data_validation(dv)
for col, width in zip("ABCDEFGH", (5, 24, 16, 40, 38, 46, 13, 36)):
    ws.column_dimensions[col].width = width
ws.freeze_panes = "D4"
ws.auto_filter.ref = f"A3:H{last}"
out = sys.argv[1] if len(sys.argv) > 1 else "docs/missing-tariffs-2026-11-04.xlsx"
wb.save(out)
print("saved", out, len(ROWS), "rows")
