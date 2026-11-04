"""Check of the four tasks after the review of the sources (04/11/2026), boss20, rolled back: an agent's lump-sum cost
sold as several lines of the same service (cost in the first line, one purchase), «Reopen» for sales managers with a
reason (Odoo 17), the optional sailings of a quotation (printed, the chosen one gives the dates and goes to the file),
and the shipping lines grouped by their legal entities. Fictitious records only.
    dev/uat_run.sh check_source_tasks.py boss20"""
from datetime import date, timedelta

from odoo import Command
from odoo.exceptions import UserError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def outcome(fn):
    try:
        with env.cr.savepoint():
            fn()
        return "accepted"
    except UserError as exc:
        print(f"      «{' '.join(str(exc).split())[:150]}»")
        return "refused"


def product(code):
    return env["product.product"].search([("default_code", "=", code)], limit=1)


Partner = env["res.partner"]
customer = Partner.create({"name": "[PRUEBA] Cliente tareas fuentes", "is_company": True})
agent = Partner.create({"name": "[PRUEBA] Agente origen", "is_company": True, "supplier_rank": 1})
exw = product("EXW")

# 1. one agent cost, several sale lines of the same service
order = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "order_line": [Command.create({"product_id": exw.id, "product_uom_id": exw.uom_id.id, "boss_supplier_id": agent.id,
                                   "name": "[PRUEBA] Recogida en origen", "boss_manual_cost": 300.0, "sequence": 1}),
                   Command.create({"product_id": exw.id, "product_uom_id": exw.uom_id.id,
                                   "name": "[PRUEBA] Despacho de exportación", "sequence": 2}),
                   Command.create({"product_id": exw.id, "product_uom_id": exw.uom_id.id,
                                   "name": "[PRUEBA] Documentos", "sequence": 3})]})
first, second, third = order.order_line.sorted("sequence")
check("1 the second and third lines of the same service take their cost from the first: no cost, «included»",
      (False, True, True, "included", "included"),
      (first.boss_cost_included, second.boss_cost_included, third.boss_cost_included, second.boss_cost_kind,
       third.boss_cost_kind))
check("2 ... and cost nothing", (0.0, 0.0), (second.boss_cost_amount, third.boss_cost_amount))
second.boss_cost_included = False
check("3 unticked, the line is priced on its own again", True, second.boss_cost_kind != "included")
second.boss_cost_included = True

order.write({"state": "sale"})  # inside this transaction only: the file and its purchase needs
file = env["boss.expediente"].create(order._boss_file_values())
file._boss_link_orders(order)
needs = file.cost_ids.filtered(lambda n: n.product_id == exw)
check("4 the file buys the agent's charges once (one purchase need, from the first line)", (1, first),
      (len(needs), needs.sale_line_id))

# 2. reopen: sales managers, with a reason
file.write({"state": "closed"})
salesman = env["res.users"].create({"name": "[PRUEBA] Comercial sin gestión", "login": "prueba_comercial_fuentes",
                                    "group_ids": [Command.set([env.ref("sales_team.group_sale_salesman").id])]})
check("5 a salesperson cannot reopen a closed file", "refused", outcome(file.with_user(salesman).action_reopen))
action = file.action_reopen()
check("6 a manager is asked the reason", "boss.expediente.reopen", action.get("res_model"))
env["boss.expediente.reopen"].create({"expediente_ids": [Command.set(file.ids)],
                                      "reason": "[PRUEBA] la naviera cambió el buque"}).action_confirm()
check("7 reopened, with the reason in the history", ("open", True),
      (file.state, any("la naviera cambió el buque" in (m.body or "") for m in file.message_ids)))

# 3. sailings of a quotation
quote = env["sale.order"].create({
    "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
    "boss_sailing_ids": [
        Command.create({"vessel": "[PRUEBA] BUQUE UNO", "voyage": "001W", "cutoff": date.today() + timedelta(days=5),
                        "etd": date.today() + timedelta(days=7), "eta": date.today() + timedelta(days=37)}),
        Command.create({"vessel": "[PRUEBA] BUQUE DOS", "voyage": "002W", "via": "Singapore",
                        "cutoff": date.today() + timedelta(days=12), "etd": date.today() + timedelta(days=14),
                        "eta": date.today() + timedelta(days=40)})]})
one, two = quote.boss_sailing_ids.sorted("etd")
check("8 transit days from ETD and ETA", (30, 26), (one.transit_days, two.transit_days))
one.chosen = True
two.chosen = True
check("9 one chosen sailing: it gives the quotation its ETD and ETA", (False, True, two.etd, two.eta),
      (one.chosen, two.chosen, quote.boss_etd, quote.boss_eta))
html = env["ir.actions.report"]._render_qweb_html("sale.report_saleorder", quote.ids)[0].decode()
check("10 the quotation prints its sailings", (True, True, True),
      ("boss_sailings" in html, "BUQUE UNO" in html, "Singapore" in html))
values = quote._boss_file_values()
check("11 the chosen sailing goes to the file", ("[PRUEBA] BUQUE DOS", "002W", two.cutoff),
      (values.get("vessel"), values.get("voyage"), values.get("cutoff")))

# 4. shipping lines grouped by their legal entities
def entity(name):
    return Partner.with_context(active_test=False).search([("name", "=", name), ("parent_id", "=", False)], limit=1)


france, iberica = entity("CMA CGM FRANCE"), entity("CMA CGM IBERICA, S.A.U.")
line_, logistics = entity("MAERSK LINE"), entity("MAERSK  LOGISTICS & SERVICES SPAIN, S.L.U.")
check("12 CMA CGM France and Ibérica, Maersk Line and Maersk Logistics are one carrier each",
      (True, True), (france.id in iberica._boss_carrier_family_ids(), line_.id in logistics._boss_carrier_family_ids()))

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
