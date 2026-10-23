"""[DEMO] airport storage (ALM) cycle (odoo shell; boss20 or the local test copy). Idempotent.

Fictitious handler, customer and prices only, shaped like the WFS tariff (per 100 kg and 24 hours, 48 h free as a
threshold, Friday with a Monday exit 72 h, Saturday free until Monday included, the open readings P29/P40/P41 'not
decided'). Nothing is posted or sent: the purchase stays an RFQ (draft). Posting, credit notes and the bill comparison
are verified on the throw-away test database (boss_expediente test_storage_period).

    1. Quotation with an estimate of 3 days from a Friday arrival: estimated cost, the Friday exception not assumed.
    2. Accepted -> file. Actual period Fri 16/10 09:00 -> Mon 19/10 08:00 (free), then 10:00 (4 periods), RFQ.
    3. The stay goes on until Mon 26/10 10:00: the open readings differ -> not priced, both amounts kept.
    4. A second quotation of 10 days: «Not priced automatically» on the quotation itself.
"""
import base64
from datetime import date, datetime

from odoo import Command

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname
admin = env.ref("base.user_admin")
env = env(user=admin, context=dict(env.context, tracking_disable=True, mail_create_nosubscribe=True, lang="es_ES"))
IMD, MODULE = env["ir.model.data"], "boss_trial"


def xid(name):
    imd = IMD.search([("module", "=", MODULE), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id).exists() if imd else None


def remember(name, rec):
    if not xid(name):
        IMD.create({"module": MODULE, "name": name, "model": rec._name, "res_id": rec.id, "noupdate": True})
    return rec


def madrid(day, hour, minute=0):
    """Odoo datetime (UTC) of a Madrid time in October 2026 (CEST until Sunday 25, then CET)."""
    return datetime(2026, 10, day, hour - (2 if day < 25 else 1), minute)


if env.cr.dbname == "boss_test" and not env["boss.vat.tax"].search_count([]):
    # throw-away local copy only: fictitious taxes standing for the BOSS VAT table of the server
    Tax = env["account.tax"]
    taxes = {k: Tax.create({"name": f"[DEMO] IVA {k}", "amount": rate, "type_tax_use": "sale"})
             for k, rate in (("NR", 21.0), ("EX", 0.0), ("NS", 0.0))}
    env["boss.vat.tax"].create([{"vat_class": k, "tax_id": t.id} for k, t in taxes.items()])
Partner = env["res.partner"]
customer = xid("customer_eu") or xid("demo_alm_customer")
if not customer:
    customer = remember("demo_alm_customer", Partner.create({
        "name": "[DEMO] Cliente ALM Ejemplo S.L.", "is_company": True, "country_id": env.ref("base.es").id,
        "boss_demo": True, "boss_is_customer": True, "vat": "ESA00000000", "street": "Calle Ejemplo 1 [DEMO]",
        "city": "Madrid", "zip": "28001"}))
assert customer.commercial_partner_id.boss_demo, "demo customers only"
handler = xid("demo_alm_handler") or remember("demo_alm_handler", Partner.create(
    {"name": "[DEMO] Handler aéreo ALM", "is_company": True, "boss_is_supplier": True}))
alm = env["product.product"].search([("default_code", "=", "ALM")], limit=1)
mad = env.ref("boss_pricing.port_esmad_air")

# Tariff: demo only (prices demo customers only), approved here because it is fictitious.
tariff = xid("demo_alm_tariff")
if not tariff:
    tariff = remember("demo_alm_tariff", env["boss.tariff"].create({
        "name": "[DEMO] Handler ALM 2026 (lecturas sin decidir)", "partner_id": handler.id, "is_demo": True,
        "currency_id": env.company.currency_id.id, "valid_from": date(2026, 1, 1), "valid_to": date(2026, 12, 31),
        "direction": "import", "transport_mode": "air", "port_ids": [Command.set(mad.ids)], "scope_confirmed": True,
        "document": base64.b64encode(b"%PDF-1.4 [DEMO] tarifa ficticia de handler").decode(),
        "document_name": "demo_handler_alm.pdf", "document_reference": "[DEMO] Tarifa ficticia 2026",
        "line_ids": [Command.create({
            "product_id": alm.id, "uom_id": alm.uom_id.id, "method": "time", "basis": "awb_kg", "unit_size": 100,
            "round_undecided": True, "period_unit": "undecided", "free_hours": 48, "free_mode": "threshold",
            "friday_monday_free": 72, "saturday_until_monday": True, "tier_mode": "undecided", "min_amount": 40,
            "document_page": "1", "note": "[DEMO] precios ficticios con la estructura de WFS p.5 punto 1",
            "bracket_ids": [Command.create({"up_to": 7, "unit_price": 10}),
                            Command.create({"up_to": 0, "unit_price": 25})]})],
    }))
    tariff.action_submit()
    tariff.action_approve()


def quotation(name, days, price):
    order = xid(name)
    if order:
        return order
    order = remember(name, env["sale.order"].create({
        "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "air", "boss_load_type": "air",
        "boss_port_id": mad.id, "boss_country_id": env.ref("base.cn").id, "boss_awb_kg": 500, "boss_gross_kg": 480,
        "boss_volume_m3": 2.5, "boss_planned_date": date(2026, 10, 16), "boss_storage_days": days,
        "client_order_ref": "[DEMO] ALM"}))
    env["boss.add.services"].create({"order_id": order.id, "product_ids": [Command.set(alm.ids)]}).action_add()
    line = order.order_line.filtered(lambda l: l.product_id == alm)
    line.write({"boss_supplier_id": handler.id, "price_unit": price})
    return order


# 1-2. Quotation (3 days estimated from a Friday), accepted, actual period on the file.
order = quotation("demo_alm_q", 3, 180.0)
if order.state != "sale":
    order.action_confirm()
order._boss_open_files()
file = remember("demo_alm_file", order.boss_expediente_id)
need = file.cost_ids.filtered(lambda n: n.product_id == alm)
steps = [
    (madrid(19, 8), "[DEMO] Retirada real lunes 19/10 08:00 (71 h, viernes a lunes)"),
    (madrid(19, 10), "[DEMO] Retirada real lunes 19/10 10:00 (73 h)"),
]
if not need.revision_ids:
    need.period_start = madrid(16, 9)
    for end, reason in steps:
        need.period_end = end
        file.with_context(boss_reason=reason).action_recompute_costs()
    if need.state == "to_order":
        file.action_create_rfqs()
    # 3. the stay goes on: the readings not decided differ (day by day / whole stay)
    need.period_end = madrid(26, 10)
    file.with_context(boss_reason="[DEMO] La mercancía sigue hasta el lunes 26/10 10:00").action_recompute_costs()

# 4. A quotation of 10 days: not priced automatically on the quotation itself.
long_stay = quotation("demo_alm_q_long", 10, 0.0)

env.cr.commit()
line = order.order_line.filtered(lambda l: l.product_id == alm)
print("QUOTATION", order.id, order.name, order.state, line.boss_cost_status, line.boss_cost_amount, line.price_unit)
print("FILE", file.id, file.name, "need", need.id, need.state, need.days, need.expected_amount,
      need.period_start, need.period_end, "rfq", file.purchase_order_ids.mapped("name"))
for rev in need.revision_ids.sorted("id"):
    print("  REV", rev.id, rev.status, rev.applied, rev.old_amount, "->", rev.new_amount, rev.reason)
long_line = long_stay.order_line.filtered(lambda l: l.product_id == alm)
print("LONG", long_stay.id, long_stay.name, long_line.boss_cost_status)
print("TARIFF", tariff.id, tariff.name, tariff.state)
