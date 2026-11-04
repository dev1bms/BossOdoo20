"""A [PRUEBA] air consolidation on boss20 (a master air waybill with one house, invented data) whose house air waybill is
issued, to look at the IATA set of roadmap item 19 in the browser. Kept; a second run reuses it.
    dev/server_shell.sh sample_air_house.py"""
from datetime import date

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
File, Partner = env["boss.expediente"], env["res.partner"]  # noqa: F821
port = lambda code: env["boss.port"].search([("code", "=", code), ("kind", "=", "air")], limit=1)  # noqa: E731, F821
house = File.search([("goods_description", "=", "[PRUEBA] MUESTRA AWB: RECAMBIOS")], limit=1)
if not house:
    def company(name, country):
        return Partner.search([("name", "=", name)], limit=1) or Partner.create({
            "name": name, "is_company": True, "country_id": env.ref(f"base.{country}").id,  # noqa: F821
            "street": "[PRUEBA] Calle 1", "city": "[PRUEBA] Ciudad"})
    shipper, consignee = company("[PRUEBA] Muestra AWB Expedidor", "es"), company("[PRUEBA] Muestra AWB Destinatario", "au")
    route = {"partner_id": shipper.id, "business": "boss", "direction": "export", "transport_mode": "air",
             "load_type": "air", "origin_port_id": port("MAD").id, "destination_port_id": port("SYD").id,
             "etd": date(2026, 11, 25)}
    master = File.create(dict(route, mawb_ref="[PRUEBA] 157-00000011", vessel="[PRUEBA] QR148"))
    house = File.create(dict(route, master_id=master.id, shipper_id=shipper.id, consignee_id=consignee.id,
                             packages=3, package_type="CT", gross_kg=150.0, volume_m3=1.2,
                             goods_description="[PRUEBA] MUESTRA AWB: RECAMBIOS", house_doc_freight="prepaid"))
    house.action_issue_house_document()
print("HOUSE", house.id, house.name, "| issued", house.house_doc_issue_date, "| issues", house.house_doc_issue_count)
env.cr.commit()  # noqa: F821
