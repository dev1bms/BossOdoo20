"""Verify the trial path on boss20 as real roles, WITHOUT changing the database (odoo shell; everything rolled back).

A salesperson (sales + tariff entry) and an approver (sales manager + tariff approver) are created inside the
transaction. Steps: approve the [DEMO] tariffs -> quotation from the [DEMO] opportunity -> shipment data -> add
services -> cost per line -> missing price added from the quotation and approved -> sale price from the customer
agreement -> send blocked while VAT is pending -> (temporary VAT mapping, only to prove acceptance) -> accept ->
frozen + snapshot. Air quotation: ALM threshold and Saturday rule, HAN from the AWB weight. No e-mail is sent.
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
    try:
        with_sales(order).action_quotation_send()
        check("send blocked while VAT pending", "sent", "blocked")
    except UserError as error:
        check("send blocked while VAT pending", order.order_line[:1].boss_vat_trace in str(error), True)
        print("BLOCK MESSAGE:", " | ".join(str(error).splitlines())[:400])
    # Temporary VAT mapping (rolled back): ONLY to prove that the path completes once Ángel maps the taxes.
    sale_taxes = env["account.tax"].search([("type_tax_use", "=", "sale"), ("company_id", "=", order.company_id.id)], limit=3)
    order.company_id.sudo().write({"boss_tax_nr_id": sale_taxes[0].id, "boss_tax_ex_id": sale_taxes[1].id,
                            "boss_tax_ns_id": sale_taxes[2].id})
    order.order_line._boss_recompute_cost()
    env.add_to_compute(order.order_line._fields["boss_vat_status"], order.order_line)
    order.order_line._recompute_recordset(["boss_vat_status", "tax_ids"])
    with_sales(order).action_confirm()
    check("accepted and frozen", (order.state, order.boss_pricing_frozen, len(order.boss_snapshot_ids)), ("sale", True, 1))
    try:
        with_sales(line("THC", "40")).price_unit = 1.0
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
except Exception as error:  # noqa: BLE001 (report what was checked before the failure)
    checks.append((f"stopped: {type(error).__name__}", False, str(error)[:300], "no exception"))
finally:
    env.cr.rollback()

width = max(len(c[0]) for c in checks)
for label, ok, got, expected in checks:
    print(f"{'OK  ' if ok else 'FAIL'} {label.ljust(width)}  got={got!r}" + ("" if ok else f" expected={expected!r}"))
print(f"VERIFY {env.cr.dbname}: {sum(c[1] for c in checks)}/{len(checks)} checks OK (rolled back)")
