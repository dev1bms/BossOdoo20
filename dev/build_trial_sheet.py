"""Build the step-by-step sheet of the full trial with Ángel and Cristina (roadmap item 13). Excel files stay out of
Git (.gitignore), so the sheet is built here and shared in the «NEW ODOO» folder. No prices and no customer names: the
[PRUEBA] files are named by number only.
    python dev/build_trial_sheet.py [output.xlsx]      # default: docs/prueba-completa.xlsx (ignored by Git)"""
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

STEPS = [
    # (scenario, who, step, where, expected)
    ("1 Quotation", "Ángel", "Create a sea import FCL quotation for a [PRUEBA] customer from the template «IMB FOB».",
     "Sales → Quotations → New; field Template", "Direction, mode, load type, incoterm and services come from the template."),
    ("1 Quotation", "Ángel", "Choose the origin port (e.g. Xingang) without choosing the country first.",
     "Quotation → tab Shipment", "The origin country fills itself (China)."),
    ("1 Quotation", "Ángel", "Look at the delivery address and the Spanish port.", "Quotation → tab Shipment",
     "Both are proposed (the customer's warehouse, the port of its last similar quotation); you can change them."),
    ("1 Quotation", "Ángel", "Type «MSC» in Main carrier.", "Quotation → tab Shipment",
     "The MSC group and its companies appear, no people."),
    ("1 Quotation", "Ángel", "Add the ETA and one 40' container.", "Quotation → tab Shipment",
     "THC and the other services get their cost and selling price; about 6 entries in total."),
    ("1 Quotation", "Ángel", "Open the ⓘ of a cost line.", "Quotation → Order lines",
     "It says which tariff, version and page gave the cost, and how the selling price was set."),
    ("1 Quotation", "Ángel", "Lower a selling price under the cost.", "Quotation → Order lines",
     "A yellow minimum-margin warning appears; nothing is blocked."),
    ("1 Quotation", "Ángel", "Confirm the quotation.", "Quotation → Confirm",
     "A shipment file E26xxxx opens, once."),
    ("2 WFS tariff", "Ángel", "Open the WFS tariff waiting for approval and approve it (or return it).",
     "Pricing & Suppliers → Tariffs and documents → filter «Waiting for approval»",
     "State Approved (or Draft); air imports with WFS now take its cost by themselves."),
    ("3 One file end to end", "Cristina", "Open E260181 and read the Next step line.", "Shipment files → E260181",
     "It says what is due now; «Go» does it or opens what is missing."),
    ("3 One file end to end", "Cristina", "Follow «Go» until the requests for quotation are confirmed.",
     "E260181 → Next step → Go", "One request per supplier and currency; confirmed with the supplier's reference."),
    ("3 One file end to end", "Cristina", "Put the file in transit without ATD or B/L.", "E260181 → In transit",
     "Accepted with a warning in the history listing what is missing."),
    ("3 One file end to end", "Cristina", "Type the ATA.", "E260181 → tab References and dates",
     "The file moves to «Arrived» by itself."),
    ("3 One file end to end", "Cristina", "Try «Delivered» before the discharge, customs release and delivery date.",
     "E260181 → Delivered", "Refused with the list of what is missing."),
    ("3 One file end to end", "Cristina", "Fill the Customs tab (DUA, channel, release) and copy the data for the broker.",
     "E260181 → tab Customs", "The text has parties, B/L, containers, goods, freight, THC, T3 and insurance; «Copy» works."),
    ("3 One file end to end", "Cristina", "Print the transport order.", "E260181 → Transport order",
     "PDF for the haulier without prices; refused while the house B/L is not released."),
    ("3 One file end to end", "Cristina", "Mark the file delivered.", "E260181 → Delivered",
     "State Delivered; the parties to rate appear in the Ratings tab."),
    ("3 One file end to end", "Ángel", "Invoice the services.", "E260181 → Invoice services",
     "Paid-on-behalf amounts (duties, import VAT) on a separate invoice; VAT per the BOSS table."),
    ("3 One file end to end", "Ángel", "Record the supplier bills and a payment.", "Purchase orders → Bill; Accounting",
     "Actual cost and margin on the Summary tab; variances to review are flagged."),
    ("3 One file end to end", "Cristina", "Press «Close operations» before rating.", "E260181 → Close operations",
     "Not closed: a notice says who is still to rate."),
    ("3 One file end to end", "Cristina", "Rate the customer and the suppliers (0-10) and close operations.",
     "E260181 → tab Ratings", "State Operations closed; the averages show on the contacts and in Services to buy."),
    ("3 One file end to end", "Cristina", "Try to change the vessel or the goods.", "E260181",
     "Read-only; reopening allows it again."),
    ("3 One file end to end", "Ángel", "Close financially and open the margin report.",
     "E260181 → Close financially; Shipment files → Margin by file", "The file appears with its final margin."),
    ("4 Air import", "Cristina", "Open E260182: handler, storage days and the house AWB draft.",
     "Shipment files → E260182; ⋮ → Print → House air waybill", "Handler proposed when one is known for the airline and airport; the AWB prints with DRAFT."),
    ("5 Sea export", "Cristina", "Print the house B/L draft of E260183, then issue it.",
     "E260183 → ⋮ → Print → House bill of lading; Issue HBL",
     "DRAFT first; issuing lists what is missing, then gives the number and the date."),
    ("6 Consolidation", "Cristina", "Open the master E260231 and its houses E260232 and E260233.",
     "Shipment files → E260231 → tab Houses", "Each house has its own customer, share of the costs and margin."),
    ("6 Consolidation", "Cristina", "Change «Shared costs split by» (weight, volume, equal parts).", "E260231",
     "The share and margin of each house change; the consolidated margin stays."),
    ("6 Consolidation", "Cristina", "Print the cargo manifest of the master and the house B/L of each house.",
     "E260231 → ⋮ → Print → Cargo manifest", "One line per house with totals; a warning if the agent abroad is empty."),
    ("7 Agent business", "Ángel", "Open E260184 (LCL for an agent) and invoice it.", "Shipment files → E260184",
     "The invoice goes to the agent (the orderer)."),
    ("8 My files", "Both", "Open Shipment files.", "Shipment files → Files",
     "Opens on «My files» and «In progress»; filters and the board by status work."),
]
QUESTIONS = [
    ("Ángel", "WFS tariff: approve or return it (point 38)."),
    ("Ángel", "Import demurrage: does it end at the pickup at the port or at the empty return? (point 17)"),
    ("Ángel", "From 01/01/2027: SII or VERI*FACTU?"),
    ("Ángel", "Payment terms of 75 and 90 days from Odoo 17: still used? (the law allows 60 days between companies)"),
    ("Ángel and Cristina", "DAP/DDP files: opened at acceptance or when the documents arrive?"),
    ("Cristina", "Storage (ALM): her e-mail of 25/09 or the clause in the quotations?"),
    ("Cristina", "Check the 7 quotation templates and their prices."),
]

