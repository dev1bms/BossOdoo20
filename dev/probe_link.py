"""Local only (boss_test): why does a confirmed order not appear in file.sale_order_ids? Rolled back."""
from odoo import Command
assert env.cr.dbname == "boss_test"  # noqa: F821
Order = env["sale.order"]  # noqa: F821
partner = env["res.partner"].create({"name": "PROBE", "country_id": env.ref("base.es").id})  # noqa: F821
tax = env["account.tax"].create({"name": "PROBE 21", "amount": 21, "type_tax_use": "sale"})  # noqa: F821
env["boss.vat.tax"].create([{"vat_class": c, "tax_id": tax.id} for c in ("NR", "EX", "NS")])  # noqa: F821
csm = env.ref("boss_services.service_csm").product_variant_id  # noqa: F821
order = Order.create({"partner_id": partner.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
                      "boss_port_id": env.ref("boss_pricing.port_esvlc").id, "boss_country_id": env.ref("base.cn").id,  # noqa: F821
                      "order_line": [Command.create({"product_id": csm.id})]})
order.order_line.price_unit = 90
from odoo.tests import new_test_user
sales = new_test_user(env, "probe_sales", groups="sales_team.group_sale_salesman,boss_pricing.group_tariff_user,purchase.group_purchase_user")  # noqa: F821
order.user_id = sales
try:
    order.with_user(sales).action_confirm()
except Exception as e:
    print("confirm", repr(str(e)))
f = order.boss_expediente_id
print("search0", env["boss.expediente"].search([("sale_order_ids", "in", order.ids)]))  # noqa: F821
print("file", f, "link", f.order_link_ids, "alloc", f.allocation_ids, "stored", f.sale_order_ids)
env.flush_all()  # noqa: F821
env.cr.execute("select * from boss_expediente_sale_order_rel where expediente_id = %s", [f.id])  # noqa: F821
print("rel rows", env.cr.fetchall())  # noqa: F821
print("search", env["boss.expediente"].search([("sale_order_ids", "in", order.ids)]))  # noqa: F821
order._boss_open_files()
print("search2", env["boss.expediente"].search([("sale_order_ids", "in", order.ids)]), f.sale_order_ids)  # noqa: F821
env.cr.rollback()  # noqa: F821
