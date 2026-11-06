"""Leroy Merlin flow (go-live tracker P4-10) on boss20, inside a transaction rolled back. A periodic-invoice customer
with several delivery warehouses: one contract quotation for three shipments is accepted and split into three files
with «Move services to another file» (quantities move, never duplicate: owner decision 26/08/2026, P34), each file with
its warehouse; the first shipment is operated to delivery; the three files are invoiced together on one invoice with
a section per file (F0-C59); the first file closes operationally and financially (acceptance criterion of P4-10).
    dev/uat_run.sh check_leroy_flow.py boss20"""
from datetime import date, datetime

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def outcome(fn):
    try:
        with env.cr.savepoint():
            fn()
    except (UserError, ValidationError, AccessError) as e:
        print(f"      refused: {' '.join(str(e).split())[:200]}")
        return "refused"
    return "allowed"


ref = env.ref
Partner, File = env["res.partner"], env["boss.expediente"]
company = env.company
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
line_of = lambda o, code: o.order_line.filtered(lambda l: l.product_id.default_code == code)  # noqa: E731
state = lambda code: env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", code)], limit=1)  # noqa: E731
es = ref("base.es").id
customer = Partner.create({"name": "[PRUEBA] Leroy Merlin España (cliente periódico)", "is_company": True,
                           "vat": "ESB12345674", "country_id": es, "city": "Alcobendas", "state_id": state("M").id,
                           "boss_invoice_grouping": "grouped"})
torija = Partner.create({"name": "[PRUEBA] Almacén Torija", "parent_id": customer.id, "type": "delivery",
                         "city": "Torija", "state_id": state("GU").id, "country_id": es})
ribarroja = Partner.create({"name": "[PRUEBA] Centro logístico Ribarroja", "parent_id": customer.id, "type": "delivery",
                            "city": "Ribarroja de Turia", "state_id": state("V").id, "country_id": es})
other = Partner.create({"name": "[PRUEBA] Otro cliente", "is_company": True, "vat": "ESB12345674", "country_id": es,
                        "city": "Madrid", "state_id": state("M").id})
carrier = Partner.create({"name": "[PRUEBA] Naviera Leroy", "is_company": True, "country_id": es, "city": "Valencia"})
broker = Partner.create({"name": "[PRUEBA] Agente de aduanas Leroy", "is_company": True, "country_id": es, "city": "Valencia"})
haulier = Partner.create({"name": "[PRUEBA] Transportista Leroy", "is_company": True, "country_id": es, "city": "Valencia"})
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                                         ("company_id", "=", company.id)], limit=1)
fob = env["account.incoterms"].search([("code", "=", "FOB")], limit=1)
dv = ref("boss_pricing.container_type_dv")
check("0 the customer is a periodic-invoice customer with two delivery warehouses (F0-C59)", ("grouped", 2),
      (customer.boss_invoice_grouping, len(customer.child_ids.filtered(lambda c: c.type == "delivery"))))

# ---- 1. one contract quotation for three shipments, accepted ---------------------------------------------------------------
PRICES = {"FMI": 1000.0, "THC": 150.0, "FAD": 120.0, "TTE-FCL": 200.0}  # per shipment fees (CSM) are not part of a contract
SUPPLIERS = {"THC": carrier, "FAD": broker, "TTE-FCL": haulier}  # asked case by case; the freight has an offer
order = env["sale.order"].create({
    "partner_id": customer.id, "partner_shipping_id": torija.id, "client_order_ref": "[PRUEBA] LM-2026-11",
    "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl", "incoterm": fob.id,
    "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id,
    "boss_destination_port_id": port("ESVLC", "sea").id, "boss_delivery_address_id": torija.id,
    "boss_scope_main": True, "boss_scope_destination_customs": True, "boss_scope_delivery": True,
    "boss_etd": date(2026, 11, 25), "boss_eta": date(2026, 12, 28),
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": dv.id, "quantity": 3})],
    "order_line": [Command.create({"product_id": product(c).id, "product_uom_id": product(c).uom_id.id,
                                   "product_uom_qty": 3.0}) for c in PRICES]})
for code, supplier in SUPPLIERS.items():
    line_of(order, code).write({"boss_supplier_id": supplier.id, "boss_cost_on_request": True})
line_of(order, "FMI").write({"boss_supplier_id": carrier.id, "boss_manual_cost": 800.0,
                             "boss_manual_cost_note": "[PRUEBA] oferta de flete de la naviera para el contrato"})
order.action_boss_update_costs()
for code, price in PRICES.items():
    line_of(order, code).price_unit = price
