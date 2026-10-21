"""Local demo states for the guide screenshots (odoo shell on boss_test only). FICTITIOUS data."""
from odoo import Command

env = env  # noqa: F821 (odoo shell)
assert env.cr.dbname == "boss_test", "local test database only"
accepted = env["sale.order"].search([("state", "=", "sale")], order="id desc", limit=1)
draft = accepted.copy({"origin": accepted.origin})
ces = env["product.product"].search([("default_code", "=", "CES")])
dv = env.ref("boss_pricing.container_type_dv")
env["sale.order.line"].create({"order_id": draft.id, "product_id": ces.id, "product_uom_id": ces.uom_id.id,
                               "boss_container_size": "20", "boss_container_type_id": dv.id})
draft.order_line.filtered(lambda l: l.product_id.default_code == "DEM").unlink()
env.cr.commit()
tariff = env["boss.tariff"].search([("name", "ilike", "EJEMPLO")], limit=1)
thc = env.ref("boss_services.service_thc")
print("IDS", {"accepted": accepted.id, "draft": draft.id, "tariff": tariff.id,
              "dem_line": tariff.line_ids.filtered(lambda l: l.method == "time")[:1].id, "thc_tmpl": thc.id,
              "lead": accepted.opportunity_id.id})
