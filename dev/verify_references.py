"""Check the supplier reference examples on a database WITHOUT changing it (odoo shell).

The sample tariffs are approved inside the transaction only to compute, and everything is rolled back.
Data file: /tmp/samples.json (private, real prices). Prints one line per failure and a summary.
"""
import json
from datetime import date

env = env  # noqa: F821 (odoo shell)
data = json.load(open("/tmp/samples.json", encoding="utf-8"))


def rid(model, domain):
    return env[model].with_context(active_test=False).search(domain, limit=1).id


def inputs_of(raw):
    inputs = {k: raw[k] for k in ("direction", "transport_mode", "load_type", "line_qty", "gross_kg", "volume_m3",
                                  "awb_kg", "storage_days", "container_size") if k in raw}
    if "carrier" in raw:
        inputs["carrier_id"] = rid("res.partner", [("name", "=", f"{raw['carrier']} [MUESTRA]")])
    if "country" in raw:
        inputs["country_id"] = rid("res.country", [("code", "=", raw["country"])])
    if "port" in raw:
        inputs["port_id"] = rid("boss.port", [("code", "=", raw["port"])])
    if "state" in raw:
        inputs["state_id"] = rid("res.country.state", [("country_id.code", "=", "ES"), ("code", "=", raw["state"])])
    if "container_type" in raw:
        inputs["container_type_id"] = rid("boss.container.type", [("code", "=", raw["container_type"])])
    if "containers" in raw:
        inputs["containers"] = [{"size": s, "quantity": q, "type_id": rid("boss.container.type", [("code", "=", t)])}
                                for s, t, q in raw["containers"]]
    if "related" in raw:
        supplier = rid("res.partner", [("name", "=", "IRENEO [MUESTRA]")])
        inputs["related_costs"] = [{"product_id": rid("product.product", [("default_code", "=", c)]),
                                    "supplier_id": supplier, "amount": a, "currency": "EUR"} for c, a in raw["related"]]
    return inputs


try:
    samples = env["boss.tariff"].search([("name", "like", "[MUESTRA]")])
    samples.filtered(lambda t: t.state == "to_approve").with_user(env.ref("base.user_admin")).action_approve()
    failures = 0
    for ref in data["references"]:
        product = env["product.product"].search([("default_code", "=", ref["service"])])
        res = env["boss.pricing"].price_cost(product, env.ref(f"boss_services.uom_{ref['uom']}"),
                                             inputs_of(ref["inputs"]), date.fromisoformat(ref["date"]))
        ok = res.status != "ok" if ref["expected"] is None else (res.status == "ok" and round(res.amount, 2) == ref["expected"])
        if not ok:
            failures += 1
            print("VERIFY FAIL", ref["ref"], ref["service"], ref["expected"], res.status, res.amount, res.missing)
    print(f"VERIFY {env.cr.dbname}: {len(data['references'])} references, {failures} failures, {len(samples)} sample tariffs")
finally:
    env.cr.rollback()
    print("VERIFY rolled back; sample states now:", sorted(set(env["boss.tariff"].search([("name", "like", "[MUESTRA]")]).mapped("state"))))