for l in order.order_line:
    print(f"      {l.product_id.default_code:8} qty {l.product_uom_qty:g} sale {l.price_unit:8.2f} cost {l.boss_cost_status} vat {l.boss_vat_status}")
check("1 the contract quotation holds three shipments: every service x3, 3 containers", ([3.0] * 4, 3),
      (order.order_line.mapped("product_uom_qty"), sum(order.boss_container_ids.mapped("quantity"))))
order.action_confirm()
file1 = order.boss_expediente_id
check("1 accepted: one file with the whole agreement, the three containers and the first warehouse",
      ("IMB", [3.0] * 4, 3, torija.id),
      (file1.traffic_code, file1.allocation_ids.sorted("id").mapped("quantity"), len(file1.container_ids),
       file1.delivery_address_id.id))

# ---- 2. the agreement is split into three files (one per shipment), each with its warehouse ------------------------------
Split = env["boss.expediente.split"]


def move_one_shipment(source, quantity=1.0):
    wizard = Split.with_context(default_expediente_id=source.id).create({})  # as the «Actions» menu opens it
    wizard.line_ids.write({"quantity": quantity})
    return File.browse(wizard.action_split()["res_id"])


check("2 moving more than the file holds is refused", "refused", outcome(lambda: move_one_shipment(file1, 5.0)))
file2 = move_one_shipment(file1)
file3 = move_one_shipment(file1)
file1.container_ids[1:].unlink()  # the operator keeps one container per file
for file, warehouse in ((file2, ribarroja), (file3, torija)):
    file.write({"delivery_address_id": warehouse.id,
                "container_ids": [Command.create({"size": "40", "container_type_id": dv.id})]})
env.invalidate_all()
files = file1 | file2 | file3
check("2 three files of the same customer, each with one shipment of every service (quantities moved, never duplicated)",
      [(1.0,) * 4] * 3, [tuple(f.allocation_ids.sorted("id").mapped("quantity")) for f in files])
check("2 the accepted totals are unchanged on the quotation", [3.0] * 4, order.order_line.mapped("product_uom_qty"))
check("2 each file sells one third of the agreement", [1470.0] * 3, [round(f.sudo().amount_sale, 2) for f in files])
check("2 each file has its own warehouse and container", [(torija.id, 1), (ribarroja.id, 1), (torija.id, 1)],
      [(f.delivery_address_id.id, len(f.container_ids)) for f in files])
check("2 each file buys its own shipment: 4 needs of quantity 1", [[1.0] * 4] * 3,
      [f.cost_ids.mapped("quantity") for f in files])
print(f"      next step of the second shipment: {file2.next_step} · {file2.next_step_detail}")

# ---- 3. the first shipment is bought and operated to delivery --------------------------------------------------------------
for code, cost in (("FMI", 800.0), ("THC", 100.0), ("FAD", 80.0), ("TTE-FCL", 150.0)):
    file1.cost_ids.filtered(lambda n, c=code: n.product_id.default_code == c).write({"expected_unit_cost": cost})
file1.action_create_rfqs()
pos = file1.purchase_order_ids
check("3 RFQs of the first shipment only: carrier, customs broker, haulier", {carrier.id, broker.id, haulier.id},
      set(pos.partner_id.ids))
check("3 the other shipments have nothing ordered", [0, 0], [len(f.purchase_order_ids) for f in file2 | file3])
for po in pos:
    po.partner_ref = f"[PRUEBA] conf. {po.partner_id.name[-8:]}"
    po.button_confirm()
file1.cost_ids.filtered("purchase_line_ids").action_mark_performed()
file1.write({"booking_ref": "[PRUEBA] BK-LM-1", "mbl_ref": "[PRUEBA] MBL-LM-1", "hbl_ref": "[PRUEBA] HBL-LM-1",
             "vessel": "[PRUEBA] BUQUE", "voyage": "002W", "haulier_id": haulier.id, "atd": datetime(2026, 11, 25, 18, 0)})
file1.container_ids.write({"number": "PRUU1234565", "seal": "SEAL-LM-1"})
file1.action_in_transit()
file1.write({"ata": datetime(2026, 12, 28, 6, 0), "discharge_date": datetime(2026, 12, 28, 14, 0),
             "customs_ref": "[PRUEBA] 26ES00460010000003", "customs_guarantee": "boss",
             "customs_admission_date": datetime(2026, 12, 29, 9, 0), "customs_channel": "green",
             "customs_release_date": datetime(2026, 12, 29, 12, 0), "hbl_release": "released",
             "delivery_date": datetime(2026, 12, 30, 11, 0)})