wb = Workbook()
ws = wb.active
ws.title = "Trial steps"
navy = PatternFill("solid", fgColor="FF14324A")
gold = PatternFill("solid", fgColor="FF8A7A00")
yellow = PatternFill("solid", fgColor="FFFFF9C4")
white = Font(bold=True, color="FFFFFFFF")
top = Alignment(wrap_text=True, vertical="top")
ws["A1"] = "BOSS Odoo 20 · Full trial with Ángel and Cristina"
ws["A1"].font = Font(bold=True, size=14)
ws["A2"] = ("On https://system.bosscontinental.com with [PRUEBA] records: everything can be confirmed, invoiced and closed "
            "safely; nothing is sent outside. Guide: https://doc.bosscontinental.com/new/#/prueba. "
            "Please write your verdict and notes in the yellow columns (G, H).")
headers = ["#", "Scenario", "Who", "Step", "Where in Odoo", "Expected result", "Your verdict", "Your notes"]
for col, title in enumerate(headers, start=1):
    c = ws.cell(3, col, title)
    c.fill = gold if col >= 7 else navy
    c.font, c.alignment = white, Alignment(wrap_text=True, vertical="center")
for i, (scenario, who, step, where, expected) in enumerate(STEPS, start=1):
    row = 3 + i
    for col, value in enumerate((i, scenario, who, step, where, expected), start=1):
        ws.cell(row, col, value).alignment = top
    for col in (7, 8):
        ws.cell(row, col).fill = yellow
        ws.cell(row, col).alignment = top
last = 3 + len(STEPS)
dv = DataValidation(type="list", formula1='"OK,Not OK,To discuss"', allow_blank=True)
dv.add(f"G4:G{last}")
ws.add_data_validation(dv)
for col, width in zip("ABCDEFGH", (5, 20, 11, 50, 38, 50, 14, 40)):
    ws.column_dimensions[col].width = width
ws.freeze_panes = "D4"
ws.auto_filter.ref = f"A3:H{last}"

q = wb.create_sheet("Questions for the call")
q["A1"] = "Questions for the call"
q["A1"].font = Font(bold=True, size=14)
for col, title in enumerate(("#", "Who", "Question", "Answer"), start=1):
    c = q.cell(3, col, title)
    c.fill = gold if col == 4 else navy
    c.font = white
for i, (who, question) in enumerate(QUESTIONS, start=1):
    q.cell(3 + i, 1, i).alignment = top
    q.cell(3 + i, 2, who).alignment = top
    q.cell(3 + i, 3, question).alignment = top
    q.cell(3 + i, 4).fill = yellow
for col, width in zip("ABCD", (5, 20, 80, 50)):
    q.column_dimensions[col].width = width
wb.save(sys.argv[1] if len(sys.argv) > 1 else "docs/prueba-completa.xlsx")
print("steps", len(STEPS), "questions", len(QUESTIONS))
