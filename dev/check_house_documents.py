"""Check of roadmap item 11 (boss20, rolled back): the house documents BOSS issues as NVOCC (F0-C45, ADR-014). A sea
export consolidation of [PRUEBA] parties (a master B/L with two houses) prints a house B/L per house and the cargo
manifest of the master; an air house prints its house air waybill. Prints «CHECK PASS|FAIL …» and «RESULT …».
    dev/uat_run.sh check_house_documents.py boss20"""
from datetime import date

from odoo import Command, fields
from odoo.exceptions import UserError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def refused(name, fn, words=()):
    try:
        with env.cr.savepoint():
            fn()
        got, message = "accepted", ""
    except UserError as exc:
        got, message = "refused", str(exc)
        print(f"      «{' '.join(message.split())[:200]}»")
    check(name, ("refused", True), (got, all(w in message for w in words)))


def html(report, record, lang="en_US"):
    return env["ir.actions.report"].with_context(lang=lang)._render_qweb_html(
        f"boss_documents.{report}", record.ids)[0].decode()


port = lambda code, kind="sea": env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
incoterm = lambda code: env["account.incoterms"].search([("code", "=", code)], limit=1)  # noqa: E731
Partner, File = env["res.partner"], env["boss.expediente"]
company = lambda name, country: Partner.create({  # noqa: E731
    "name": name, "is_company": True, "country_id": ref(f"base.{country}").id, "street": "[PRUEBA] Calle 1",
    "city": "[PRUEBA] Ciudad", "vat": "ESB12345674" if country == "es" else False})
exporter_a = company("[PRUEBA] HBL Exportador A", "es")
exporter_b = company("[PRUEBA] HBL Exportador B", "es")
buyer_a = company("[PRUEBA] HBL Comprador A", "au")
buyer_b = company("[PRUEBA] HBL Comprador B", "au")
agent = company("[PRUEBA] HBL Agente Sydney", "au")
carrier = company("[PRUEBA] HBL Naviera", "es")

route = {"business": "boss", "direction": "export", "transport_mode": "sea", "carrier_id": carrier.id,
         "origin_country_id": ref("base.es").id, "origin_port_id": port("ESVLC").id,
         "destination_country_id": ref("base.au").id, "destination_port_id": port("AUSYD").id,
         "etd": date(2026, 11, 20), "eta": date(2027, 1, 5)}
master = File.create(dict(route, partner_id=exporter_a.id, load_type="fcl", mbl_ref="[PRUEBA] MBL-HBL-1",
                          vessel="[PRUEBA] VESSEL", voyage="012W",
                          container_ids=[Command.create({"size": "40", "number": "MSCU1234565", "seal": "S-77",
                                                         "container_type_id": ref("boss_pricing.container_type_hc").id})]))
house_a = File.create(dict(route, partner_id=exporter_a.id, load_type="lcl", master_id=master.id,
                           shipper_id=exporter_a.id, consignee_id=buyer_a.id, incoterm_id=incoterm("FOB").id,
                           packages=10, package_type="PL", gross_kg=4000.0, volume_m3=12.0,
                           goods_description="[PRUEBA] FURNITURE", hs_code="940360", origin_place="Paterna"))
house_b = File.create(dict(route, partner_id=exporter_b.id, load_type="lcl", master_id=master.id,
                           shipper_id=exporter_b.id, consignee_id=buyer_b.id, incoterm_id=incoterm("CIF").id,
                           gross_kg=2500.0, volume_m3=8.0, goods_description="[PRUEBA] TILES"))
env.invalidate_all()

# 1. which document each file has
check("1 house document: none on the master, a house B/L on each sea house", (False, "hbl", "hbl"),
      (master._boss_house_doc_kind(), house_a._boss_house_doc_kind(), house_b._boss_house_doc_kind()))
check("2 freight proposed from the incoterm: FOB collect, CIF prepaid", ("collect", "prepaid"),
      (house_a.house_doc_freight, house_b.house_doc_freight))
check("3 the houses carry the master's vessel and voyage (ADR-013)", ("[PRUEBA] VESSEL", "012W"),
      (house_a.vessel, house_a.voyage))

# 2. draft, then issue
draft = html("report_house_bl", house_a)
check("4 before issuing, the house B/L prints as a DRAFT with the boxes of Odoo 17",
      (True, True, True, True), ("DRAFT" in draft, "INTERNATIONAL BILL OF LADING" in draft,
                                 "[PRUEBA] HBL EXPORTADOR A" in draft, "SAME AS CONSIGNEE" in draft))
refused("5 house B and its missing data: issuing is refused and says what is missing",
        house_b.action_issue_house_document, words=("number of packages",))
action = house_a.action_issue_house_document()
check("6 issuing gives the B/L the file's number and today's date, and prints it",
      (house_a.name, fields.Date.context_today(house_a), "ir.actions.report"),
      (house_a.hbl_ref, house_a.house_doc_issue_date, action["type"]))
issued = html("report_house_bl", house_a)
check("7 the issued B/L: no DRAFT, its number, the master's container and seal, freight payable at destination",
      (False, True, True, True), ("DRAFT" in issued, house_a.name in issued,
                                  "MSCU1234565" in issued and "S-77" in issued, "DESTINATION" in issued))
issued_es = html("report_house_bl", house_a, lang="es_ES")
check("8 printed by a Spanish user, the B/L stays in English (an international document)", True,
      "INTERNATIONAL BILL OF LADING" in issued_es and "FREIGHT PAYABLE AT" in issued_es.upper())

# 3. the cargo manifest of the master
refused("9 no cargo manifest without the agent abroad (Odoo 17 action 1543)", master.action_print_cargo_manifest,
        words=("agent",))
master.agent_id = agent
manifest = html("report_cargo_manifest", master)
check("10 the manifest lists both houses with their shipper and consignee, and the totals",
      (True, True, True, True, True),
      ("CARGO MANIFEST" in manifest, house_a.name in manifest and house_b.name in manifest,
       "[PRUEBA] HBL COMPRADOR B" in manifest, "6500.00" in manifest, "HBLs: 2" in manifest))

# 4. an air house: its house air waybill
air_master = File.create(dict(route, partner_id=exporter_a.id, transport_mode="air", load_type="air",
                              origin_port_id=port("MAD", "air").id, destination_port_id=port("SYD", "air").id,
                              mawb_ref="[PRUEBA] 157-12345675", vessel="[PRUEBA] QR148"))
air_house = File.create(dict(route, partner_id=exporter_a.id, transport_mode="air", load_type="air",
                             master_id=air_master.id, shipper_id=exporter_a.id, consignee_id=buyer_a.id,
                             incoterm_id=incoterm("FCA").id, packages=3, gross_kg=150.0, volume_m3=1.2,
                             goods_description="[PRUEBA] SPARE PARTS"))
env.invalidate_all()
air_house.action_issue_house_document()
awb = html("report_house_awb", air_house)
check("11 an air house issues its house air waybill under the master's number",
      ("hawb", air_house.name, True, True), (air_house._boss_house_doc_kind(), air_house.hawb_ref,
                                             "[PRUEBA] 157-12345675" in awb, "200.40" in awb))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
