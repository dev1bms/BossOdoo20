"""IRENEO 2026 as ONE supplier document (ADR-002 amendment, Belal 27/10/2026): the sections that were separate tariffs
become prices of one tariff «IRENEO Tarifas MAD 2026», each price with the scope of its section. Prices are copied from
the tariffs already checked against «TARIFAS MAD 2025.pdf» and the letter of 14/07/2026 (no amount in this script).
    dev/server_shell.sh setup_ireneo_2026_document.py
Stage 1 (version 1 missing): draft from 01/01/2026 at 2025 prices with
  terminal pickups (import · air) · Barajas export package and X-ray (export · air) · zone-3 distribution (its 15
  provinces) · G-5 storage (import · air · MAD, «On request» until IRENEO says how its free days work).
  The export storage of p.4 is added from the user interface (test of the line scope in Chrome), then the tariff is
  sent for approval and approved.
Stage 2 (version 1 approved, no version 2): new version from 15/07/2026 with the zone-3 transport +10 % (letter of
  14/07/2026, as its document), sent and approved under Belal's delegation for trials; the separate 2026 section tariffs
  are archived (their quotations keep showing them). The 2025 tariffs stay as history. Idempotent."""
from datetime import date

from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=False))  # noqa: F821
Tariff = env["boss.tariff"].with_context(active_test=False)
NAME = "IRENEO Tarifas MAD 2026"
belal = env["res.users"].search([("login", "=", "devbms")])
OLD = {  # section tariffs of 2026 that the document replaces
    "pickup": "IRENEO MAD recogidas en terminal 2026 (precios 2025)",
    "export": "IRENEO MAD exportación Barajas 2026 (precios 2025)",
    "zone3_jan": "IRENEO distribución nacional zona 3 2026 hasta 14/07 (precios 2025)",
    "zone3_jul": "IRENEO distribución nacional zona 3 2026 (+10 % transporte, carta 14/07/2026)",
    "g5": "[MUESTRA] IRENEO almacén G-5 (ADT) importación MAD 2026 (precios 2025)",
}
old = {key: Tariff.search([("name", "=", name)], limit=1) for key, name in OLD.items()}
assert all(old.values()), [k for k, t in old.items() if not t]


def copy_lines(source, target, **scope):
    """Copy every price of a section tariff into the document, with the section's scope on the line."""
    for line in source.line_ids:
        vals = {"tariff_id": target.id}
        for name in ("direction", "transport_mode", "load_type"):
            if source[name]:
                vals[f"line_{name}"] = source[name]
        for name in ("port_ids", "country_ids", "state_ids"):
            if source[name]:
                vals[f"line_{name}"] = [Command.set(source[name].ids)]
        vals.update(scope)
        line.copy(vals)


versions = Tariff.search([("name", "=", NAME)], order="version")
v1 = versions[:1]
if not v1:
    v1 = Tariff.create({
        "name": NAME, "partner_id": old["pickup"].partner_id.id, "currency_id": old["pickup"].currency_id.id,
        "valid_from": date(2026, 1, 1), "scope_confirmed": True,
        "document": old["pickup"].document, "document_name": old["pickup"].document_name,
        "document_reference": "IRENEO «Tarifas MAD 2025» (p.4, p.5, p.6-7, p.15); mismos precios en 2026 (Ángel, "
                              "14/10/2026). Un solo documento: cada precio lleva el alcance de su sección.",
        "note": "Sustituye a las tarifas por sección de 2026 (recogidas, exportación Barajas, zona 3, almacén G-5). "
                "Almacén G-5: «A consultar» hasta que IRENEO confirme si los días libres se descuentan."})
    copy_lines(old["pickup"], v1)
    copy_lines(old["export"], v1)
    copy_lines(old["zone3_jan"], v1)
    copy_lines(old["g5"], v1, on_request=True,
               note="A consultar: IRENEO confirma si los 5 días libres se descuentan o se cobra desde el día 1")
    print("STAGE 1: draft created", v1.id, "| prices", len(v1.line_ids),
          "| next: add the export storage (p.4) in the UI, send for approval and approve")
elif v1.state != "approved":
    print("STAGE 1 pending: version 1 is", v1.state, "| prices", len(v1.line_ids))
elif len(versions) == 1:
    action = v1.with_user(belal).action_new_version()
    v2 = Tariff.browse(action["res_id"])
    v2.write({"valid_from": date(2026, 7, 15), "document": old["zone3_jul"].document,
              "document_name": old["zone3_jul"].document_name,
              "document_reference": "Carta IRENEO 14/07/2026 (RDL 9/2026): transporte +10 % desde 15/07/2026, sobre "
                                    "«Tarifas MAD 2025»; el resto de servicios, sin cambios."})
    zone_codes = set(old["zone3_jan"].line_ids.product_id.mapped("default_code"))
    v2.line_ids.filtered(lambda l: l.product_id.default_code in zone_codes and l.line_state_ids).unlink()
    copy_lines(old["zone3_jul"], v2)
    v2.action_submit()
    v2.with_user(belal).action_approve()
    v1.message_post(body="Aprobada el 27/10/2026 por delegación de Belal para pruebas: precios copiados de las tarifas "
                         "por sección ya comprobadas con el documento; el almacenaje de exportación (p.4) se dio de alta "
                         "desde la pantalla. No es una aprobación de Cristina ni de Ángel.")
    v2.message_post(body="Activada el 27/10/2026 por delegación de Belal para pruebas: mismos precios ya comprobados "
                         "(zona 3 = 2025 + 10 %, carta de 14/07/2026). No es una aprobación de Cristina ni de Ángel.")
    for tariff in old.values():
        if tariff.active:
            tariff.active = False
            tariff.message_post(body=f"Archivada el 27/10/2026: sus precios están ahora en «{NAME}» (un documento, "
                                     "alcance por precio). Las ofertas que la usaron la siguen mostrando.")
    print("STAGE 2: version", v2.version, "from", v2.valid_from, v2.state, "| prices", len(v2.line_ids),
          "| archived", ", ".join(t.name for t in old.values()))
else:
    print("DONE: versions", [(t.version, str(t.valid_from), t.state, len(t.line_ids)) for t in versions])
env.cr.commit()
