"""Approve on boss20 the supplier tariffs whose document proves price, calculation, validity and scope (Belal's
delegation of 27/10/2026 for development and trials). Each one was checked line by line against its document on 27/10
(private reports .research/verify_sea.md and verify_air.md; WFS items 10, 12, 49 and IRENEO p.16-17 re-read by hand).
The fixes the documents require are applied first (tariff back to draft, fix, sent again). The approval is recorded in
the chatter as Belal's delegation for trials: it is not a decision of Cristina or Ángel. Idempotent.
Not approved here (no source for an essential part): MSC FuelEU Far East (country list is a proposal, P24).
    dev/server_shell.sh approve_verified_tariffs.py"""
from datetime import date

from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=False))  # noqa: F821
belal = env["res.users"].search([("login", "=", "devbms")])
assert belal.has_group("boss_pricing.group_tariff_approver"), belal.login
Tariff = env["boss.tariff"].with_user(belal)
DELEGATION = ("Activada el 27/10/2026 para desarrollo y pruebas en boss20 por delegación de Belal, tras comprobar el "
              "documento línea a línea. No es una aprobación de Cristina ni de Ángel. Comprobación: {}")


def drop_lines(codes):
    def fix(tariff):
        lines = tariff.line_ids.filtered(lambda l: l.product_id.default_code in codes)
        lines.unlink()
        return f"quitadas las líneas {', '.join(codes)} ({len(lines)})"
    return fix


def sea_ports_without_canaries(tariff):
    ports = env["boss.port"].search([("code", "in", ["ESALG", "ESBCN", "ESBIO", "ESVGO", "ESVLC"])])
    tariff.port_ids = [Command.set(ports.ids)]
    return "alcance: puertos de la península (el documento dice «all ports (excluding Canary islands)»)"


def end_may_2026(tariff):
    tariff.valid_to = date(2026, 5, 31)
    return ("fin de vigencia 31/05/2026: Leroy anunció la licitación 2026-2027 para ETD desde el 01/06/2026 (correo "
            "«NUEVOS THC TENDER 2026 - 2027», 08/06/2026); no hay hoja de demoras y ocupaciones 2026-27")


