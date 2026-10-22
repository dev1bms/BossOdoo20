"""Data for the demonstration to Ángel (odoo shell; boss20 or the local copy). ILLUSTRATIVE amounts, marked [DEMO].

Authorised by Belal (22/10/2026): [DEMO] tariffs and sale rules created AND approved here, limited to the [DEMO]
customers (tariff scope «customer»), so they never price a real quotation. The [MUESTRA] supplier tariffs (real
documents) are not touched and stay waiting for approval. Suppliers: the three existing ones (MSC, WFS, IRENEO).
The fictitious suppliers and opportunities of the earlier trial are archived (kept, not deleted). Idempotent.
"""
import base64
from datetime import date

from odoo import Command

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname
admin = env.ref("base.user_admin")
env = env(user=admin, context=dict(env.context, tracking_disable=True, mail_create_nosubscribe=True, lang="es_ES"))
ref, IMD, MODULE = env.ref, env["ir.model.data"], "boss_trial"
eur = ref("base.EUR")
DOC = base64.b64encode(b"%PDF-1.4\n% [DEMO] tarifa ilustrativa para la demostracion\n").decode()


def xid(name):
    imd = IMD.search([("module", "=", MODULE), ("name", "=", name)], limit=1)
    return env[imd.model].browse(imd.res_id) if imd else None


def record(name, model, vals):
    rec = xid(name)
    if rec and rec.exists():
        return rec
    rec = env[model].create(vals)
    IMD.create({"module": MODULE, "name": name, "model": model, "res_id": rec.id, "noupdate": True})
    return rec


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


def uom(name):
    return ref(f"boss_services.uom_{name}")


def supplier(prefix):
    partner = env["res.partner"].search([("name", "=like", f"{prefix} %")], limit=1)
    assert partner, prefix
    return partner


# 1. Earlier fictitious trial data: archived (kept).
for name in ("tariff_sea", "tariff_road", "tariff_air"):
    old = xid(name)
    if old and old.active:
        old.active = False
for name in ("carrier", "haulier", "handler", "lead_sea", "lead_air", "lead_eu"):
    old = xid(name)
    if old and old.active:
        old.active = False
for old in env["boss.tariff"].search([("name", "=like", "[DEMO] Naviera Ejemplo%")]):
    old.active = False

# 2. Customers: the [DEMO] EU customer is a business with a (fictitious, valid-format) VAT number.
customer_es, customer_eu = xid("customer"), xid("customer_eu")
if not customer_eu.vat:
    from stdnum.de import vat as de_vat  # noqa: PLC0415
    customer_eu.vat = "DE" + next(str(n) for n in range(100000000, 100010000) if de_vat.is_valid(str(n)))
msc, wfs, ireneo = supplier("MSC"), supplier("WFS"), supplier("IRENEO")
dv, hc, rf = (ref(f"boss_pricing.container_type_{c}") for c in ("dv", "hc", "rf"))
vlc = ref("boss_pricing.port_esvlc")
mad = env["boss.port"].search([("code", "=", "MAD")], limit=1)
madrid = env["res.country.state"].search([("country_id.code", "=", "ES"), ("code", "=", "M")], limit=1)
common = {"currency_id": eur.id, "valid_from": date(2026, 1, 1), "valid_to": date(2026, 12, 31), "document": DOC,
          "document_name": "demo-tarifa.pdf", "note": "[DEMO] Importes ilustrativos para la demostración."}


def msc_lines(with_bl=True):
    lines = [
        Command.create({"product_id": product("THC").id, "uom_id": uom("container").id, "container_size": "20",
                        "basis": "containers", "unit_price": 180.0, "document_page": "1"}),
        Command.create({"product_id": product("THC").id, "uom_id": uom("container").id, "container_size": "40",
                        "basis": "containers", "unit_price": 240.0, "document_page": "1"}),
        Command.create({"product_id": product("THC").id, "uom_id": uom("container").id, "container_size": "40",
                        "container_type_ids": [Command.set(rf.ids)], "basis": "containers", "unit_price": 300.0,
                        "document_page": "1"}),
        Command.create({"product_id": product("DEM").id, "uom_id": uom("container").id, "method": "time",
                        "basis": "containers", "free_days": 7, "free_mode": "deduct", "tier_mode": "relative",
                        "document_page": "2", "bracket_ids": [Command.create({"up_to": 5, "unit_price": 30.0}),
                                                              Command.create({"up_to": 0, "unit_price": 60.0})]}),
    ]
    if with_bl:
        lines.append(Command.create({"product_id": product("BL").id, "uom_id": uom("shipment").id, "basis": "line",
                                     "unit_price": 60.0, "document_page": "1"}))
    return lines


sea = {"direction": "import", "transport_mode": "sea", "load_type": "fcl", "port_ids": [Command.set(vlc.ids)]}
tariffs = record("demo_msc", "boss.tariff", {
    **common, **sea, "name": "[DEMO] MSC gastos locales importación Valencia 2026", "partner_id": msc.id,
    "carrier_id": msc.id, "customer_id": customer_eu.id, "document_reference": "[DEMO] MSC tarifa ilustrativa",
    "line_ids": msc_lines()})
