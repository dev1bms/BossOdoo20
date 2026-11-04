"""Belal, 04/11/2026: make sure no [DEMO] supplier tariff can price a real quotation (archived tariffs are never used:
boss.pricing searches tariff_id.active; on 04/11 all of them were found already archived, so this is a guard), and clear
the open-question flag of the services whose question is answered (P09 DET, P11 T3-PAD, P12 VGM, P25 AWB; P03, P13, P16,
P18 and P24 stay open). Idempotent; commits.
    dev/server_shell.sh archive_demo_tariffs.py"""
assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
Tariff = env["boss.tariff"]  # noqa: F821
demo = Tariff.search([("name", "ilike", "[DEMO]")]).filtered(lambda t: t.name.strip().startswith("[DEMO]"))
for tariff in demo:
    print(f"ARCHIVED [{tariff.state}] {tariff.name} ({tariff.partner_id.name}, {len(tariff.line_ids)} lines)")
demo.write({"active": False})
answered = {"T3-PAD": "P11", "DET": "P09", "VGM": "P12", "AWB": "P25"}
for code, question in answered.items():
    template = env["product.template"].search([("default_code", "=", code)], limit=1)  # noqa: F821
    if template.boss_open_question == question:
        template.boss_open_question = False
        print(f"FLAG CLEARED {code} ({question} answered)")
env.cr.commit()  # noqa: F821
left = env["product.template"].search([("boss_open_question", "!=", False)])  # noqa: F821
print("DONE: demo tariffs archived", len(demo), "| services still with an open question:",
      ", ".join(f"{t.default_code} ({t.boss_open_question})" for t in left) or "none")
