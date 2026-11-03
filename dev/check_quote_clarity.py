"""Check of roadmap item 9 (boss20, rolled back): fewer entries on a quotation, the port fills its country, the search
for «MSC» offers the carrier group.

A sea import FCL quotation (template IMB FOB) for a [PRUEBA] customer with one warehouse in Valencia needs six entries
(customer, template, carrier, origin port, ETA, container): the template gives the case and Spain; the customer gives
the consignee and the delivery address (its only warehouse, so its province); the Spanish port comes from the
customer's latest quotation of the same traffic (else the one BOSS uses most); the origin port gives its country.
THC is then priced from the MSC tariff. Prints «CHECK PASS|FAIL …» and «RESULT …», never an amount.
    dev/uat_run.sh check_quote_clarity.py boss20"""
from datetime import date

from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


port = lambda code: env["boss.port"].search([("code", "=", code), ("kind", "=", "sea")], limit=1)  # noqa: E731
Partner = env["res.partner"]
msc = ref("o17_partner.res_partner_23762")  # MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.
template = env["sale.order.template"].search([("name", "=like", "IMB FOB · %")], limit=1)
valencia = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "V")], limit=1)
customer = Partner.create({"name": "[PRUEBA] Cliente con un almacén", "is_company": True, "vat": "ESB12345674",
                           "country_id": ref("base.es").id, "state_id": valencia.id, "city": "Valencia"})
warehouse = Partner.create({"name": "[PRUEBA] Almacén Paterna", "parent_id": customer.id, "type": "delivery",
                            "street": "Calle 1", "city": "Paterna", "state_id": valencia.id,
                            "country_id": ref("base.es").id})

# 1. the practice: the customer's previous sea import went through Valencia
env["sale.order"].create({"partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea",
                          "boss_business": "boss", "boss_load_type": "fcl", "boss_destination_port_id": port("ESVLC").id,
                          "boss_destination_country_id": ref("base.es").id, "boss_origin_country_id": ref("base.cn").id})

# 2. six entries
with Form(env["sale.order"]) as form:
    form.partner_id = customer
    form.sale_order_template_id = template
    check("1 template IMB: import, sea, FCL, destination Spain, consignee = the customer",
          ("import", "sea", "fcl", "ES", customer.id),
          (form.boss_direction, form.boss_transport_mode, form.boss_load_type,
           form.boss_destination_country_id.code, form.boss_consignee_id.id))
    check("2 delivery address proposed: the customer's only warehouse, and its province",
          (warehouse.id, valencia.id), (form.boss_delivery_address_id.id, form.boss_inland_state_id.id))
    check("3 Spanish port proposed from the customer's latest sea import", "ESVLC", form.boss_destination_port_id.code)
    form.boss_carrier_id = msc
    form.boss_origin_port_id = port("CNXGG")
    check("4 the origin port fills its country", "CN", form.boss_origin_country_id.code)
    form.boss_eta = date(2026, 12, 16)
    with form.boss_container_ids.new() as row:
        row.size = "20"
    check("5 container: type DV and 1 unit by default", ("DV", 1), (row.container_type_id.code, row.quantity))
order = form.save()
order.action_boss_update_costs()
thc = order.order_line.filtered(lambda l: l.product_id.default_code == "THC")
check("6 after six entries THC is priced from the MSC tariff (status only, no amount)",
      (1, "ok", True), (len(thc), thc.boss_cost_status, thc.boss_sale_status in ("agreed", "cost_based")))
check("7 the pricing inputs follow: Spanish port, country abroad, tariff date = ETA",
      ("ESVLC", "CN", date(2026, 12, 16)), (order.boss_port_id.code, order.boss_country_id.code, order.boss_planned_date))

# 3. a customer without history and without warehouse: BOSS's most used port, the customer itself as address
other = Partner.create({"name": "[PRUEBA] Cliente nuevo sin almacén", "is_company": True, "vat": "ESB12345674",
                        "country_id": ref("base.es").id, "state_id": valencia.id, "city": "Valencia"})
with Form(env["sale.order"]) as form:
    form.partner_id = other
    form.sale_order_template_id = template
    proposed = form.boss_destination_port_id
    check("8 new customer: a Spanish sea port is proposed (the one BOSS uses most for sea imports)",
          ("ES", "sea"), (proposed.country_id.code, proposed.kind))
    check("9 new customer without warehouse: its own address is the delivery address", other.id,
          form.boss_delivery_address_id.id)
    form.boss_destination_port_id = port("ESBCN")
    check("10 a port chosen by the user is kept (proposals only fill empty fields)", "ESBCN",
          form.boss_destination_port_id.code)
    form.boss_origin_port_id = port("CNXGG")
    form.boss_origin_port_id = port("VNSGN")
    check("11 changing the origin port corrects the country", "VN", form.boss_origin_country_id.code)

# 4. the carrier search: companies only, the MSC group among the first results
group = Partner.search([("name", "=", "Mediterranean Shipping Company (MSC)")], limit=1)
group.is_company = True  # set for real by dev/fix_carrier_groups.py (no-op once done)
found = Partner.browse([i for i, _name in Partner.name_search("MSC", domain=[("is_company", "=", True)], limit=8)])
check("12 searching «MSC» among companies offers the carrier group and the Spanish entity, no person",
      (True, True, True), (group in found, msc in found, all(found.mapped("is_company"))))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
