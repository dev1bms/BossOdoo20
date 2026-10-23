"""[DEMO] examples of the operational cycle (odoo shell; boss20 or the local copy). Idempotent.

Built only on [DEMO] customers and [DEMO] tariffs. The quotations shown in the guide (S00010, S00011) are not
changed: each example is a repeat of them. Nothing is posted, confirmed to a supplier or sent: purchase orders stay
as RFQs (drafts) and customer invoices as drafts; the server has no outgoing mail. Posting, credit notes and the
accounting effects are verified on the throw-away test database (boss_expediente tests).

    1. MSC sea import (accepted S00009): file, RFQ to MSC, draft invoice of the THC only (milestone), extra cost
       of port occupancy re-invoiced to the customer with a reason.
    2. WFS air import (repeat of S00010): file, RFQ to WFS for handling and storage.
    3. IRENEO road delivery (repeat of S00011): file, RFQ to IRENEO.
    4. BOSS own service only (CSM): file without purchases, margin after external costs = sale.
"""
from datetime import date

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


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


customer_es, customer_eu = xid("customer"), xid("customer_eu")
assert customer_eu.boss_demo and customer_es.boss_demo, "demo customers only"
# fictitious addresses: a complete invoice needs the customer's address and tax ID
if not customer_eu.street:
    customer_eu.write({"street": "Beispielstraße 1 [DEMO]", "zip": "20095"})
if not customer_es.street:
    customer_es.write({"street": "Calle Ejemplo 1 [DEMO]", "zip": "46001"})


def accept(name, source):
    """Repeat of a [DEMO] quotation, with the demo sale prices of the source where the copy has none, accepted."""
    order = xid(name)
    if order and order.state == "sale":
        return order
    if order:
        order.action_boss_update_costs()
    else:
        order = source.copy()
        remember(name, order)
    for line, origin in zip(order.order_line, source.order_line):
        if line.boss_sale_status == "missing" and origin.price_unit:
            line.price_unit = origin.price_unit
    try:
        order.action_confirm()
    except Exception as exc:  # noqa: BLE001 (report and keep the quotation for the demo)
        print("NOT ACCEPTED", order.name, " ".join(str(exc).split())[:300])
    return order


def rfqs(file):
    if file.cost_ids.filtered(lambda n: n.state == "to_order"):
        file.action_create_rfqs()


# 1. MSC sea import: the accepted demo quotation gets its file.
msc_order = xid("demo_q_msc")
msc_order._boss_open_files()
msc_file = remember("demo_file_msc", msc_order.boss_expediente_id)
if not msc_file.booking_ref:
    msc_file.write({"booking_ref": "[DEMO] BKG-0001", "mbl_ref": "[DEMO] MEDU0000001", "vessel": "[DEMO] MSC EJEMPLO",
                    "voyage": "DEMO1", "etd": date(2026, 10, 1), "eta": date(2026, 11, 2)})
    for number, row in zip(("MSCU0000010", "MSCU0000020"), msc_file.container_ids):
        row.number = f"{number} [DEMO]"
rfqs(msc_file)
if not msc_order.invoice_ids:
    thc = msc_order.order_line.filtered(lambda l: l.product_id.default_code == "THC")
    env["boss.invoice.services"].create({"expediente_id": msc_file.id, "order_ids": [Command.set(msc_order.ids)],
                                         "line_ids": [Command.set(thc.ids)]}).action_create()
extra = xid("demo_extra_msc")
if not extra:
    msc = msc_order.boss_carrier_id
    extra = remember("demo_extra_msc", env["boss.expediente.cost"].create({
        "expediente_id": msc_file.id, "product_id": product("OCU").id, "name": "[DEMO] Ocupación de muelle extra",
        "uom_id": product("OCU").uom_id.id, "quantity": 1, "partner_id": msc.id, "currency_id": msc_file.currency_id.id,
        "expected_unit_cost": 120.0, "extra_class": "approval",
        "reason": "[DEMO] El cliente retiró el contenedor 3 días tarde"}))
if not extra.rebill_line_id:
    env["boss.rebill.wizard"].with_context(default_cost_id=extra.id).create({
        "price_unit": 160.0, "reason": "[DEMO] Cliente acepta pagar la ocupación extra (correo 23/10)"}).action_apply()
rfqs(msc_file)

# 2. WFS air import, 3. IRENEO road delivery: repeats of the demo quotations of the guide.
wfs_order = accept("demo_q_wfs_cycle", xid("demo_q_wfs"))
ireneo_order = accept("demo_q_ireneo_cycle", xid("demo_q_ireneo"))
for order, name in ((wfs_order, "demo_file_wfs"), (ireneo_order, "demo_file_ireneo")):
    if order.boss_expediente_id:
        remember(name, order.boss_expediente_id)
        rfqs(order.boss_expediente_id)

# 4. A BOSS own service only.
own = xid("demo_q_own")
if not own:
    own = remember("demo_q_own", env["sale.order"].create({
        "partner_id": customer_eu.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
        "boss_port_id": env.ref("boss_pricing.port_esvlc").id, "boss_country_id": env.ref("base.cn").id,
        "boss_planned_date": date(2026, 11, 16), "origin": "[DEMO] Solo consignación BOSS"}))
    env["boss.add.services"].create({"order_id": own.id, "product_ids": [Command.set(product("CSM").ids)]}).action_add()
    own.order_line.price_unit = 90.0
    own.action_confirm()
if own.boss_expediente_id:
    remember("demo_file_own", own.boss_expediente_id)

for name in ("demo_file_msc", "demo_file_wfs", "demo_file_ireneo", "demo_file_own"):
    file = xid(name)
    if not file:
        print("NO FILE", name)
        continue
    print(f"FILE {file.name} ({name}) orders={file.sale_order_ids.mapped('name')} "
          f"rfqs={[(p.name, p.partner_id.name, p.state, p.amount_untaxed, p.currency_id.name) for p in file.purchase_order_ids]}"
          f" invoices={[(m.state, m.amount_untaxed) for m in file.invoice_ids]}")
    print("   needs", [(n.product_id.default_code, n.partner_id.name, n.quantity, n.uom_id.name, n.expected_unit_cost,
                        n.currency_id.name, n.state) for n in file.cost_ids])
    print(f"   sale={file.amount_sale} accepted cost={file.amount_cost_accepted} forecast cost={file.amount_cost_forecast}"
          f" margin={file.amount_margin_forecast} to do={file.completeness!r}")
env.cr.commit()