# name (exact) -> (evidence, fix or None)
CHECKS = {
    "[MUESTRA] MSC gastos locales importación (origen China) 09-12/2026": (
        "MSC «DRY - Gastos Locales 2026» 01/09-31/12/2026, p.12 y p.18: 10 líneas iguales al documento.", None),
    "[MUESTRA] MSC ocupación importación Valencia 09-12/2026": (
        "MSC gastos locales p.17, tramos de ocupación 20'DV/40'DV iguales. El 40'HC no tiene columna (pendiente A5).", None),
    "[MUESTRA] MSC ocupación importación Barcelona 09-12/2026": (
        "MSC gastos locales p.17, tramos iguales. El 40'HC no tiene columna (pendiente A5).", None),
    "[MUESTRA] Hapag-Lloyd demoras+detención importación (MHD/DTD)": (
        "Hapag-Lloyd «SPAIN - Import» efectiva 01/10/2025 «until further notice», p.1 MHD/DTD: precios iguales.",
        sea_ports_without_canaries),
    "[MUESTRA] CMA CGM demoras+detención importación Standard": (
        "CMA CGM «D&D Tariffs Spain» efectiva 01/03/2025, p.1: precios iguales.", None),
    "[MUESTRA] ADUCEX, S.L. FAD importación FCL (Cristina 28/09/2026)": (
        "Respuesta de Cristina 28/09/2026 (Plan detallado previsiones, Explicaciones A116): un importe con 1 contenedor y otro con 2 o más.",
        None),
    "[MUESTRA] RAMOS VILA, S.L. FAD importación FCL (Cristina 28/09/2026)": (
        "Respuesta de Cristina 28/09/2026 (Explicaciones A36): importe base + importe por contenedor adicional, con tope.", None),
    "[MUESTRA] WFS importación MAD/BCN desde 01/06/2026": (
        "WFS «Tarifas de servicios de carga» V 2026-02 desde 01/06/2026: punto 1 almacenaje p.5, punto 10 DATA/DOCS "
        "p.6, punto 12 manipulación p.6, punto 49 recargo p.10.", None),
    "[MUESTRA] WFS exportación PNS MAD/BCN desde 01/06/2026": (
        "WFS V 2026-02: almacenaje exportación p.5, manipulación p.6, rayos X por tramos.", None),
    "[MUESTRA] IRENEO MAD recogidas en terminal 2025": ("IRENEO «Tarifas MAD 2025» p.7 (por kg tasable, 1 m³ = 333 kg, con mínimo).", None),
    "[MUESTRA] IRENEO MAD recogidas en terminal 2026 (precios 2025)": (
        "Mismos precios que 2025 p.7 (Ángel 14/10/2026: los precios 2025 siguen en 2026; la carta de 14/07 solo sube el "
        "transporte).", None),
    "[MUESTRA] IRENEO MAD exportación Barajas 2025": ("IRENEO 2025 p.4 (15 tramos) y p.5 (rayos X).", None),
    "[MUESTRA] IRENEO MAD exportación Barajas 2026 (precios 2025)": ("Iguales a 2025 p.4-5 (Ángel 14/10/2026).", None),
    "[MUESTRA] IRENEO distribución nacional zona 3 2025": (
        "IRENEO 2025 p.6 columna zona 3, 28 filas iguales; p.16: el seguro del grupaje nacional va «incluido en tarifa».",
        drop_lines(["SEG"])),
    "[MUESTRA] IRENEO distribución nacional zona 3 2026 hasta 14/07 (precios 2025)": (
        "Iguales a 2025 (Ángel 14/10/2026); p.16: seguro del grupaje nacional incluido.", drop_lines(["SEG"])),
    "[MUESTRA] IRENEO distribución nacional zona 3 2026 (+10 % transporte, carta 14/07/2026)": (
        "2025 + 10 % en las 28 filas de transporte (carta IRENEO 14/07/2026, RDL 9/2026, desde 15/07/2026); p.16: seguro "
        "del grupaje nacional incluido.", drop_lines(["SEG"])),
}
LEROY = Tariff.search([("name", "=like", "[MUESTRA] % demoras y ocupaciones importación % (licitación Leroy Merlin 2025/2026)")])
for t in LEROY:
    CHECKS[t.name] = ("Licitación Leroy Merlin 2025/2026, hoja «DEMORAS Y OCUPACIONES», todas las celdas iguales; solo "
                      "para el cliente Leroy Merlin.", end_may_2026)

for name, (evidence, fix) in CHECKS.items():
    tariff = Tariff.search([("name", "in", [name, name.replace("[MUESTRA] ", "", 1)])], limit=1)
    if not tariff:
        print("NOT FOUND", name)
        continue
    if tariff.state == "approved":
        print("ALREADY", tariff.name)
        continue
    done = ""
    if fix:
        tariff.action_back_to_draft()
        done = fix(tariff)
        tariff.scope_confirmed = True  # scope checked against the document above (a scope change clears it)
        tariff.action_submit()
    tariff.action_approve()
    tariff.name = name.replace("[MUESTRA] ", "", 1)
    tariff.message_post(body=DELEGATION.format(evidence + (f" Corrección: {done}." if done else "")))
    print("APPROVED", tariff.id, tariff.name, tariff.state, done)
wfs = env["boss.tariff"].search([("name", "=", "WFS importación MAD/BCN desde 01/06/2026")])
if wfs and "no modelado" in (wfs.note or ""):  # the Friday/Saturday free time is set on the storage line since 23/10
    wfs.note = ("Base de cálculo: peso cargable de la AWB (el documento no da factor). Almacenaje: 48 h libres desde el "
                "NOA; llegada en viernes retirada el lunes: 72 h; llegada en sábado: libre hasta el lunes (en la línea).")
pending = env["boss.tariff"].search([("is_demo", "=", False), ("state", "!=", "approved")])
print("NOT APPROVED:", [(t.id, t.name, t.state) for t in pending])
env.cr.commit()
