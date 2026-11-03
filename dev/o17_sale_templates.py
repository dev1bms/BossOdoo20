"""Read-only extraction of the selling-price templates of Odoo 17 (roadmap item 3, Belal's go-ahead of 03/11/2026 to
copy settings). Runs ON the server after o17_lib.py (see dev/o17_run.sh):
    dev/o17_run.sh run o17_sale_templates.py
Writes ~/o17_export/sale_templates.json (private: real selling prices, never in Git or in the chat) with every template
of «Quotation Local Lines Template» (x_quotation_local_line: «Standard» without customer, one per customer/incoterm)
and its lines (x_quotation_line: concept, charge basis «calc type», value, currency, profit formula flag). Prints counts,
charge bases and value shapes only.
"""
import re
from collections import Counter

TEMPLATE_FIELDS = ["id", "x_name", "x_studio_client", "x_studio_incoterm", "x_studio_quotation_lines", "x_active",
                   "write_date"]
LINE_FIELDS = ["id", "x_name", "x_studio_concept", "x_studio_calc_type", "x_studio_value", "x_studio_currency",
               "x_studio_profit_auto_formula", "x_studio_profit", "x_studio_line_type", "x_studio_active", "x_active",
               "x_studio_sequence"]


def shape(value):
    """The form of a value without the value: 9 // 9, 9, text…"""
    return re.sub(r"\d+(?:[.,]\d+)?", "9", str(value or "")).strip()[:30]


try:
    client = Client()
    templates = client.call("x_quotation_local_line", "search_read", [[]],
                            {"fields": TEMPLATE_FIELDS, "context": {"active_test": False}})
    line_ids = sorted({i for t in templates for i in t["x_studio_quotation_lines"]})
    fields_meta = client.call("x_quotation_line", "fields_get", [], {"attributes": ["type"]})
    lines = client.call("x_quotation_line", "read", [line_ids],
                        {"fields": [f for f in LINE_FIELDS if f in fields_meta or f == "id"],
                         "context": {"active_test": False}})
except O17Error as exc:  # noqa: F821 (o17_lib)
    fail(exc)  # noqa: F821
write_private("sale_templates.json", {"templates": templates, "lines": lines})  # noqa: F821
print("TEMPLATES", len(templates), "with customer", sum(1 for t in templates if t["x_studio_client"]),
      "active", sum(1 for t in templates if t.get("x_active")))
print("LINES", len(lines))
print("CALC TYPES", Counter(l.get("x_studio_calc_type") for l in lines).most_common())
print("VALUE SHAPES", Counter(shape(l.get("x_studio_value")) for l in lines).most_common(15))
print("CURRENCIES", Counter((l.get("x_studio_currency") or [0, "-"])[1] for l in lines).most_common())
print("PROFIT FORMULA", Counter(bool(l.get("x_studio_profit_auto_formula")) for l in lines).most_common())
print("LINE TYPES", Counter(l.get("x_studio_line_type") for l in lines).most_common())
print("CONCEPTS", len({(l.get("x_studio_concept") or [0])[0] for l in lines}))
