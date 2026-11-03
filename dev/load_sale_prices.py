"""Load BOSS's selling prices of Odoo 17 into the pricelists of boss20 (roadmap item 3; Belal's go-ahead of 03/11/2026
to copy settings). The data file is private (real prices, .research/sale_prices_o17.json, never in Git) and is passed
by dev/server_shell.sh; this script holds no price.
    dev/server_shell.sh load_sale_prices.py .research/sale_prices_o17.json

- «Standard» template of Odoo 17 (no customer, Cristina) → fixed rules of the general pricelist (the one holding the
  default «cost + %» rule): an agreed price wins over cost + % (Ángel, meeting 27/10, M2-16).
- each customer template → the customer's own pricelist (created when the customer is on the general one), with the
  same fixed rules and, last, «based on the general pricelist» so every other service still gets cost + %.
- a price per container size becomes one rule per size; a rule is created once and updated when its price changed
  (idempotent). Nothing is converted between charge bases: the mapping and what was left out are in the data file.
Prints counts and names only. MODE «dry» rolls back.
"""
import json
import os

from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
MODE = "commit"
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
name = os.environ["BOSS_FILES"].split("|")[0]
assert name == "sale_prices_o17.json", name
data = json.load(open(f"/tmp/boss/{name}", encoding="utf-8"))
Item = env["product.pricelist.item"]
general = env["res.config.settings"]._boss_default_markup_rules()[:1].pricelist_id
assert general, "no general pricelist with the default cost + % rule"
counts = {"created": 0, "updated": 0, "same": 0}


def product(code):
    found = env["product.product"].search([("default_code", "=", code)], limit=1)
    assert found, code
    return found


def upsert(pricelist, rule):
    service = product(rule["service"])
    key = [("pricelist_id", "=", pricelist.id), ("applied_on", "=", "1_product"),
           ("product_tmpl_id", "=", service.product_tmpl_id.id), ("uom_id", "=", service.uom_id.id),
           ("boss_container_size", "=", rule["size"] or False), ("min_quantity", "=", 0)]
    item = Item.search(key, limit=1)
    if not item:
        Item.create({"pricelist_id": pricelist.id, "applied_on": "1_product",
                     "product_tmpl_id": service.product_tmpl_id.id, "uom_id": service.uom_id.id,
                     "compute_price": "fixed", "fixed_price": rule["price"], "boss_container_size": rule["size"] or False})
        counts["created"] += 1
    elif item.compute_price != "fixed" or item.fixed_price != rule["price"]:
        item.write({"compute_price": "fixed", "fixed_price": rule["price"]})
        counts["updated"] += 1
    else:
        counts["same"] += 1


for rule in data["general"]["rules"]:
    upsert(general, rule)
print(f"GENERAL {general.name}: {len(data['general']['rules'])} rules from «{data['general']['template']}»")

for customer in data["customers"]:
    partner = env.ref(f"o17_partner.res_partner_{customer['o17_partner']}")
    pricelist = partner.property_product_pricelist
    if not pricelist or pricelist == general:
        pricelist = env["product.pricelist"].search(
            [("name", "=", f"{partner.name} · precios de venta (Odoo 17)")], limit=1) or env["product.pricelist"].create(
            {"name": f"{partner.name} · precios de venta (Odoo 17)", "currency_id": general.currency_id.id,
             "company_id": general.company_id.id})
        partner.property_product_pricelist = pricelist
    for rule in customer["rules"]:
        upsert(pricelist, rule)
    if not pricelist.item_ids.filtered(lambda i: i.base == "pricelist" and i.base_pricelist_id == general):
        pricelist.item_ids = [Command.create({"applied_on": "3_global", "compute_price": "discount",
                                              "price_discount": 0.0, "base": "pricelist",
                                              "base_pricelist_id": general.id})]
    print(f"CUSTOMER {partner.name}: pricelist «{pricelist.name}», {len(customer['rules'])} rules from "
          f"«{customer['template']}», {len(customer['skipped'])} lines left out, falls back to {general.name}")

print("COUNTS", counts)
if MODE == "commit":
    env.cr.commit()
else:
    env.cr.rollback()
print(f"RESULT mode {MODE}")
