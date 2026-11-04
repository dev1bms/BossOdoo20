"""Load the minimum margin control of Odoo 17 into boss20 (roadmap item 15): groups of services, rules by kind of
shipment, policies of single services and the exceptions per customer or carrier. The data is private (commercial
terms) and stays out of Git: .research/margin_rules_o17.json, read from Odoo 17 production on 04/11/2026.
Idempotent by name: a second run updates, never duplicates. Prints counts, not terms.
    dev/server_shell.sh load_margin_rules.py .research/margin_rules_o17.json"""
import json
import os

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
name = [n for n in os.environ.get("BOSS_FILES", "").split("|") if n == "margin_rules_o17.json"]
assert name, "pass .research/margin_rules_o17.json"
data = json.load(open(f"/tmp/boss/{name[0]}", encoding="utf-8"))
Family = env["boss.margin.family"].with_context(active_test=False)  # noqa: F821
Rule = env["boss.margin.rule"].with_context(active_test=False)  # noqa: F821
Exception_ = env["boss.margin.exception"].with_context(active_test=False)  # noqa: F821
Product = env["product.product"].with_context(active_test=False)  # noqa: F821
missing = set()


def products(codes):
    found = Product.search([("default_code", "in", codes)])
    missing.update(set(codes) - set(found.mapped("default_code")))
    return found


def o17_partner(o17_id):
    partner = env.ref(f"o17_partner.res_partner_{o17_id}", raise_if_not_found=False)  # noqa: F821
    if not partner:
        missing.add(f"partner {o17_id}")
    return partner


def upsert(model, domain, values):
    record = model.search(domain, limit=1)
    if record:
        record.write(values)
    else:
        record = model.create(values)
    return record


families = {}
for seq, group in enumerate(data["groups"], start=1):
    families[group["name"]] = upsert(Family, [("name", "=", group["name"]), ("kind", "=", "group")], {
        "name": group["name"], "kind": "group", "sequence": seq, "active": True,
        "product_ids": [(6, 0, products(group["codes"]).ids)]})
for seq, policy in enumerate(data["policies"], start=1):
    upsert(Family, [("name", "=", policy["name"]), ("kind", "=", "policy")], {
        "name": policy["name"], "kind": "policy", "sequence": seq, "active": True,
        "product_ids": [(6, 0, products(policy["codes"]).ids)], "percent": policy["percent"],
        "exact": policy["exact"], "allow_negative": policy["allow_negative"]})
FIELDS = ("transport_mode", "load_type", "business", "direction", "freight_payment", "percent", "cap_per_container",
          "min_amount", "min_per_container", "min_per_container_20", "min_per_container_40", "min_per_kg")
for seq, rule in enumerate(data["rules"], start=1):
    family = families[rule["group"]]
    upsert(Rule, [("family_id", "=", family.id), ("name", "=", rule["name"])], dict(
        {"family_id": family.id, "name": rule["name"], "sequence": seq, "active": True},
        **{f: rule.get(f, False if f in FIELDS[:5] else 0.0) for f in FIELDS}))
for exc in data["exceptions"]:
    values = {"name": exc["name"], "sequence": exc["o17"], "active": True,
              "customer_id": exc.get("customer") and o17_partner(exc["customer"]).id or False,
              "carrier_id": exc.get("carrier") and o17_partner(exc["carrier"]).id or False,
              "freight_payment": exc.get("freight_payment", False),
              "family_id": exc.get("group") and families[exc["group"]].id or False,
              "product_ids": [(6, 0, products(exc.get("codes", [])).ids)],
              "force_amount": exc.get("force_amount", False), "amount": exc.get("amount", 0.0),
              "force_percent": exc.get("force_percent", False), "percent": exc.get("percent", 0.0),
              "allow_negative": exc.get("allow_negative", False)}
    upsert(Exception_, [("name", "=", exc["name"])], values)
env.cr.commit()  # noqa: F821
print("LOADED groups", Family.search_count([("kind", "=", "group")]), "policies",
      Family.search_count([("kind", "=", "policy")]), "rules", Rule.search_count([]), "exceptions",
      Exception_.search_count([]))
print("NOT FOUND (left out):", sorted(missing) or "none")
