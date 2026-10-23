"""ALM of the WFS [MUESTRA] sample tariffs as the document reads (odoo shell; boss20). Idempotent; approves NOTHING.

WFS «Tarifas de servicios de carga» V 2026-02 p.5 punto 1 (carga general MAD/BCN): per 100 kg of the AWB chargeable
weight and per 24 hours, 48 h from NOA/FOH as a threshold, Friday with a Monday exit 72 h, Saturday free until Monday
included. Readings the business has not decided stay 'not decided': day count (P40), tiers (P29), fraction (P41).
The tariffs follow their own workflow: back to draft, edit, sent for approval again (a person approves).
"""
from odoo import Command

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname == "boss20", env.cr.dbname
env = env(user=env.ref("base.user_admin"), context=dict(env.context, lang="es_ES"))
alm = env["product.product"].search([("default_code", "=", "ALM")], limit=1)
COMMON = {"method": "time", "basis": "awb_kg", "unit_size": 100, "round_up": False, "round_undecided": True,
          "period_unit": "undecided", "free_hours": 48, "free_days": 0, "free_mode": "threshold",
          "friday_monday_free": 72, "saturday_until_monday": True, "friday_extra_day": False,
          "tier_mode": "undecided", "min_per_day": False, "document_page": "5 (punto 1)"}
NOTE = ("Revisión ALM 23/10/2026 con el documento (p.5 punto 1): viernes con salida el lunes 72 h; sábado libre hasta el "
        "lunes incluido; sin decidir: cuenta de días (P40), tramos (P29), «por 100 kg» con o sin fracción (P41). "
        "Alcance comprobado con el documento (cualquier aerolínea, país y cliente). Sigue pendiente de aprobación por "
        "una persona.")


def update(name, prices, minimum):
    tariff = env["boss.tariff"].search([("name", "=", name)], limit=1)
    assert tariff and tariff.state in ("draft", "to_approve"), (name, tariff.state)
    line = tariff.line_ids.filtered(lambda l: l.product_id == alm)
    values = dict(COMMON, min_amount=minimum)
    tiers = [{"up_to": 7, "unit_price": prices[0]}, {"up_to": 0, "unit_price": prices[1]}]
    current = line and all(line[k] == v for k, v in values.items()) and [
        (b.up_to, b.unit_price) for b in line.bracket_ids] == [(7.0, prices[0]), (0.0, prices[1])]
    if current:
        print("UNCHANGED", tariff.id, name)
        return tariff
    was = tariff.state
    tariff.action_back_to_draft()
    if line:
        line.write(dict(values, bracket_ids=[Command.clear()] + [Command.create(t) for t in tiers]))
    else:
        tariff.write({"line_ids": [Command.create(dict(values, product_id=alm.id, uom_id=alm.uom_id.id,
                                                       bracket_ids=[Command.create(t) for t in tiers]))]})
    if not tariff.scope_confirmed:
        # p.5 punto 1 applies to any airline, origin country and customer: the empty scope fields mean «any»
        tariff.scope_confirmed = True
    if was == "to_approve":
        tariff.action_submit()
    tariff.message_post(body=NOTE)
    print("UPDATED", tariff.id, name, was, "->", tariff.state)
    return tariff


imp = update("[MUESTRA] WFS importación MAD/BCN desde 01/06/2026", (13.26, 31.00), 56.16)
exp = update("[MUESTRA] WFS exportación PNS MAD/BCN desde 01/06/2026", (13.02, 30.43), 55.13)
env.cr.commit()
for tariff in imp | exp:
    for line in tariff.line_ids.filtered(lambda l: l.product_id == alm):
        print("LINE", line.id, tariff.state, line.period_unit, line.tier_mode, line.round_undecided, line.free_hours,
              line.friday_monday_free, line.saturday_until_monday, line.min_amount,
              [(b.up_to, b.unit_price) for b in line.bracket_ids])
for line in env["boss.tariff.line"].search([("product_id", "=", alm.id)]):
    print("ALL", line.id, line.tariff_id.name, line.tariff_id.state, line.period_unit, line.tier_mode)
