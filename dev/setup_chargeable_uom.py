"""Road chargeable kg («kg tasable terrestre») counted from the shipment (ADR-006 amendment, Ángel's Teams message of
27/10/2026): its quantity on a quotation line is the chargeable weight of the shipment (higher of gross weight and
volume × 333, whatever the main mode of the shipment: the road leg of a sea import is road), no longer typed. Air («kg tasable aéreo») keeps the AWB weight (the handlers charge on the
figure of the AWB; the chargeable weight estimates it until the AWB exists). Only draft quotations recompute when
they are edited; accepted ones are frozen (ADR-003). Idempotent.    dev/server_shell.sh setup_chargeable_uom.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
uom = env["uom.uom"].with_context(lang="es_ES").search([("name", "=", "kg tasable terrestre")], limit=1)  # noqa: F821
assert uom, "road chargeable kg unit not found"
if uom.boss_quantity_source != "chargeable_road_kg":
    uom.boss_quantity_source = "chargeable_road_kg"
    env.cr.commit()  # noqa: F821
print("UOM", uom.name, uom.boss_quantity_source)