tariffs |= record("demo_msc_es", "boss.tariff", {
    **common, **sea, "name": "[DEMO] MSC gastos locales importación Valencia 2026 (cliente español)",
    "partner_id": msc.id, "carrier_id": msc.id, "customer_id": customer_es.id,
    "document_reference": "[DEMO] MSC tarifa ilustrativa", "line_ids": msc_lines(with_bl=False)})
air = {"direction": "import", "transport_mode": "air", "load_type": "air", "port_ids": [Command.set(mad.ids)]}
tariffs |= record("demo_wfs", "boss.tariff", {
    **common, **air, "name": "[DEMO] WFS importación aérea Madrid 2026", "partner_id": wfs.id,
    "customer_id": customer_eu.id, "document_reference": "[DEMO] WFS tarifa ilustrativa",
    "line_ids": [
        Command.create({"product_id": product("HAN").id, "uom_id": uom("kg_air").id, "basis": "line",
                        "unit_price": 0.05, "min_amount": 20.0, "document_page": "6"}),
        Command.create({"product_id": product("ALM").id, "uom_id": uom("shipment").id, "method": "time",
                        "basis": "awb_kg", "unit_size": 100, "round_up": True, "free_hours": 48,
                        "free_mode": "threshold", "tier_mode": "positional", "saturday_until_monday": True,
                        "min_amount": 40.0, "document_page": "5",
                        "bracket_ids": [Command.create({"up_to": 7, "unit_price": 10.0}),
                                        Command.create({"up_to": 0, "unit_price": 25.0})]}),
        Command.create({"product_id": product("AWB").id, "uom_id": uom("awb").id, "basis": "line",
                        "unit_price": 30.0, "document_page": "6"}),
    ]})
tariffs |= record("demo_ireneo", "boss.tariff", {
    **common, "name": "[DEMO] IRENEO distribución desde Barajas 2026", "partner_id": ireneo.id,
    "customer_id": customer_eu.id, "direction": "import", "transport_mode": "air",
    "state_ids": [Command.set(madrid.ids)], "document_reference": "[DEMO] IRENEO tarifa ilustrativa",
    "line_ids": [
        Command.create({"product_id": product("TTE-CON").id, "uom_id": uom("shipment").id, "method": "brackets",
                        "basis": "chargeable_kg", "volumetric_factor": 333, "floor_previous": True,
                        "document_page": "7", "bracket_ids": [
                            Command.create({"up_to": 100, "fixed_amount": 45.0}),
                            Command.create({"up_to": 500, "unit_price": 0.20}),
                            Command.create({"up_to": 1000, "unit_price": 0.15})]}),
        Command.create({"product_id": product("FS").id, "uom_id": uom("shipment").id, "method": "percent",
                        "percent_base": "services", "rate": 5.0, "document_page": "16",
                        "base_product_ids": [Command.set(product("TTE-CON").ids)]}),
    ]})
for tariff in tariffs:
    if tariff.state == "draft":
        tariff.action_submit()
    if tariff.state == "to_approve":
        tariff.action_approve()  # [DEMO] only, authorised for this demonstration

# 3. Sale rules of the [DEMO] customers' agreement.
pricelist = xid("pricelist")
pricelist.item_ids.unlink()
pricelist.write({"name": "[DEMO] Acuerdo de precios de los clientes de demostración", "item_ids": [
    Command.create({"applied_on": "1_product", "product_tmpl_id": product("THC").product_tmpl_id.id,
                    "uom_id": uom("container").id, "compute_price": "fixed", "fixed_price": 280.0}),
    Command.create({"applied_on": "1_product", "product_tmpl_id": product("BL").product_tmpl_id.id,
                    "compute_price": "markup", "base": "boss_line_cost", "boss_sale_margin": 20.0}),
    Command.create({"applied_on": "1_product", "product_tmpl_id": product("DEM").product_tmpl_id.id,
                    "compute_price": "markup", "base": "boss_line_cost", "price_markup": 15.0,
                    "price_min_margin": 30.0}),
    Command.create({"applied_on": "1_product", "product_tmpl_id": product("ARA").product_tmpl_id.id,
                    "compute_price": "markup", "base": "boss_line_cost", "price_markup": 0.0}),
    Command.create({"applied_on": "3_global", "compute_price": "markup", "base": "boss_line_cost",
                    "price_markup": 15.0}),
]})
(customer_es | customer_eu).property_product_pricelist = pricelist


# 4. Opportunities and saved quotations.
def lead(name, partner, title):
    return record(name, "crm.lead", {"name": title, "type": "opportunity", "partner_id": partner.id,
                                     "user_id": admin.id})


