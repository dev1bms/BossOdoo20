"""BOSS documents (ADR-011). Two modes, nothing committed:
  * WIP (module not installed, dev/server_shell_wip.sh): the four QWeb files are loaded in the transaction (the
    xpaths must match Odoo 20), the shipment-block builder is exercised on real records and the block template
    rendered.
  * installed (dev/uat_run.sh check_documents.py boss20): in addition, a [PRUEBA] file with vessel, B/L, container
    number and cargo is created in the transaction, its quotation, invoice and purchase order are rendered as HTML
    and as PDF (the PDFs are printed base64 between PDF-BEGIN/PDF-END markers for a visual check), and the company
    layout is checked.
Everything is rolled back at the end."""
import base64
import os
from datetime import date

assert env.cr.dbname == "boss20"  # noqa: F821
env = env(context=dict(env.context, lang="en_US"))  # noqa: F821  labels compared in English
results = []


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


installed = env["ir.module.module"].search_count([("name", "=", "boss_documents"), ("state", "=", "installed")]) == 1  # noqa: F821
print("MODE", "installed" if installed else "wip")

if not installed:
    from odoo.tools import convert_file
    path = "/mnt/wip-addons/boss_documents"
    for filename in ("shipment_block_templates.xml", "invoice_templates.xml", "sale_templates.xml", "purchase_templates.xml"):
        convert_file(env, "boss_documents", f"report/{filename}", {}, mode="init", pathname=os.path.join(path, "report", filename))  # noqa: F821
    env.flush_all()  # noqa: F821
    ns = {}
    with open(os.path.join(path, "models", "shipment_block.py"), encoding="utf-8") as fp:
        exec(compile(fp.read(), "shipment_block.py", "exec"), ns)
    shipment_rows, scope_sentence = ns["shipment_rows"], ns["scope_sentence"]

    def block_of_file(f):
        order = f.sale_order_ids.filtered(lambda o: o.state == "sale")[:1] or f.sale_order_ids[:1]
        return {"reference": f.name, "customer_reference": order.client_order_ref or "", "quotation": order.name or "",
                "scope": scope_sentence(f), "columns": shipment_rows(f, "", file=f)}

    def block_of_order(o):
        if not (o.boss_transport_mode or o.boss_direction or o.boss_origin_country_id or o.boss_destination_country_id):
            return None
        return {"reference": "", "customer_reference": o.client_order_ref or "", "quotation": "",
                "scope": scope_sentence(o, "boss_"), "columns": shipment_rows(o, "boss_")}
else:
    def block_of_file(f):
        return f._boss_document_block()

    def block_of_order(o):
        return o._boss_document_block()

View = env["ir.ui.view"]  # noqa: F821
for key in ("account.report_invoice_document", "sale.report_saleorder_document", "purchase.report_purchaseorder_document"):
    arch = View._get_combined_arch_for_xmlid(key) if hasattr(View, "_get_combined_arch_for_xmlid") else env.ref(key)._get_combined_arch()  # noqa: F821
    from lxml import etree
    text = etree.tostring(arch, encoding="unicode") if not isinstance(arch, str) else arch
    check(f"1 {key}: shipment block inserted, charge base no longer behind the units group",
          (True, False), ("boss_documents.shipment_block" in text, 'groups="uom.group_uom"' in text))

# ---- builder on real records
f38 = env["boss.expediente"].browse(38)  # noqa: F821  [PRUEBA] E260038, S00162
b = block_of_file(f38)
cols = b["columns"]
labels = {label for col in cols.values() for label, _v in col}
check("2 file block: reference, quotation, route from/to, traffic, incoterm, ETA, containers",
      ("E260038", "S00162", True, True, True, True, True),
      (b["reference"], b["quotation"], "From" in labels and "To" in labels, "Traffic" in labels, "Incoterm" in labels,
       "ETA" in labels, any(v.startswith("1 × 40' DV") for _l, v in cols["cargo"])))
values = " ".join(v for col in cols.values() for _l, v in col)
check("2b file block: Shanghái and Valencia named with their codes; no amounts", (True, True, False),
      ("Shanghái (CNSHA)" in values, "Valencia (ESVLC)" in values, "€" in values))
so_rate = env["sale.order"].search([("boss_rate_quotation", "=", True), ("partner_id.name", "like", "[PRUEBA]")], order="id desc", limit=1)  # noqa: F821
br = block_of_order(so_rate)
check("3 rate quotation block: route without containers (alternatives are lines), no file",
      (True, "", False), (bool(br and br["columns"]["route"]), br["reference"], any(l == "Containers" for l, _v in br["columns"]["cargo"])))
plain = env["sale.order"].search([("boss_transport_mode", "=", False), ("boss_direction", "=", False), ("boss_origin_country_id", "=", False), ("boss_destination_country_id", "=", False)], limit=1)  # noqa: F821
if plain:
    check("4 an order without shipment data prints no block", None, block_of_order(plain))
html = str(env["ir.qweb"]._render("boss_documents.shipment_block", {"block": b, "for_supplier": False}))  # noqa: F821
check("5 block template: file, quotation, three columns, scope line; supplier variant hides the customer side",
      (True, True, True, True), ("E260038" in html, "S00162" in html, html.count("col-4") == 3, "Services of BOSS" in html))
