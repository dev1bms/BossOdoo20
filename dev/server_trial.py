"""Trial data for trying the CRM -> accepted quotation path on boss20 (odoo shell). FICTITIOUS, marked [DEMO].

Creates once (idempotent, xmlids in module `boss_trial`): a demo customer and suppliers, three demo supplier tariffs
SENT FOR APPROVAL (never approved here: approving them is the trier's step), a demo customer pricelist (agreed THC
price and a cost-based rule) and two opportunities (sea FCL and air). No quotation is created, no e-mail is sent.
CES is deliberately left without a supplier price (the 'missing price' step of the trial).
"""
import base64
from datetime import date

from odoo import Command

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname in ("boss20", "boss_test"), env.cr.dbname
env = env(context=dict(env.context, tracking_disable=True, mail_create_nosubscribe=True))
IMD = env["ir.model.data"]
MODULE = "boss_trial"
company = env.company
eur = env.ref("base.EUR")
DOC = base64.b64encode(b"%PDF-1.4\n% [DEMO] documento ficticio para la prueba guiada\n").decode()


def record(name, model, vals):
    imd = IMD.search([("module", "=", MODULE), ("name", "=", name)], limit=1)
    if imd and env[model].browse(imd.res_id).exists():
        return env[model].browse(imd.res_id)
    rec = env[model].create(vals)
    IMD.create({"module": MODULE, "name": name, "model": model, "res_id": rec.id, "noupdate": True})
    return rec


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


def uom(name):
    return env.ref(f"boss_services.uom_{name}")


spain, china = env.ref("base.es"), env.ref("base.cn")
customer = record("customer", "res.partner", {
    "name": "[DEMO] Cliente Ejemplo, S.L.", "is_company": True, "country_id": spain.id, "city": "Valencia",
    "state_id": env["res.country.state"].search([("country_id", "=", spain.id), ("code", "=", "V")]).id})
carrier = record("carrier", "res.partner", {"name": "[DEMO] Naviera Ejemplo", "is_company": True})
haulier = record("haulier", "res.partner", {"name": "[DEMO] Transportista Ejemplo", "is_company": True})
handler = record("handler", "res.partner", {"name": "[DEMO] Handler Aéreo Ejemplo", "is_company": True})
dv = env.ref("boss_pricing.container_type_dv")
valencia, madrid_air = env.ref("boss_pricing.port_esvlc"), env["boss.port"].search([("code", "=", "MAD")], limit=1)

sea_scope = {"direction": "import", "transport_mode": "sea", "load_type": "fcl", "currency_id": eur.id,
             "valid_from": date(2026, 1, 1), "valid_to": date(2026, 12, 31), "document": DOC,
             "document_name": "demo.pdf", "note": "[DEMO] Precios ficticios para la prueba guiada."}
tariffs = record("tariff_sea", "boss.tariff", {
    **sea_scope, "name": "[DEMO] Naviera Ejemplo - gastos locales importación 2026", "partner_id": carrier.id,
    "carrier_id": carrier.id, "port_ids": [Command.set(valencia.ids)],
    "document_reference": "[DEMO] Tarifa ficticia 2026",
    "line_ids": [
        Command.create({"product_id": product("THC").id, "uom_id": uom("container").id, "container_size": "20",
                        "basis": "containers", "unit_price": 150.0, "document_page": "1"}),
        Command.create({"product_id": product("THC").id, "uom_id": uom("container").id, "container_size": "40",
                        "basis": "containers", "unit_price": 200.0, "document_page": "1"}),
        Command.create({"product_id": product("DEM").id, "uom_id": uom("container").id, "method": "time",
                        "basis": "containers", "free_days": 7, "free_mode": "deduct", "tier_mode": "relative",
                        "document_page": "2", "bracket_ids": [Command.create({"up_to": 5, "unit_price": 30.0}),
                                                              Command.create({"up_to": 0, "unit_price": 60.0})]}),
    ]})
