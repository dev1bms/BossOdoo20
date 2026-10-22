"""Verify the trial path on boss20 as real roles, WITHOUT changing the database (odoo shell; everything rolled back).

A salesperson (sales + tariff entry) and an approver (sales manager + tariff approver) are created inside the
transaction. Steps: approve the [DEMO] tariffs -> quotation from the [DEMO] opportunity -> shipment data -> add
services -> cost per line -> missing price added from the quotation and approved -> sale price from the customer
agreement -> VAT from the BOSS VAT table (Spanish customer: THC pending, the only blocker) -> EU customer quotation
accepted -> frozen + snapshot. Air quotation: ALM threshold and Saturday rule, HAN from the AWB weight. No e-mail is sent.
"""
import base64
from datetime import date

from odoo import Command
from odoo.exceptions import UserError

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname
ref = env.ref
checks = []


def check(label, got, expected):
    checks.append((label, got == expected, got, expected))


def trial(name):
    imd = env["ir.model.data"].search([("module", "=", "boss_trial"), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id)


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


try:
    groups = lambda *xmlids: [Command.set([ref(x).id for x in xmlids])]  # noqa: E731
    Users = env["res.users"].with_context(no_reset_password=True)
    sales = Users.create({"name": "VERIFY comercial", "login": "verify_sales_tmp", "group_ids": groups(
        "base.group_user", "sales_team.group_sale_salesman", "boss_pricing.group_tariff_user")})
    approver = Users.create({"name": "VERIFY aprobador", "login": "verify_approver_tmp", "group_ids": groups(
        "base.group_user", "sales_team.group_sale_manager", "boss_pricing.group_tariff_approver")})
    for name in ("tariff_sea", "tariff_road", "tariff_air"):
        trial(name).with_user(approver).action_approve()
    with_sales = lambda rec: rec.with_user(sales)  # noqa: E731

    # --- sea FCL: THC agreed, DEM time, TTE-FCL + FS percent, CES missing then added -------------------------
    lead = trial("lead_sea")
    (lead | trial("lead_air")).user_id = sales  # the salesperson owns the opportunities, as in real use
    order = with_sales(env["sale.order"]).create({
        "partner_id": lead.partner_id.id, "opportunity_id": lead.id, "boss_direction": "import",
        "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": trial("carrier").id,
        "boss_port_id": ref("boss_pricing.port_esvlc").id, "boss_country_id": ref("base.cn").id,
        "boss_planned_date": date(2026, 11, 4), "boss_storage_days": 12,
        "boss_container_ids": [
            Command.create({"size": "20", "container_type_id": ref("boss_pricing.container_type_dv").id, "quantity": 2}),
            Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id, "quantity": 1})]})
    check("pricelist from the customer agreement", order.pricelist_id, trial("pricelist"))
    services = product("THC") | product("DEM") | product("TTE-FCL") | product("FS") | product("CES")
    with_sales(env["boss.add.services"]).create(
        {"order_id": order.id, "product_ids": [Command.set(services.ids)]}).action_add()
    line = lambda code, size=False: order.order_line.filtered(  # noqa: E731
        lambda l: l.product_id.default_code == code and (not size or l.boss_container_size == size))
    check("THC 20' cost", (line("THC", "20").boss_cost_status, line("THC", "20").boss_cost_amount), ("ok", 300.0))
    check("THC 40' sale agreed", (line("THC", "40").price_unit, line("THC", "40").boss_sale_status), (230.0, "agreed"))
    # DEM: 12 days, 7 free (deducted), relative tiers: days 8-12 = 5 x 30 per container
    check("DEM 20' estimate", (line("DEM", "20").boss_cost_amount, line("DEM", "20").boss_cost_is_estimate), (300.0, True))
    check("TTE-FCL 40' cost", line("TTE-FCL", "40").boss_cost_amount, 320.0)
    check("FS 8 % of transport", (line("FS").boss_cost_status, line("FS").boss_cost_amount), ("ok", 76.8))
    check("FS sale from cost (+15 %)", (line("FS").price_unit, line("FS").boss_sale_status), (88.32, "cost_based"))
    check("DEM 20' sale: 150 + 15 % < 150 + 30 minimum margin", line("DEM", "20").price_unit, 180.0)
    check("TTE-FCL 20' sale = 320 + 48", line("TTE-FCL", "20").price_unit, 368.0)
    check("CES missing price", (line("CES", "20").boss_cost_status, line("CES", "20").boss_sale_status),
          ("no_tariff", "missing"))
    for ces in line("CES"):
        wizard = with_sales(env["boss.supplier.price.wizard"]).create({
            "sale_line_id": ces.id, "unit_price": 45.0, "document_page": "3",
            "document": base64.b64encode(b"%PDF-1.4 [DEMO]").decode(), "document_name": "demo-ces.pdf"})
        wizard.action_save()
    check("CES after entry", line("CES", "20").boss_cost_status, "pending_approval")
    line("CES").boss_cost_candidate_ids.tariff_id.with_user(approver).action_approve()
    check("CES approved: cost and sale", (line("CES", "20").boss_cost_amount, line("CES", "20").price_unit), (90.0, 51.75))
    # VAT from the BOSS VAT table (no temporary mapping): Spanish customer, import from China.
    tpl = env["account.chart.template"].with_company(order.company_id).ref
    t21, t_eu, t_ns = (tpl(f"account_tax_template_{x}") for x in ("s_iva21s", "s_iva0_sp_i", "s_iva0_ns"))
    check("DEM (NR, Spanish customer): 21% S", (line("DEM", "20").boss_vat_class, line("DEM", "20").tax_ids), ("NR", t21))
    check("THC (EX, Spanish customer): VAT pending, decision open",
          (line("THC", "20").boss_vat_class, line("THC", "20").boss_vat_status), ("EX", "pending"))
    ara = product("ARA")
    with_sales(env["boss.add.services"]).create({"order_id": order.id, "product_ids": [Command.set(ara.ids)]}).action_add()
    check("ARA (NS, paid on behalf): 0% EXEMPT NS", line("ARA").tax_ids, t_ns)
    line("ARA").write({"boss_manual_cost": 120.0, "price_unit": 120.0})
    try:
        with_sales(order).action_quotation_send()
        check("send blocked only by THC (EX, Spanish customer)", "sent", "blocked")
    except UserError as error:
        blocking = [ln for ln in str(error).splitlines() if ln.startswith("- ")]
        check("send blocked only by THC (EX, Spanish customer)", all("[THC]" in ln for ln in blocking) and len(blocking) == 2, True)
        print("BLOCK MESSAGE:", " | ".join(str(error).splitlines())[:400])

    # --- EU customer: every VAT case is decided -> the quotation is accepted -------------------------------
    lead_eu = trial("lead_eu")
    lead_eu.user_id = sales
    eu = with_sales(env["sale.order"]).create({
        "partner_id": lead_eu.partner_id.id, "opportunity_id": lead_eu.id, "boss_direction": "import",
        "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": trial("carrier").id,
        "boss_port_id": ref("boss_pricing.port_esvlc").id, "boss_country_id": ref("base.cn").id,
        "boss_planned_date": date(2026, 11, 4), "boss_storage_days": 10,
        "boss_container_ids": [Command.create({"size": "40", "container_type_id": ref("boss_pricing.container_type_hc").id,
                                               "quantity": 1})]})
    with_sales(env["boss.add.services"]).create({"order_id": eu.id, "product_ids": [Command.set(
        (product("THC") | product("DEM") | product("TTE-FCL") | product("FS")).ids)]}).action_add()
    check("EU customer: THC and NR services -> 0% EU S", (set(eu.order_line.mapped("boss_vat_status")),
                                                        eu.order_line.tax_ids), ({"ok"}, t_eu))
    check("EU customer: DEM is EX after the customer layer", eu.order_line.filtered(
        lambda l: l.product_id.default_code == "DEM").boss_vat_class, "EX")
    with_sales(eu).action_confirm()
    check("EU quotation accepted and frozen", (eu.state, eu.boss_pricing_frozen, len(eu.boss_snapshot_ids)), ("sale", True, 1))
    check("snapshot keeps the tax", sorted({t for v in eu.boss_snapshot_ids.data["lines"] for t in v["taxes"]}),
          sorted(set(eu.order_line.tax_ids.mapped("name"))))
    try:
        with_sales(eu.order_line[:1]).price_unit = 1.0
        check("accepted price locked", "changed", "locked")
    except UserError:
        check("accepted price locked", "locked", "locked")

    # --- air: ALM threshold / Saturday rule, HAN quantity from the AWB weight ------------------------------
    air = with_sales(env["sale.order"]).create({
        "partner_id": trial("lead_air").partner_id.id, "opportunity_id": trial("lead_air").id,
        "boss_direction": "import", "boss_transport_mode": "air", "boss_load_type": "air",
        "boss_port_id": env["boss.port"].search([("code", "=", "MAD")], limit=1).id,
        "boss_country_id": ref("base.cn").id, "boss_planned_date": date(2026, 11, 4), "boss_awb_kg": 500})
    with_sales(env["boss.add.services"]).create(
        {"order_id": air.id, "product_ids": [Command.set((product("ALM") | product("HAN")).ids)]}).action_add()
    alm = air.order_line.filtered(lambda l: l.product_id.default_code == "ALM")
    han = air.order_line.filtered(lambda l: l.product_id.default_code == "HAN")
    check("ALM without days: missing data", (alm.boss_cost_status, alm.boss_cost_missing), ("missing_input", "storage_days"))
    air.boss_storage_days = 4  # Wednesday arrival, 4 periods > 48 h: billed from day 1: 4 x 5 x 10
    check("ALM 4 periods from Wednesday", alm.boss_cost_amount, 200.0)
    air.write({"boss_planned_date": date(2026, 11, 7), "boss_storage_days": 3})  # Saturday: free until Monday
    check("ALM Saturday arrival, 3 periods", (alm.boss_cost_status, alm.boss_cost_amount), ("ok", 0.0))
    check("HAN from AWB weight (500 kg x 0.08)", (han.product_uom_qty, han.boss_cost_amount), (500.0, 40.0))
    check("HAN sale per kg: 0.08 + 15 % (kept with 3 decimals)", (han.price_unit, han.price_subtotal), (0.092, 46.0))
    # VAT by customer zone on the same air quotation: third country -> 0% EX S; Canary Islands -> pending (P17).
    Partner = env["res.partner"]
    air.partner_id = Partner.create({"name": "VERIFY cliente EEUU", "country_id": ref("base.us").id})
    check("third-country customer: ALM -> 0% EX S", (alm.boss_vat_class, alm.tax_ids),
          ("EX", tpl("account_tax_template_s_iva_e")))
    air.partner_id = Partner.create({"name": "VERIFY cliente Canarias", "country_id": ref("base.es").id,
                                     "state_id": env["res.country.state"].search([("code", "=", "GC"), ("country_id.code", "=", "ES")]).id})
    check("Canary customer: ALM pending (P17)", (alm.boss_vat_class, alm.boss_vat_status), ("EX", "pending"))
except Exception as error:  # noqa: BLE001 (report what was checked before the failure)
    checks.append((f"stopped: {type(error).__name__}", False, str(error)[:300], "no exception"))
finally:
    env.cr.rollback()

width = max(len(c[0]) for c in checks)
for label, ok, got, expected in checks:
    print(f"{'OK  ' if ok else 'FAIL'} {label.ljust(width)}  got={got!r}" + ("" if ok else f" expected={expected!r}"))
print(f"VERIFY {env.cr.dbname}: {sum(c[1] for c in checks)}/{len(checks)} checks OK (rolled back)")