file1.container_ids.write({"pickup_date": date(2026, 12, 30), "return_date": date(2027, 1, 4)})
file1.action_delivered()
check("3 the first shipment is delivered at its warehouse", ("delivered", torija.id), (file1.state, file1.delivery_address_id.id))

# ---- 4. the three files on one invoice, a section per file (F0-C59) -------------------------------------------------------
stray = File.create({"partner_id": other.id, "direction": "import", "transport_mode": "sea", "load_type": "fcl",
                     "scope_main": True})
check("4 files of different customers cannot be invoiced together", "refused",
      outcome(lambda: (file1 | stray).action_invoice_together()))
bindings = env["ir.actions.actions"].get_bindings("boss.expediente")["action"]
check("4 «Invoice files together» is an action of the list of files", True,
      any(b["name"] == "Invoice files together" for b in bindings if b.get("binding_view_types") == "list"))
action = files.action_invoice_together()
invoice = env["account.move"].browse(action["res_id"])
products = invoice.invoice_line_ids.filtered(lambda l: l.display_type == "product")
sections = invoice.invoice_line_ids.filtered(lambda l: l.display_type == "line_section").sorted("sequence")
check("4 one invoice to the customer with the 12 services of the three files and a section per file",
      (customer.id, 12, 3), (invoice.partner_id.commercial_partner_id.id, len(products), len(sections)))
check("4 the sections name each file, its customer reference, route and container",
      [f.name for f in files.sorted("name")], [s.name.split(" · ")[0] for s in sections])
print("      sections:", [s.name for s in sections])
check("4 every line carries its file and its file's analytic account, with the quantity of that file",
      {(f.id, 4, True) for f in files},
      {(f.id, len(products.filtered(lambda l, f=f: l.boss_expediente_id == f)),
        all(l.quantity == 1.0 and str(f.analytic_account_id.id) in ",".join((l.analytic_distribution or {}).keys())
            for l in products.filtered(lambda l, f=f: l.boss_expediente_id == f))) for f in files})
check("4 the lines of each file follow its section", True,
      all(sec.sequence < l.sequence < sec.sequence + 100 for sec in sections
          for l in products.filtered(lambda l, s=sec: l.boss_expediente_id.name == s.name.split(" · ")[0])))
env.invalidate_all()
check("4 nothing left to invoice on the three files; the invoice is on each of them", ([0.0] * 3, [True] * 3),
      ([round(f.sudo().amount_to_invoice, 2) for f in files], [invoice in f.invoice_ids for f in files]))
check("4 a mixed invoice prints no shipment block of its own (ADR-011: the sections identify the files)", 0,
      len(invoice._boss_document_file()))
invoice.invoice_date = date(2026, 12, 31)
invoice.action_post()
check("4 the grouped invoice is posted", "posted", invoice.state)
check("4 invoicing again finds nothing", "refused", outcome(lambda: files.action_invoice_together()))

# ---- 5. supplier bills of the first shipment, then its two closes ----------------------------------------------------------
for po in pos:
    po.action_create_invoice()
    bill = po.invoice_ids.filtered(lambda m: m.state == "draft")[:1]
    bill.write({"invoice_date": date(2027, 1, 5), "ref": f"[PRUEBA] factura {po.partner_id.name[-8:]}"})
    bill.invoice_line_ids.tax_ids = purchase_0
    bill.action_post()
check("5 every need of the first shipment is billed", ["billed"] * 4, file1.cost_ids.mapped("state"))
file1.action_close_operations()  # first: the parties to rate
file1.rating_ids.write({"rating": "8"})
file1.action_close_operations()
check("5 operations of the first shipment closed", "closed", file1.state)
env.invalidate_all()
check("5 nothing left to review on it", False, bool(file1.completeness))
file1.action_close_financial()
check("5 the first Leroy file is closed financially (acceptance criterion of P4-10)", True, file1.financial_closed)
row = env["boss.margin.report"].search([("expediente_id", "=", file1.id)])
check("5 «Margin by file» keeps its final margin: one third of the agreement less its own costs", (1, 340.0),
      (len(row), round(row.amount_margin_final, 2)))
check("5 the other two shipments stay open, invoiced, with their services still to buy", [("open", 0.0, 4)] * 2,
      [(f.state, round(f.sudo().amount_to_invoice, 2), len(f.cost_ids.filtered(lambda n: n.state == "to_order")))
       for f in file2 | file3])
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if not all(results):
    raise SystemExit(1)
