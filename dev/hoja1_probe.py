"""Read-only: state on boss20 of every code and field named in Hoja1 of «Plan detallado previsiones» (Cristina,
02/10/2026). No amount is printed. Rollback at the end."""
from datetime import date

assert env.cr.dbname in ("boss20", "boss_test", "boss20_uat"), env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, lang="es_ES"))  # noqa: F821
today = date.today()
CODES = ["T3", "T3-PAD", "FAD", "DEX", "THC-LCL", "THC", "PFT-FCL", "PFT-LCL", "PFT-AIR", "ROH", "SOI", "INS", "SAN",
         "VET", "GLO", "GLO-CCC", "GLO-LOG", "GLO-FUELEU", "DEM", "OCU", "DET", "TTE-FCL", "CES", "TTE-CON", "HAN",
         "ETX", "ALM", "AWB", "X-R"]
Line = env["boss.tariff.line"]
for code in CODES:
    t = env["product.template"].with_context(active_test=False).search([("default_code", "=", code)], limit=1)
    if not t:
        print(f"CODE {code}: NOT IN CATALOGUE")
        continue
    lines = Line.search([("product_id.default_code", "=", code), ("tariff_id.is_demo", "=", False)])
    tariffs = [(l.tariff_id.partner_id.name.replace(" [MUESTRA]", ""), l.tariff_id.state,
                "valid" if (not l.tariff_id.valid_to or l.tariff_id.valid_to >= today) and l.tariff_id.valid_from <= today
                else f"not valid ({l.tariff_id.valid_from}..{l.tariff_id.valid_to or 'open'})",
                l.uom_id.name, l.method) for l in lines]
    print(f"CODE {code}: active={t.active} mode={t.boss_pricing_mode} method={t.boss_cost_method} "
          f"vat={t.boss_vat_class} question={t.boss_open_question or '-'} sale_ok={t.sale_ok} | real prices: "
          f"{sorted(set(tariffs))}")

File = env["boss.expediente"]
fields = {k: (v.type, v.string) for k, v in File._fields.items()
          if any(s in k for s in ("ata", "noa", "eta", "etd", "airline", "handler", "carrier", "airport", "port",
                                  "period", "arrival", "pickup", "foh", "event", "date"))}
print("FILE FIELDS", sorted(fields.items()))
print("EVENT TYPES", env["boss.expediente.event"]._fields["kind"].selection if "kind" in env["boss.expediente.event"]._fields
      else [(k, v.string) for k, v in env["boss.expediente.event"]._fields.items() if k not in ("id", "create_uid", "write_uid", "create_date", "write_date", "display_name", "__last_update")])
print("ROLES", env["boss.partner.role"].search([]).mapped("name"))
print("AIRPORTS", env["boss.port"].search([("code", "in", ["MAD", "BCN", "VLC", "ESVLC", "ESBCN"])]).mapped(lambda p: (p.code, p.name)))
Partner = env["res.partner"]
print("HANDLERS/AIRLINES (roles)", [(p.name, p.boss_role_ids.mapped("name")) for p in Partner.search(
    [("boss_role_ids", "!=", False)], limit=40)])
cost = env["boss.expediente.cost"]
print("COST PERIOD FIELDS", [(k, v.type) for k, v in cost._fields.items() if "period" in k or "days" in k or "date" in k])
env.cr.rollback()  # noqa: F821
