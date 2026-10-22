"""Acceptance of the «Tarifas y proveedores» workspace (odoo shell; boss20). ILLUSTRATIVE, marked [DEMO].

Creates three DRAFT [DEMO] tariff headers (supplier, currency, scope and a fictitious PDF copied from the [DEMO]
demonstration tariffs, without customer restriction) so that prices are entered in the interface; nothing is
approved here. Idempotent. Also lists open quotation lines without a supplier price (read only).
"""
import base64
from datetime import date

DOC = base64.b64encode(b"%PDF-1.4\n% [DEMO] tarifa ilustrativa (espacio de trabajo)\n").decode()
SOURCES = {
    "[DEMO] MSC gastos locales importación Valencia 2026": "[DEMO] MSC ampliación espacio de trabajo 2026",
    "[DEMO] WFS importación aérea Madrid 2026": "[DEMO] WFS ampliación espacio de trabajo 2026",
    "[DEMO] IRENEO distribución desde Barajas 2026": "[DEMO] IRENEO ampliación espacio de trabajo 2026",
}
# second MSC draft: target of «Add supplier price» from a quotation (UX acceptance of 22/10/2026)
EXTRA = {"[DEMO] MSC gastos locales importación Valencia 2026": "[DEMO] MSC precios añadidos desde ofertas 2026"}
SCOPE = ("partner_id", "currency_id", "direction", "transport_mode", "load_type", "carrier_id", "port_ids",
         "country_ids", "state_ids")
Tariff = env["boss.tariff"]
for source_name, name in list(SOURCES.items()) + list(EXTRA.items()):
    source = Tariff.search([("name", "=", source_name)], limit=1)
    assert source, source_name
    tariff = Tariff.search([("name", "=", name)], limit=1)
    if not tariff:
        values = source._convert_to_write({f: source[f] for f in SCOPE})
        tariff = Tariff.create({**values, "name": name, "valid_from": date(2026, 10, 1),
                                "valid_to": date(2026, 12, 31), "document": DOC,
                                "document_name": "demo-espacio.pdf",
                                "document_reference": "[DEMO] tarifa ilustrativa espacio de trabajo",
                                "is_demo": True,
                                "note": "[DEMO] Importes ilustrativos (prueba del espacio de trabajo)."})
    print(tariff.id, tariff.name, tariff.state, tariff.partner_id.name, len(tariff.line_ids))

for line in env["sale.order.line"].search([("order_id.state", "in", ("draft", "sent")),
                                           ("boss_cost_status", "=", "no_tariff")]):
    print("no price:", line.order_id.name, line.order_id.id, line.id, line.product_id.default_code,
          line.boss_supplier_id.name, line.order_id.partner_id.name)
env.cr.commit()
