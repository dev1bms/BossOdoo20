"""Check of the settings, phase 2 (boss20, rolled back): the service lists that were in the code are attributes of the
service and of the incoterm, seeded once, and the behaviour follows them. Fictitious records only.
    dev/uat_run.sh check_service_fields.py boss20"""
from datetime import date

from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


T = lambda code: env["product.template"].search([("default_code", "=", code)], limit=1)  # noqa: E731
P = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
inco = lambda code: env["account.incoterms"].search([("code", "=", code)], limit=1)  # noqa: E731

# 1. seeds (migration): what the code listed is on the services and the incoterms
check("1 bought from the handler: HAN, ALM, AWB, ETX; from the haulier: TTE-CON, TTE-FCL; FAD from anyone",
      ("handler", "handler", "handler", "handler", "haulier", "haulier", "any"),
      tuple(T(c).boss_supplier_role for c in ("HAN", "ALM", "AWB", "ETX", "TTE-CON", "TTE-FCL", "FAD")))
check("2 customs value charges: FMI freight, THC-LCL THC, T3-PAD T3, SEG insurance, FAD none",
      ("freight", "THC", "T3", "insurance", False),
      tuple(T(c).boss_customs_value_charge for c in ("FMI", "THC-LCL", "T3-PAD", "SEG", "FAD")))
dem = T("DEM")
check("3 DEM default periods on the service: import ATA → empty return, export gate-in → departure",
      {("import", "ata", "container_empty_return"), ("export", "container_gate_in", "departure")},
      {(p.direction, p.start_event, p.end_event) for p in dem.boss_period_ids})
alm = T("ALM")
check("4 ALM: the LCL import line (emptying → pickup) and the LCL export line without period",
      {("import", "lcl", "emptying", "pickup"), ("export", "lcl", False, False),
       ("import", False, "noa_or_ata", "pickup"), ("export", False, "foh", "departure")},
      {(p.direction, p.load_type, p.start_event, p.end_event) for p in alm.boss_period_ids})
check("5 incoterms: CFR, CIF, DAP prepaid; EXW, FOB collect", ("prepaid", "prepaid", "prepaid", "collect", "collect"),
      tuple(inco(c).boss_freight_payment for c in ("CFR", "CIF", "DAP", "EXW", "FOB")))

# 2. the behaviour follows the attributes
customer = env["res.partner"].create({"name": "[PRUEBA] Atributos Cliente", "is_company": True})
haulier = env["res.partner"].create({"name": "[PRUEBA] Atributos Camionero", "is_company": True, "supplier_rank": 1})
service = env["product.product"].create({"name": "[PRUEBA] Reparto urbano", "default_code": "PRB-URB", "type": "service",
                                         "boss_pricing_mode": "manual", "boss_cost_method": "manual",
                                         "boss_supplier_role": "haulier", "boss_customs_value_charge": "T3"})
order = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "incoterm": inco("CFR").id,
    "order_line": [Command.create({"product_id": service.id, "product_uom_qty": 1, "price_unit": 50.0,
                                   "boss_supplier_id": haulier.id})]})
check("6 a new service marked «bought from the haulier» is a road line: its supplier is the quotation's haulier",
      haulier, order.boss_haulier_id)
check("7 ... and counts as T3 for the customs broker text", "T3", env["boss.expediente"]._boss_customs_value_charge(service))
file = env["boss.expediente"].create({"partner_id": customer.id, "business": "boss", "direction": "import",
                                      "transport_mode": "sea", "load_type": "fcl", "incoterm_id": inco("CFR").id,
                                      "eta": date(2026, 12, 1)})
need = env["boss.expediente.cost"].create({"expediente_id": file.id, "kind": "extra", "product_id": P("DEM").id,
                                           "uom_id": P("DEM").uom_id.id, "quantity": 1.0, "expected_unit_cost": 1.0,
                                           "extra_class": "covered", "reason": "[PRUEBA]"})
check("8 a DEM need takes its period from the service: ATA → empty return (default)",
      ("ata", "container_empty_return", "default"), need._boss_period_events())
dem.boss_period_ids.filtered(lambda p: p.direction == "import").write({"start_event": "discharge"})
check("9 ... changed on the service (discharge → empty return), no code", ("discharge", "container_empty_return", "default"),
      need._boss_period_events())
check("10 the house document reads the incoterm: CFR → prepaid", "prepaid", file.house_doc_freight)
inco("CFR").boss_freight_payment = "collect"
env.flush_all()
file.invalidate_recordset(["house_doc_freight"])
other = env["boss.expediente"].create({"partner_id": customer.id, "business": "boss", "direction": "import",
                                       "transport_mode": "sea", "load_type": "fcl", "incoterm_id": inco("CFR").id})
check("11 a change on the incoterm is proposed to the files that take it afterwards, never rewrites a file",
      ("prepaid", "collect"), (file.house_doc_freight, other.house_doc_freight))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
