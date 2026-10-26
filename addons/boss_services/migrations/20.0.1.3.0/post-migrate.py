"""ETX, VET and DET leave «pending decision» with the rules found in the references (product records are noupdate).

- ETX (Cristina 07/10 «solo aplica a importación», 08/10 «compra por AWB máster, venta por expediente»; WFS 2026
  item 49 «Recargo de mantenimiento del servicio», 31 €/AWB, import only; Odoo 17 bills: 410 of 422 ETX lines are air
  import): priced from supplier tariffs, per master AWB (one per file).
- VET (WFS 2026 item 54: veterinarian's cost + 20 % handling; proposal of 07/10: per document like SAN): manual cost.
- DET (MSC 01/09/2026 p.10: export detention from empty pickup to full gate-in, billed on its own; Hapag includes it in
  DEM; proposal of 07/10): priced from supplier tariffs, per container and day."""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ref = env.ref
    ref("boss_services.service_etx").write({
        "boss_pricing_mode": "tariff", "boss_cost_method": "per_unit", "uom_id": ref("boss_services.uom_awb").id,
        "boss_open_question": False,
        "description": "Energy / service maintenance surcharge of the handler (WFS item 49, Swissport «tasa de "
                       "mantenimiento»): air import only, bought per master AWB, sold per file (one master AWB per "
                       "file). Cristina 07/10 and 08/10/2026."})
    ref("boss_services.service_vet").write({
        "boss_pricing_mode": "manual", "boss_cost_method": "manual",
        "description": "Veterinary inspection at the border post, per document like SAN: cost of the veterinarian + 20 % "
                       "handling of the handler (WFS item 54). Proposal of 07/10/2026 applied (P16)."})
    ref("boss_services.service_det").write({
        "boss_pricing_mode": "tariff",
        "description": "Container detention outside the terminal when the carrier bills it on its own (MSC export: "
                       "empty pickup to full gate-in); inside DEM when combined (Hapag MHD/DTD). Proposal of 07/10/2026 "
                       "applied (P09)."})
    if env["res.lang"]._lang_get("es_ES"):
        es = {
            "service_etx": "Tasa energética / recargo de mantenimiento del servicio del handler (WFS ítem 49, Swissport «tasa "
                           "de mantenimiento»): solo importación aérea, compra por AWB máster, venta por expediente (un "
                           "AWB máster por expediente). Cristina 07/10 y 08/10/2026.",
            "service_vet": "Inspección veterinaria en el PIF, por documento como SAN: coste del veterinario + 20 % de gestión "
                           "del handler (WFS ítem 54). Propuesta del 07/10/2026 aplicada (P16).",
            "service_det": "Detención del contenedor fuera de la terminal cuando la naviera la factura aparte (MSC "
                           "exportación: retirada del vacío a entrada del lleno); dentro de DEM cuando va combinada (Hapag "
                           "MHD/DTD). Propuesta del 07/10/2026 aplicada (P09).",
        }
        for xmlid, text in es.items():
            ref(f"boss_services.{xmlid}").with_context(lang="es_ES").write({"description": text})
