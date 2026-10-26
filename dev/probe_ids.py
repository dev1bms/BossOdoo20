"""Local only: ids of the [DEMO] cycle records for dev/shots_cycle.json."""
assert env.cr.dbname == "boss_test"  # noqa: F821
imd = env["ir.model.data"].search([("module", "=", "boss_trial"), ("name", "like", "demo_")])  # noqa: F821
print({d.name: (d.model, d.res_id) for d in imd if d.model in ("boss.expediente", "sale.order")})
f = env["boss.expediente"].browse(imd.filtered(lambda d: d.name == "demo_file_wfs").res_id)  # noqa: F821
print("wfs bills", f.purchase_order_ids.ids, "msc invoice", env["boss.expediente"].browse(imd.filtered(lambda d: d.name == "demo_file_msc").res_id).invoice_ids.ids)  # noqa: F821
print("action", env.ref("boss_expediente.boss_expediente_action").id)  # noqa: F821