html_sup = str(env["ir.qweb"]._render("boss_documents.shipment_block", {"block": b, "for_supplier": True}))  # noqa: F821
check("5b supplier variant: no quotation, no customer reference, no scope", (False, False), ("S00162" in html_sup, "Services of BOSS" in html_sup))

if installed:
    company = env.company  # noqa: F821
    check("6 company layout: Light template, striped tables, BOSS colours, Lato, footer with the contact data",
          ("web.external_layout_standard", "striped", "#64a8af", "#003a5c", "Lato", True),
          (company.external_report_layout_id.key, company.report_tables_id, company.primary_color, company.secondary_color,
           company.font, "boss@bosscontinental.com" in (company.report_footer or "")))
    # ---- a complete [PRUEBA] file in the transaction
    so = env["sale.order"].browse(162)  # noqa: F821  S00162 → E260038
    f38.write({"vessel": "MSC ISABELLA", "voyage": "FI642A", "mbl_ref": "MEDUSH123456", "hbl_ref": "BOSS26SH0042",
               "booking_ref": "BK7788", "atd": date(2026, 10, 20), "packages": 480, "package_type": "CT",
               "gross_kg": 9850, "volume_m3": 58.4, "goods_description": "[PRUEBA] Children's books",
               "hs_code": "4901.99"})
    f38.container_ids.write({"number": "MSCU1234567", "seal": "S998877"})
    so.write({"client_order_ref": "PO-[PRUEBA]-2026-77"})
    Report = env["ir.actions.report"]  # noqa: F821
    outputs = {}
    html_so = Report._render_qweb_html("sale.action_report_saleorder", [so.id])[0].decode()
    check("7 quotation HTML: block with file, vessel, B/L, container number, customer reference; no shipping-address duplicate; units printed",
          (True, True, True, True, True, False, True),
          ("E260038" in html_so, "MSC ISABELLA" in html_so, "MEDUSH123456 / BOSS26SH0042" in html_so, "MSCU1234567" in html_so,
           "PO-[PRUEBA]-2026-77" in html_so, "Shipping Address" in html_so, "Container" in html_so))
    outputs["quotation"] = Report._render_qweb_pdf("sale.action_report_saleorder", [so.id])[0]
    # invoice of the file
    wiz = env["sale.advance.payment.inv"].with_context(active_model="sale.order", active_ids=so.ids).create({"advance_payment_method": "delivered"})  # noqa: F821
    invoices = so.invoice_ids
    if not invoices:
        try:
            wiz.create_invoices()
        except Exception as exc:  # noqa: BLE001
            print("INFO create_invoices refused:", exc)
    invoice = so.invoice_ids[:1]
    if invoice:
        invoice.write({"ref": "PO-[PRUEBA]-2026-77"})
        html_inv = Report._render_qweb_html("account.account_invoices", [invoice.id])[0].decode()
        check("8 invoice HTML: block with file and quotation, vessel, container, reference; «Source» column replaced; units printed; no cost field",
              (True, True, True, True, False, True, False),
              ("E260038" in html_inv, "S00162" in html_inv, "MSC ISABELLA" in html_inv, "MSCU1234567" in html_inv,
               ">Source<" in html_inv, "Container" in html_inv, "boss_cost" in html_inv))
        outputs["invoice"] = Report._render_qweb_pdf("account.account_invoices", [invoice.id])[0]
    else:
        print("INFO no invoice could be created for S00162 in this transaction")
    po = env["purchase.order"].search([("boss_expediente_id", "=", f38.id)], limit=1)  # noqa: F821
    if not po:
        supplier = env["res.partner"].search([("name", "like", "[PRUEBA]"), ("supplier_rank", ">", 0)], limit=1) or env["res.partner"].create({"name": "[PRUEBA] Naviera documentos", "is_company": True, "supplier_rank": 1})  # noqa: F821
        product = env["product.product"].search([("default_code", "=", "THC")], limit=1)  # noqa: F821
        po = env["purchase.order"].create({"partner_id": supplier.id, "order_line": [(0, 0, {  # noqa: F821
            "product_id": product.id, "name": "THC [PRUEBA]", "product_qty": 1, "price_unit": 1.0})], "boss_expediente_id": f38.id})
    html_po = Report._render_qweb_html("purchase.action_report_purchase_order", [po.id])[0].decode()
    check("9 purchase order HTML: block with file, vessel, container; no customer reference, no quotation, no scope line",
          (True, True, True, False, False, False),
          ("E260038" in html_po, "MSC ISABELLA" in html_po, "MSCU1234567" in html_po, "PO-[PRUEBA]-2026-77" in html_po,
           "S00162" in html_po, "Services of BOSS" in html_po))
    outputs["purchase"] = Report._render_qweb_pdf("purchase.action_report_purchase_order", [po.id])[0]
    for name, pdf in outputs.items():
        check(f"10 {name} PDF rendered", True, pdf[:4] == b"%PDF" and len(pdf) > 10000)
        print(f"PDF-BEGIN {name} {len(pdf)}")
        print(base64.b64encode(pdf).decode())
        print(f"PDF-END {name}")

print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
