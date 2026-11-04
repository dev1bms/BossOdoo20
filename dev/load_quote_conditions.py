"""Load the conditions of the offer that the commercial team sends today (Ángel's FCL sheets, 04/11/2026) into the
«Terms and conditions» of the matching quotation templates, in Spanish and English: a quotation made from the template
prints them in the customer's language. The text is commercial (amounts of extras) and stays out of Git:
.research/quote_conditions.json. A template whose conditions were already written by someone is left as it is.
    dev/server_shell.sh load_quote_conditions.py .research/quote_conditions.json"""
import json
import os

from markupsafe import Markup, escape

from odoo.tools import is_html_empty

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
name = [n for n in os.environ.get("BOSS_FILES", "").split("|") if n == "quote_conditions.json"]
assert name, "pass .research/quote_conditions.json"
data = json.load(open(f"/tmp/boss/{name[0]}", encoding="utf-8"))
Template = env["sale.order.template"].with_context(active_test=False)  # noqa: F821


def html(title, items):
    return Markup("<p><strong>%s</strong></p><ul>%s</ul>") % (
        title, Markup("").join(Markup("<li>%s</li>") % escape(item) for item in items))


for template_name, texts in data["templates"].items():
    template = Template.search([("name", "=", template_name)], limit=1)
    if not template:
        print(f"MISSING template «{template_name}»")
        continue
    if not is_html_empty(template.with_context(lang="es_ES").note):
        print(f"KEPT {template.id}: conditions already written")
        continue
    # «note» is translated as a whole (translate=True): one value per language
    template.with_context(lang="en_US").note = html("Conditions of the offer", texts["en"])
    template.with_context(lang="es_ES").note = html("Condiciones de la oferta", texts["es"])
    print(f"SET {template.id}: {len(texts['es'])} conditions (es, en)")
env.cr.commit()  # noqa: F821
