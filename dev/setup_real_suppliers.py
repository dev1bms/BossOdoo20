"""The suppliers of the tariffs loaded from real documents were created as sample partners («MSC [MUESTRA]»…). They are
the real companies BOSS buys from: give them their legal data from Odoo 17 production (read on 27/10/2026, partner id in
«ref» as O17:<id>), keeping the same records so tariffs, purchases and bills stay linked. Idempotent.
    dev/server_shell.sh setup_real_suppliers.py"""
from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
Partner = env["res.partner"]
es, de = env.ref("base.es"), env.ref("base.de")
role = env.ref
# (sample name on boss20, Odoo 17 id, legal name, VAT, street, zip, city, country, roles)
SUPPLIERS = [
    ("MSC [MUESTRA]", 23762, "MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.", "ESB98261944", "C/Suiza 12", "46024",
     "Valencia", es, ["boss_expediente.role_carrier"]),
    ("WFS [MUESTRA]", 23336, "WORLDWIDE FLIGHT SERVICES", "ESA81050353", "Centro de Carga Aérea. Aeropuerto El Prat",
     "08820", "Barcelona", es, ["boss_expediente.role_handler"]),
    ("IRENEO [MUESTRA]", 23062, "IRENEO LOGÍSTICA, S.L.", "ESB28509412", "Parcela 2-4 Nave 7", "28042", "Madrid", es,
     ["boss_expediente.role_haulier", "boss_expediente.role_handler"]),
    ("CMA CGM [MUESTRA]", 23016, "CMA CGM IBERICA, S.A.U.", "ESA83728279", "C/ Menorca, 19", "46023", "Valencia", es,
     ["boss_expediente.role_carrier"]),
    # Odoo 17 keeps the German VAT, the Hamburg address and a Spanish zip on the Spanish company name: copied as it is.
    ("Hapag-Lloyd [MUESTRA]", 23276, "HAPAG-LLOYD, S.L.", "DE813960018", "Ballindamm 25, 20095", "08002", "Hamburg", de,
     ["boss_expediente.role_carrier"]),
]
for sample, o17, name, vat, street, zip_code, city, country, roles in SUPPLIERS:
    partner = Partner.search([("ref", "=", f"O17:{o17}")], limit=1) or Partner.search([("name", "=", sample)], limit=1)
    if not partner:
        print("NOT FOUND", sample)
        continue
    partner.write({"name": name, "ref": f"O17:{o17}", "vat": vat, "street": street, "zip": zip_code, "city": city,
                   "country_id": country.id, "is_company": True, "boss_is_supplier": True,
                   "boss_role_ids": [Command.link(role(r).id) for r in roles]})
    print("SUPPLIER", partner.id, partner.name, partner.vat, partner.ref)
env.cr.commit()