def quotation(name, opportunity, values, lines):
    order = xid(name)
    if order and order.exists():
        return order
    order = env["sale.order"].create({"partner_id": opportunity.partner_id.id, "opportunity_id": opportunity.id,
                                      "origin": opportunity.name, **values})
    IMD.create({"module": MODULE, "name": name, "model": "sale.order", "res_id": order.id, "noupdate": True})
    for codes, vendor in lines:
        env["boss.add.services"].create({"order_id": order.id, "supplier_id": vendor.id, "product_ids": [
            Command.set(env["product.product"].search([("default_code", "in", codes)]).ids)]}).action_add()
    return order


day = date(2026, 11, 4)  # Wednesday, inside the [DEMO] validity
lead_msc = lead("demo_lead_msc", customer_eu, "[DEMO] MSC · Importación 1x20' + 1x40'HC Shanghái - Valencia (cliente UE)")
q_msc = quotation("demo_q_msc", lead_msc, {
    "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": msc.id,
    "boss_port_id": vlc.id, "boss_country_id": ref("base.cn").id, "boss_planned_date": day, "boss_storage_days": 10,
    "boss_container_ids": [Command.create({"size": "20", "container_type_id": dv.id, "quantity": 1}),
                           Command.create({"size": "40", "container_type_id": hc.id, "quantity": 1})]},
    [(["THC", "BL", "DEM"], msc)])
if q_msc.state == "draft" and not q_msc.order_line.filtered(lambda l: l.product_id.default_code == "ARA"):
    env["boss.add.services"].create({"order_id": q_msc.id, "product_ids": [Command.set(product("ARA").ids)]}).action_add()
    q_msc.order_line.filtered(lambda l: l.product_id.default_code == "ARA").write(
        {"boss_manual_cost": 350.0, "boss_manual_cost_note": "[DEMO] DUA 26ES00000000001"})
lead_wfs = lead("demo_lead_wfs", customer_eu, "[DEMO] WFS · Importación aérea 500 kg Shanghái - Madrid (cliente UE)")
q_wfs = quotation("demo_q_wfs", lead_wfs, {
    "boss_direction": "import", "boss_transport_mode": "air", "boss_load_type": "air", "boss_port_id": mad.id,
    "boss_country_id": ref("base.cn").id, "boss_planned_date": day, "boss_awb_kg": 500.0},
    [(["HAN", "ALM", "AWB"], wfs)])
q_wfs.order_line.filtered(lambda l: l.product_id.default_code == "ALM").write(
    {"boss_days_source": "estimate", "boss_days": 4})
lead_ire = lead("demo_lead_ireneo", customer_eu, "[DEMO] IRENEO · Entrega en Madrid de carga aérea 450 kg (cliente UE)")
q_ire = quotation("demo_q_ireneo", lead_ire, {
    "boss_direction": "import", "boss_transport_mode": "air", "boss_load_type": "air", "boss_port_id": mad.id,
    "boss_country_id": ref("base.cn").id, "boss_inland_state_id": madrid.id, "boss_planned_date": day,
    "boss_gross_kg": 450.0, "boss_volume_m3": 1.0}, [(["TTE-CON", "FS"], ireneo)])
q_ire.order_line.filtered(lambda l: l.product_id.default_code == "TTE-CON" and l.product_uom_id != uom("shipment")).write(
    {"product_uom_id": uom("shipment").id})  # road transport priced per shipment on the chargeable weight
lead_es = lead("demo_lead_es", customer_es, "[DEMO] Conflicto de IVA · cliente español 1x40'HC Shanghái - Valencia")
q_es = quotation("demo_q_es", lead_es, {
    "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl", "boss_carrier_id": msc.id,
    "boss_port_id": vlc.id, "boss_country_id": ref("base.cn").id, "boss_planned_date": day, "boss_storage_days": 10,
    "boss_container_ids": [Command.create({"size": "40", "container_type_id": hc.id, "quantity": 1})]},
    [(["THC", "DEM"], msc)])
lead("demo_lead_live", customer_eu, "[DEMO] Reunión · nueva oferta MSC 2x40'HC Shanghái - Valencia (cliente UE)")
if q_msc.state == "draft":
    q_msc.action_confirm()  # accepted example: frozen prices and snapshot
env.cr.commit()


def show(order):
    print(f"QUOTE {order.name} id={order.id} state={order.state} total={order.amount_untaxed} margin={order.margin}")
    for l in order.order_line:
        print(f"   {l.product_id.default_code:8} {l.boss_container_size or '':3} qty={l.product_uom_qty:g} "
              f"cost={l.boss_cost_status}:{l.boss_cost_amount} unit_cost={l.purchase_price} sale={l.price_unit} "
              f"[{l.boss_sale_status}] vat={l.boss_vat_class}/{l.boss_vat_status} {l.tax_ids.mapped('name')}")


for order in (q_msc, q_wfs, q_ire, q_es):
    show(order)
print("LEADS", env["crm.lead"].search([("name", "=like", "[DEMO]%")]).mapped(lambda r: (r.id, r.name)))
print("TARIFFS", [(t.id, t.name, t.state) for t in tariffs])
