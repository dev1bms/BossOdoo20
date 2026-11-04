"""Check of roadmap item 19 (boss20, rolled back): an issued house document does not change (its PDF is kept at issue and
every reprint gives it; a correction is a new issue with its reason), the B/L prints the clauses of the Odoo 17 B/L and
an attached sheet for text that does not fit its box, and the issued air waybill is the IATA set of Odoo 17 (three
originals and seven copies, with the conditions of contract). [PRUEBA] records only.
    dev/uat_run.sh check_house_doc_lock.py boss20"""
import io
from datetime import date

from odoo import Command
from odoo.tools.pdf import PdfReader

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


Report = env["ir.actions.report"]
html = lambda report, record: Report._render_qweb_html(f"boss_documents.{report}", record.ids)[0].decode()  # noqa: E731
port = lambda code, kind="sea": env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
Partner, File = env["res.partner"], env["boss.expediente"]
company = lambda name, country: Partner.create({  # noqa: E731
    "name": name, "is_company": True, "country_id": ref(f"base.{country}").id, "street": "[PRUEBA] Calle 1",
    "city": "[PRUEBA] Ciudad"})
shipper, buyer, other = (company("[PRUEBA] Bloqueo Exportador", "es"), company("[PRUEBA] Bloqueo Comprador", "au"),
                         company("[PRUEBA] Bloqueo Otro Destinatario", "au"))
sea = File.create({
    "partner_id": shipper.id, "business": "boss", "direction": "export", "transport_mode": "sea", "load_type": "lcl",
    "origin_country_id": ref("base.es").id, "origin_port_id": port("ESVLC").id,
    "destination_country_id": ref("base.au").id, "destination_port_id": port("AUSYD").id,
    "etd": date(2026, 11, 20), "shipper_id": shipper.id, "consignee_id": buyer.id, "vessel": "[PRUEBA] VESSEL",
    "packages": 10, "gross_kg": 1000.0, "volume_m3": 5.0, "goods_description": "[PRUEBA] FURNITURE",
    "house_doc_freight": "prepaid"})
attachments = lambda f: env["ir.attachment"].search(  # noqa: E731
    [("res_model", "=", "boss.expediente"), ("res_id", "=", f.id), ("name", "=like", "HBL %")], order="id")

# 1. issue: the PDF is kept
sea.action_issue_house_document()
kept = attachments(sea)
check("1 issuing keeps its PDF on the file (issue 1)", (1, f"HBL {sea.name} - issue 1.pdf"), (len(kept), kept[:1].name))
# 2. data changed after the issue: a reprint gives the issued copy
sea.consignee_id = other
pdf, _type = Report._render_qweb_pdf("boss_documents.action_report_house_bl", sea.ids)
text = " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf)).pages).upper()
check("2 after changing the consignee, a reprint gives the issued copy (old consignee), nothing new is kept",
      (True, False, 1), ("BLOQUEO COMPRADOR" in text, "BLOQUEO OTRO DESTINATARIO" in text, len(attachments(sea))))
# 3. a correction is a new issue with its reason
env["boss.house.doc.reissue"].create({"expediente_id": sea.id, "reason": "[PRUEBA] destinatario corregido"}) \
    .action_confirm()
check("3 re-issue: issue 2 kept beside issue 1, the reason in the history", (2, 2, True),
      (sea.house_doc_issue_count, len(attachments(sea)),
       any("destinatario corregido" in (m.body or "") for m in sea.message_ids)))

# 4. clauses and attached sheet of the B/L
sea_html = html("report_house_bl", sea)
check("4 the B/L prints the Odoo 17 clause and excess value declaration", (True, True),
      ("RECEIVED by the Carrier" in sea_html, "EXCESS VALUE DECLARATION REFER TO CLAUSE 6(4)" in sea_html))
long_text = "\n".join(f"[PRUEBA] LINE {i} OF A LONG DESCRIPTION OF GOODS" for i in range(30))
draft = File.create(dict(sea.copy_data()[0], goods_description=long_text, house_doc_freight="prepaid"))
draft_html = html("report_house_bl", draft)
check("5 a description that does not fit its box goes to an attached sheet", (True, True, True),
      ("AS PER ATTACHED SHEET" in draft_html, "ATTACHED SHEET" in draft_html, "LINE 29 OF A LONG" in draft_html))

# 5. the air waybill: IATA set when issued, one page as a draft
air_master = File.create({"partner_id": shipper.id, "business": "boss", "direction": "export", "transport_mode": "air",
                          "load_type": "air", "origin_port_id": port("MAD", "air").id,
                          "destination_port_id": port("SYD", "air").id, "mawb_ref": "[PRUEBA] 157-12345675",
                          "vessel": "[PRUEBA] QR148"})
air = File.create({"partner_id": shipper.id, "business": "boss", "direction": "export", "transport_mode": "air",
                   "load_type": "air", "master_id": air_master.id, "shipper_id": shipper.id, "consignee_id": buyer.id,
                   "origin_port_id": port("MAD", "air").id, "destination_port_id": port("SYD", "air").id,
                   "packages": 3, "gross_kg": 150.0, "goods_description": "[PRUEBA] SPARE PARTS",
                   "house_doc_freight": "collect"})
env.invalidate_all()
air_draft = html("report_house_awb", air)
check("6 a draft air waybill is one front page, no copies and no conditions", (True, False, False),
      ("DRAFT" in air_draft, "ORIGINAL 1" in air_draft, "CONDITIONS OF CONTRACT</strong>" in air_draft))
air.action_issue_house_document()
air_html = html("report_house_awb", air)
check("7 the issued air waybill: three originals and seven copies, each with its conditions of contract",
      (True, True, True, 10, 10),
      ("ORIGINAL 1 (FOR ISSUING CARRIER)" in air_html, "ORIGINAL 3 (FOR SHIPPER)" in air_html,
       "COPY 10 (EXTRA COPY FOR CARRIER)" in air_html, air_html.count("CONDITIONS OF CONTRACT</strong>"),
       air_html.count("Shipper certifies that the particulars")))
check("8 the air waybill keeps its PDF too", 1, env["ir.attachment"].search_count(
    [("res_model", "=", "boss.expediente"), ("res_id", "=", air.id), ("name", "=like", "HAWB %")]))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
