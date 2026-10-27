"""Remove demo prices from what prices a quotation (Belal 27/10/2026), keeping the history of the test records.
Demo = marked «Demo tariff» (is_demo) and with an invented document, whatever the name says; tariffs from real
documents (named [MUESTRA] while waiting for approval) are not touched here.
- Demo tariff used by no quotation line and no file service: deleted (Odoo unlink; if anything still refers to it, it
  is archived instead).
- Demo tariff used by a test quotation or file: archived (no longer chosen, the records keep showing it).
- [DEMO] customer pricelist: archived (22 test quotations use it). [DEMO] suppliers: archived.
Idempotent. Backup of boss20 taken before (~/backups/boss20-20261027_0944*).
    dev/server_shell.sh cleanup_demo_pricing.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, active_test=False))  # noqa: F821
Tariff, SOL, Cost = env["boss.tariff"], env["sale.order.line"], env["boss.expediente.cost"]
for tariff in Tariff.search([("is_demo", "=", True)]):
    lines = tariff.line_ids
    used = SOL.search_count([("boss_tariff_line_id", "in", lines.ids)]) + Cost.search_count(
        [("tariff_line_id", "in", lines.ids)])
    name = tariff.name
    if not used:
        try:
            with env.cr.savepoint():
                tariff.unlink()
            print("DELETED", name)
            continue
        except Exception as error:  # noqa: BLE001 - something else refers to it: keep it archived
            print("NOT DELETED", name, type(error).__name__, str(error)[:120])
    if tariff.active:
        tariff.active = False
        tariff.message_post(body="Tarifa de demostración archivada el 27/10/2026 (limpieza de precios de prueba): "
                                 "ya no se elige; las ofertas y expedientes de prueba que la usaron la siguen mostrando.")
    print("ARCHIVED", name, f"(used {used} times)")
for pricelist in env["product.pricelist"].search([("name", "ilike", "[DEMO]"), ("active", "=", True)]):
    pricelist.active = False
    print("PRICELIST ARCHIVED", pricelist.name)
for partner in env["res.partner"].search([("name", "=ilike", "[DEMO]%"), ("active", "=", True), ("boss_demo", "=", False)]):
    partner.active = False
    print("PARTNER ARCHIVED", partner.name)
print("LEFT: demo tariffs active", Tariff.search_count([("is_demo", "=", True), ("active", "=", True)]),
      "| real tariffs", Tariff.search_count([("is_demo", "=", False), ("active", "=", True)]))
env.cr.commit()
