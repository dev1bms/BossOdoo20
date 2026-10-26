"""Start and end events of the time-based supplier prices, read from their documents (odoo shell; boss20 / boss20_uat).
Only [MUESTRA] tariffs not approved are touched: the events are written on their time lines and a note in the tariff's
chatter tells the approver (state and approval untouched: approval stays Cristina's); approved tariffs never change
(they use the default of the service, the same events here). Idempotent.

Sources (.research/06_sea_supplier_docs.md, 07_air_road_supplier_docs.md; BossOdoo19 DECISIONS.md:139):
- MSC local charges import 01/09/2026 p.18 «DEMORAS (Fecha llegada buque hasta devolución del vacío)».
- MSC p.17 «OCUPACIONES (Fecha llegada buque hasta fecha entrega)»: «entrega» of the container = full container out
  of the terminal (the delivery to the consignee is not a port event).
- Hapag-Lloyd import MHD/DTD «from 00:01 of the first calendar day after discharge (DIFU)» until the empty unit is
  returned.
- WFS 2026 p.5 item 1: storage «desde el NOA (IMP) / FOH (EXP)»; Cristina 25/09: air import NOA -> pickup, air export
  delivery to the handler -> ETD (the actual departure once known).
- CMA CGM: the document gives no events (only on the carrier's website): left empty, the default of DEM applies."""
assert env.cr.dbname in ("boss20", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True))  # noqa: F821
EVENTS = {
    ("[MUESTRA] MSC gastos locales importación (origen China) 09-12/2026", "DEM"): ("ata", "container_empty_return"),
    ("[MUESTRA] MSC ocupación importación Valencia 09-12/2026", "OCU"): ("ata", "container_full_out"),
    ("[MUESTRA] MSC ocupación importación Barcelona 09-12/2026", "OCU"): ("ata", "container_full_out"),
    ("[MUESTRA] Hapag-Lloyd demoras+detención importación (MHD/DTD)", "DEM"): ("discharge", "container_empty_return"),
    ("[MUESTRA] WFS importación MAD/BCN desde 01/06/2026", "ALM"): ("noa_or_ata", "pickup"),
    ("[MUESTRA] WFS exportación PNS MAD/BCN desde 01/06/2026", "ALM"): ("foh", "departure"),
}
Tariff = env["boss.tariff"]
for (name, code), (start, end) in EVENTS.items():
    tariff = Tariff.search([("name", "=", name)], limit=1)
    if not tariff:
        print("not here:", name)
        continue
    lines = tariff.line_ids.filtered(lambda l, c=code: l.product_id.default_code == c and l.method == "time")
    if all((l.period_start_event, l.period_end_event) == (start, end) for l in lines):
        print("already", name, code, start, "->", end)
        continue
    if tariff.state == "approved":
        print("approved, not changed:", name)
        continue
    lines.write({"period_start_event": start, "period_end_event": end})
    labels = dict(lines._fields["period_start_event"]._description_selection(env))
    tariff.message_post(body=f"{code}: periodo desde «{labels[start]}» hasta «{labels[end]}», según el documento del "
                             f"proveedor (dev/setup_period_events.py, 26/10/2026). Estado y aprobación sin cambios.")
    print("set", name, code, f"({len(lines)} lines)", start, "->", end, "| state", tariff.state)
env.cr.commit()
