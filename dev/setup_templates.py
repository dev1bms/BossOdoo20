"""Quotation templates (standard sale_management) with the BOSS services that always apply per case, on boss20 (odoo
shell). Approved by Belal on 26/10/2026 (task TP02); names without «[DEMO]» since 27/10 (they are real cases, not demo
data). Idempotent by case code: a template is renamed, never created twice; missing services are added, none removed.

Lists: air import FOB = the services of the real offer to Cofitel 05570 (03/02/2026) and of its shipments E260167 /
E261152 (Odoo 17); sea import FCL = Odoo 19 «proposed by default» classification and the FCL file E260883 (Odoo 17),
with T3-PAD (MSC «PAD - Additional Port Expenses (T-3 incluido)»); air export = Odoo 19 classification. Cristina still
confirms the always/sometimes split per case (task TP03). Optional services (EXW-AIR pickup at origin, ALM, inspections,
SEG, CAU, QBR, extras) are added on the quotation with «Add services». The template note is Odoo's customer-facing
«Terms and conditions»: left empty (internal guidance lives in the user guide).

03/11/2026 (roadmap item 3, Belal: apply what is documented instead of asking again): sea export FCL, LCL import, LCL
export and road, with the services of the documented proposal F0-C09 (docs/decisiones-f0.md), built from BOSS's real
offers (NEW ODOO/COSTO_VENTA_MULTINIVEL.xlsx, sheets FCL_DAP and LCL IMB FOB). Reversible defaults: a service is
added or removed on the quotation, and the template is corrected as data."""
from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, mail_create_nosubscribe=True))  # noqa: F821
P, Template = env["product.product"], env["sale.order.template"]
TEMPLATES = {
    "IAB FOB · Importación aérea FOB · servicios fijos": ["FAI", "HAN", "AWB", "CSA", "FAD", "ETX", "TTE-CON"],
    "IMB FOB · Importación marítima FCL · servicios fijos": ["FMI", "THC", "BL", "GLO-CCC", "T3-PAD", "FAD", "CSM",
                                                             "TTE-FCL"],
    "EAB · Exportación aérea · servicios fijos": ["TTE-CON", "HAN", "AWB", "DEX", "CSA", "FAE"],
    "EMB · Exportación marítima FCL · servicios fijos": ["THC", "GLO-CCC", "BL", "VGM", "CSM", "T3-PAD", "DEX", "FME"],
    "IMB LCL FOB · Importación marítima LCL (grupaje) FOB · servicios fijos": ["FMI-LCL", "THC-LCL", "T3", "CSM", "BL",
                                                                                "FAD", "TTE-CON"],
    "EMB LCL · Exportación marítima LCL (grupaje) · servicios fijos": ["TTE-CON", "DEX", "CSM", "BL", "THC-LCL", "T3",
                                                                        "FME-LCL"],
    "TTE · Transporte por carretera · servicios fijos": ["TTE-CON", "CST"],
    # customs clearance only (Odoo 17 traffic ITB, e.g. E261189 with a BOSS guarantee): no carriage, the declaration
    # and its disbursements; CAU/QBR and ARA/IVA are added on the quotation when they apply (go-live tracker P4-08)
    "ITB · Solo despacho de aduana (importación) · servicios fijos": ["FAD"],
    # agent business (Odoo 17 traffic IMA, business of the agent's client): the import FCL services, quoted to the
    # agent in USD on the USD price list (go-live tracker P4-09). The profit share is settled per case (F0-C58): BOSS's
    # share is added as PFT-BOSS when invoiced to the agent; the origin agent's share is a cost of the file (PFT-FCL),
    # never sold (P12). The freight goes to the payer the Incoterm gives (F0-C57).
    "IMA FOB · Importación marítima FCL de agente · servicios fijos": ["FMI", "THC", "BL", "GLO-CCC", "T3-PAD", "FAD",
                                                                      "CSM", "TTE-FCL"],
}
EN_NAMES = dict(zip(TEMPLATES, [
    "IAB FOB · Air import FOB · fixed services",
    "IMB FOB · Sea import FCL · fixed services",
    "EAB · Air export · fixed services",
    "EMB · Sea export FCL · fixed services",
    "IMB LCL FOB · Sea import LCL (groupage) FOB · fixed services",
    "EMB LCL · Sea export LCL (groupage) · fixed services",
    "TTE · Road transport · fixed services",
    "ITB · Customs clearance only (import) · fixed services",
    "IMA FOB · Agent sea import FCL · fixed services",
]))
# The case of each template (ADR-006, meeting with Ángel 27/10/2026: the template fills the quotation). Direction, mode
# and whose client come from the case code (IAB = import · air · BOSS client, decision B13); the incoterm from the name;
# what BOSS handles is read from the services of the template (freight = main carriage, FAD = customs at destination,
# DEX = customs at origin, TTE = delivery on an import / pickup on an export). PROPOSAL until Cristina confirms (S1/S2
# in docs/reunion-angel-2026-10-27.md).
CASES = {
    "IAB FOB": dict(boss_business="boss", boss_direction="import", boss_transport_mode="air", boss_load_type="air",
                    incoterm="FOB", scope=("main", "destination_customs", "delivery")),
    "IMB FOB": dict(boss_business="boss", boss_direction="import", boss_transport_mode="sea", boss_load_type="fcl",
                    incoterm="FOB", scope=("main", "destination_customs", "delivery")),
    "EAB": dict(boss_business="boss", boss_direction="export", boss_transport_mode="air", boss_load_type="air",
                incoterm=False, scope=("pickup", "origin_customs", "main")),
    "EMB": dict(boss_business="boss", boss_direction="export", boss_transport_mode="sea", boss_load_type="fcl",
                incoterm=False, scope=("origin_customs", "main")),  # pickup (TTE-FCL) only when BOSS does it
    "IMB LCL FOB": dict(boss_business="boss", boss_direction="import", boss_transport_mode="sea", boss_load_type="lcl",
                        incoterm="FOB", scope=("main", "destination_customs", "delivery")),
    "EMB LCL": dict(boss_business="boss", boss_direction="export", boss_transport_mode="sea", boss_load_type="lcl",
                    incoterm=False, scope=("pickup", "origin_customs", "main")),
    "ITB": dict(boss_business="boss", boss_direction="import", boss_transport_mode="sea", boss_load_type="fcl",
                incoterm=False, scope=("destination_customs",)),
    "IMA FOB": dict(boss_business="agent", boss_direction="import", boss_transport_mode="sea", boss_load_type="fcl",
                    incoterm="FOB", scope=("main", "destination_customs", "delivery")),
    # road: national, import or export, chosen on the quotation (customs FAD/DEX added when BOSS clears)
    "TTE": dict(boss_business="boss", boss_direction=False, boss_transport_mode="road", boss_load_type="road",
                incoterm=False, scope=("main", "delivery")),
}
SCOPES = ("pickup", "origin_customs", "main", "destination_customs", "delivery")
OLD_NOTE = "Plantilla de servicios que aplican SIEMPRE"
made = {}
# a template is found by its case code (the start of its name), in any earlier name
for name in TEMPLATES:
    code = name.split(" · ")[0]
    old = Template.with_context(active_test=False).search([("name", "=ilike", f"%{code} · %")], limit=1)
    if old and old.name != name:
        old.name = name
