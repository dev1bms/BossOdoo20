"""Check of roadmap item 4 on boss20 (rolled back): the operator of a customer for a traffic becomes the responsible
when a file opens, the files can be filtered by their next step («Needs action», «To do in operations»), and «My work»
opens the board by status. [PRUEBA] customer and users only. Prints «CHECK PASS|FAIL …» and «RESULT …».
    dev/uat_run.sh check_work_queue.py boss20"""
from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


user = lambda login, groups: env["res.users"].with_context(no_reset_password=True).create({  # noqa: E731
    "name": f"[PRUEBA] Cola {login}", "login": f"prueba_cola_{login}", "group_ids": [Command.set([ref(g).id for g in groups])]})
sales = user("comercial", ["sales_team.group_sale_salesman"])
ops = user("operativo", ["sales_team.group_sale_salesman", "purchase.group_purchase_user"])
customer = env["res.partner"].create({"name": "[PRUEBA] Cola Importador, S.L.", "is_company": True,
                                     "country_id": ref("base.es").id})
other = env["res.partner"].create({"name": "[PRUEBA] Cola Otro, S.L.", "is_company": True,
                                  "country_id": ref("base.es").id})
env["boss.operator.assignment"].create({"partner_id": customer.id, "traffic_code": "IMB", "user_id": ops.id,
                                        "source": "[PRUEBA]"})
File = env["boss.expediente"].with_user(sales)  # the salesman opens them (as at acceptance)
case = {"business": "boss", "direction": "import", "transport_mode": "sea", "load_type": "fcl"}
assigned = File.create(dict(case, partner_id=customer.id))
check("a file of a customer with an operator for its traffic gets that operator as responsible",
      ("IMB", ops), (assigned.sudo().traffic_code, assigned.sudo().user_id))
check("... and says so in its history", True,
      any("Operators by customer and traffic" in (m.body or "") for m in assigned.sudo().message_ids))
air = File.create(dict(case, partner_id=customer.id, transport_mode="air", load_type="air"))
check("another traffic of the same customer (IAB) keeps who opened it", ("IAB", sales), (air.traffic_code, air.user_id))
plain = File.create(dict(case, partner_id=other.id))
check("a customer without operator keeps who opened it", sales, plain.user_id)

Files = env["boss.expediente"]
needs = Files.search([("next_step", "not in", ["done"]), ("state", "!=", "cancel")])
check("«Needs action» finds the new files (next step not done)", True, (assigned | air | plain) <= needs)
todo = Files.search([("next_step", "in", ["link_quotation"])])
check("a step filter finds a file by its next step (opened without quotation: «Link the accepted quotation»)",
      (True, "link_quotation"), (assigned in todo, assigned.sudo().next_step))
check("... and leaves it out of another step («Put the file in transit»)", False,
      assigned in Files.search([("next_step", "in", ["in_transit"])]))
closed = Files.search([("financial_closed", "=", True)], limit=1)
if closed:
    check("a financially closed file is not in «Needs action»", False, closed in needs)
mine = Files.with_user(ops).search([("user_id", "=", ops.id), ("next_step", "not in", ["done"]),
                                    ("state", "!=", "cancel")])
check("«My work» of the operator shows the file assigned to the operator", True, assigned in mine)
action = ref("boss_expediente.boss_expediente_my_work_action")
check("«My work» opens the board by status first, with «My files» and «Needs action»",
      ("kanban", True, True), (action.view_mode.split(",")[0], "search_default_my" in action.context,
                                "search_default_needs_action" in action.context))
arch = Files.get_view(view_type="kanban")["arch"]
check("the board shows the next step on each card", True, 'name="next_step"' in arch)

env.cr.rollback()
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
