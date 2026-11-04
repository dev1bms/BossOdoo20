"""Check of the import freight VAT rule (boss20, rolled back): an NR service that counts for the customs value is
exempt on a TER->PRO import (Art. 64 LIVA, FTT; Cristina, 04/11/2026); the other routes, the services outside the
customs value and the purchase side keep their rules. Fictitious records only.
    dev/uat_run.sh check_vat_import_freight.py boss20"""
from odoo.addons.boss_pricing_sale.models import vat_rules

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


T = lambda code: env["product.template"].with_context(active_test=False).search(  # noqa: E731
    [("default_code", "=", code)], limit=1)
rule = lambda *args: vat_rules.vat_class(*args)[0]  # noqa: E731

# 1. the rule
check("1 NR in the customs value, China -> Spain, Spanish customer: EX", "EX", rule("NR", "TER", "PRO", "PRO", True))
check("2 same service, national, Spain -> Spain: NR", "NR", rule("NR", "PRO", "PRO", "PRO", True))
check("3 same service, EU -> Spain and China -> EU: NR (unchanged)", ("NR", "NR"),
      (rule("NR", "COM", "PRO", "PRO", True), rule("NR", "TER", "COM", "PRO", True)))
check("4 NR outside the customs value (TTE-CON), China -> Spain: NR (unchanged)", "NR",
      rule("NR", "TER", "PRO", "PRO", False))
check("5 the trace names the exemption", True,
      any("Art. 64" in step for step in vat_rules.vat_class("NR", "TER", "PRO", "PRO", True)[1]))

# 2. the data: FTT is the only NR service in the customs value
ftt = T("FTT")
check("6 FTT: base NR, counts for the customs value as freight", ("NR", "freight"),
      (ftt.boss_vat_class, ftt.boss_customs_value_charge))
nr_in_value = env["product.template"].with_context(active_test=False).search(
    [("boss_customs_value_charge", "!=", False), ("boss_vat_class", "=", "NR")])
check("7 NR services in the customs value", ["FTT"], nr_in_value.mapped("default_code"))
check("8 TTE-CON, TTE-FCL outside the customs value", (False, False),
      (T("TTE-CON").boss_customs_value_charge, T("TTE-FCL").boss_customs_value_charge))

# 3. a quotation: import China -> Valencia for a Spanish customer
ftt.active = True
customer = env["res.partner"].create({"name": "CLIENTE ES PRUEBA IVA FTT (FICTICIO)",
                                      "country_id": env.ref("base.es").id})
order = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_port_id": env.ref("boss_pricing.port_esvlc").id, "boss_country_id": env.ref("base.cn").id})
lines = env["sale.order.line"].create([{"order_id": order.id, "product_id": T(code).product_variant_id.id}
                                       for code in ("FTT", "TTE-CON")])
check("9 quotation China -> Valencia: FTT EX, TTE-CON NR", ("EX", "NR"), tuple(lines.mapped("boss_vat_class")))
order.write({"boss_direction": "export", "boss_country_id": env.ref("base.fr").id})
check("10 export Valencia -> France: FTT EX by the route, as before", "EX", lines[0].boss_vat_class)

env.cr.rollback()
print(f"RESULT {results.count(True)} passed, {results.count(False)} failed")
if not all(results):
    raise SystemExit(1)