tariffs |= record("tariff_road", "boss.tariff", {
    **sea_scope, "name": "[DEMO] Transportista Ejemplo - contenedor desde Valencia 2026", "partner_id": haulier.id,
    "document_reference": "[DEMO] Tarifa ficticia 2026",
    "line_ids": [
        Command.create({"product_id": product("TTE-FCL").id, "uom_id": uom("container").id, "method": "per_unit",
                        "basis": "containers", "unit_price": 320.0, "document_page": "1"}),
        Command.create({"product_id": product("FS").id, "uom_id": uom("shipment").id, "method": "percent",
                        "percent_base": "services", "rate": 8.0, "document_page": "1",
                        "base_product_ids": [Command.set(product("TTE-FCL").ids)]}),
    ]})
tariffs |= record("tariff_air", "boss.tariff", {
    "name": "[DEMO] Handler Aéreo Ejemplo - importación 2026", "partner_id": handler.id, "currency_id": eur.id,
    "valid_from": date(2026, 1, 1), "valid_to": date(2026, 12, 31), "document": DOC, "document_name": "demo.pdf",
    "document_reference": "[DEMO] Tarifa ficticia 2026", "direction": "import", "transport_mode": "air",
    "load_type": "air", "port_ids": [Command.set(madrid_air.ids)], "note": "[DEMO] Precios ficticios.",
    "line_ids": [
        Command.create({"product_id": product("ALM").id, "uom_id": uom("shipment").id, "method": "time",
                        "basis": "awb_kg", "unit_size": 100, "round_up": True, "free_hours": 48,
                        "free_mode": "threshold", "tier_mode": "positional", "saturday_until_monday": True,
                        "min_amount": 40.0, "document_page": "1",
                        "bracket_ids": [Command.create({"up_to": 7, "unit_price": 10.0}),
                                        Command.create({"up_to": 0, "unit_price": 25.0})]}),
        Command.create({"product_id": product("HAN").id, "uom_id": uom("kg_air").id, "basis": "line",
                        "unit_price": 0.08, "min_amount": 20.0, "document_page": "1"}),
    ]})
for tariff in tariffs.filtered(lambda t: t.state == "draft"):
    tariff.action_submit()  # approval is a person's click (the trier's step)

pricelist = record("pricelist", "product.pricelist", {
    "name": "[DEMO] Cliente Ejemplo - acuerdo de precios", "currency_id": eur.id, "company_id": company.id,
    "item_ids": [
        Command.create({"applied_on": "1_product", "product_tmpl_id": product("THC").product_tmpl_id.id,
                        "uom_id": uom("container").id, "compute_price": "fixed", "fixed_price": 230.0}),
        # minimum margin is per unit of the charge basis (standard Odoo): only on per-container services here
        Command.create({"applied_on": "1_product", "product_tmpl_id": product("DEM").product_tmpl_id.id,
                        "compute_price": "markup", "base": "boss_line_cost", "price_markup": 15.0,
                        "price_min_margin": 30.0}),
        Command.create({"applied_on": "3_global", "compute_price": "markup", "base": "boss_line_cost",
                        "price_markup": 15.0}),
    ]})
customer.property_product_pricelist = pricelist
salesperson = env.ref("base.user_admin")
record("lead_sea", "crm.lead", {
    "name": "[DEMO] Importación 2x20' + 1x40'HC Shanghái - Valencia", "type": "opportunity",
    "partner_id": customer.id, "user_id": salesperson.id, "expected_revenue": 2500.0})
record("lead_air", "crm.lead", {
    "name": "[DEMO] Importación aérea 500 kg Shanghái - Madrid", "type": "opportunity",
    "partner_id": customer.id, "user_id": salesperson.id, "expected_revenue": 600.0})
env.cr.commit()
print("TRIAL", {"customer": customer.id, "tariffs": [(t.name, t.state) for t in tariffs], "pricelist": pricelist.name,
                "leads": env["crm.lead"].search([("name", "like", "[DEMO]")]).mapped("name")})