assert not env["ir.config_parameter"].sudo().get_str("sale.default_sale_order_template_id"), "a default template would apply to every quotation"
for name, codes in TEMPLATES.items():
    products = [P.search([("default_code", "=", c)], limit=1) for c in codes]
    assert all(products), [c for c, p in zip(codes, products) if not p]
    template = Template.search([("name", "=", name)], limit=1)
    if not template:
        template = Template.create({"name": name})
    for t_line in template.sale_order_template_line_ids.filtered(lambda l: l.product_id and l.product_uom_id != l.product_id.uom_id):
        # the line keeps the unit the service had when it was added (ETX was per file, now per AWB: found in Chrome
        # on 27/10, its tariff and sale price did not apply): follow the service's unit
        print("UNIT", t_line.product_id.default_code, t_line.product_uom_id.name, "->", t_line.product_id.uom_id.name)
        t_line.product_uom_id = t_line.product_id.uom_id
    have = template.sale_order_template_line_ids.product_id
    template.sale_order_template_line_ids = [
        Command.create({"product_id": p.id, "product_uom_qty": 1, "product_uom_id": p.uom_id.id, "sequence": i * 10 - (5 if have else 0)})
        for i, p in enumerate(products, start=1) if p not in have]  # an added one goes before the next
    # The name is translatable: the same «<case>» prefix in every language, so that the template is found by
    # its case code whatever the language of the user (found in Chrome on 26/10: the English name was an older one).
    template.with_context(lang="es_ES").name = name
    template.with_context(lang="en_US").name = EN_NAMES[name]
    if any(OLD_NOTE in (template.with_context(lang=lang).note or "") for lang in ("es_ES", "en_US")):
        template.note = False
    case = dict(CASES[name.split(" · ")[0]])
    incoterm, scope = case.pop("incoterm"), case.pop("scope")
    case["boss_incoterm_id"] = incoterm and env["account.incoterms"].search([("code", "=", incoterm)], limit=1).id  # noqa: F821
    case.update({f"boss_scope_{s}": s in scope for s in SCOPES})
    template.write(case)
    made[name] = template
    print("TEMPLATE", template.id, name[:40], template.boss_traffic_code, template.boss_incoterm_id.code or "-",
          [s for s in SCOPES if template[f"boss_scope_{s}"]], [l.product_id.default_code for l in template.sale_order_template_line_ids])
env.cr.commit()
