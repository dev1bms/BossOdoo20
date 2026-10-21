env = env  # noqa: F821
assert env.cr.dbname == "boss_test"
pl = env["product.pricelist"].search([])
pl.write({"currency_id": env.ref("base.EUR").id})
env.cr.commit()
print("PRICELISTS", pl.mapped("name"), pl.mapped("currency_id.name"))
