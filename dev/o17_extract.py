"""Read-only extraction from Odoo 17 for the F2 contact migration. Runs ON the server after o17_lib.py (see dev/o17_run.sh).
Output stays in the private folder ~/o17_export (mode 700, files 600), never in Git or in the chat; printed lines are counts
and technical names only.
    dev/o17_run.sh run o17_extract.py fields x_dashboard x_partidas x_quotations res.partner
    dev/o17_run.sh run o17_extract.py related            # reads ~/o17_export/spec.json
    dev/o17_run.sh run o17_extract.py balances
    dev/o17_run.sh run o17_extract.py partners ids.json  # ids.json in ~/o17_export; adds the parents it needs
"""
import re

PARTNER_FIELDS = ["id", "name", "is_company", "type", "parent_id", "active", "street", "street2", "zip", "city", "state_id",
                  "country_id", "email", "phone", "mobile", "website", "lang", "comment", "company_registry", "vat",
                  "x_studio_type", "x_studio_code", "x_studio_is_carrier", "x_studio_is_airline",
                  "x_studio_is_customs_agent", "x_studio_is_trucker", "x_studio_is_provider", "x_studio_is_agent",
                  "x_studio_is_shipperconsignee", "customer_rank", "supplier_rank", "property_payment_term_id",
                  "property_supplier_payment_term_id", "child_ids"]
CTX_ALL = {"active_test": False}


def ids_of(value):
    if isinstance(value, list):
        if len(value) == 2 and isinstance(value[0], int) and isinstance(value[1], str):
            return [value[0]]  # many2one [id, name]
        return [v for v in value if isinstance(v, int)]
    return []


def cmd_fields(client, models):
    for model in models:
        meta = client.call(model, "fields_get", [], {"attributes": ["string", "type", "relation", "selection", "store"]})
        write_private(f"fields_{model}.json", meta)  # noqa: F821
        partner = sorted(f for f, m in meta.items() if m.get("relation") == "res.partner")
        links = sorted(f for f, m in meta.items() if m.get("relation") in ("x_dashboard", "x_partidas", "x_quotations"))
        status = {f: [s[0] for s in m["selection"]] for f, m in meta.items()
                  if m.get("type") == "selection" and re.search(r"state|stage|status|estado|closed|open", f + m["string"], re.I)}
        print(f"MODEL {model}: {len(meta)} fields")
        print("  partner fields:", partner)
        print("  links to the freight models:", links)
        print("  status-like selections:", status)


def cmd_related(client):
    spec = read_private("spec.json")  # noqa: F821
    out, counts = {}, {}
    for item in spec["models"]:
        model, fields = item["model"], item["partner_fields"]
        rows = client.search_read_all(model, item.get("domain", []), ["id"] + fields, context=CTX_ALL)
        counts[model] = len(rows)
        for f in fields:
            out[f"{model}.{f}"] = sorted({i for r in rows for i in ids_of(r.get(f))})
        # keep which record points where only as ids (no names): for the line items to find their file
        print(f"{model}: {len(rows)} records read")
    write_private("related.json", {"by_field": out, "records": counts})  # noqa: F821
    for key, ids in out.items():
        print(f"  {key}: {len(ids)} distinct partners")


def cmd_balances(client):
    open_moves = client.search_read_all(
        "account.move", [("state", "=", "posted"), ("payment_state", "in", ["not_paid", "partial", "in_payment"]),
                         ("move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"])],
        ["id", "partner_id", "commercial_partner_id"])
    open_p = sorted({i for r in open_moves for i in ids_of(r.get("commercial_partner_id")) + ids_of(r.get("partner_id"))})
    groups = client.call("account.move.line", "read_group",
                         [[("parent_state", "=", "posted"), ("partner_id", "!=", False)], ["partner_id"], ["partner_id"]],
                         {"lazy": False})
    any_p = sorted({g["partner_id"][0] for g in groups if g.get("partner_id")})
    write_private("balances.json", {"open_partner_ids": open_p, "any_entry_partner_ids": any_p})  # noqa: F821
    print(f"open posted moves: {len(open_moves)}; partners with an open item: {len(open_p)}; "
          f"partners with any posted entry: {len(any_p)}")


def cmd_partners(client, ids_file):
    wanted = set(read_private(ids_file))  # noqa: F821
    have, queue, rows = set(), sorted(wanted), []
    while queue:
        batch, queue = queue[:200], queue[200:]
        for rec in client.call("res.partner", "read", [batch, PARTNER_FIELDS], {"context": CTX_ALL}):
            if isinstance(rec.get("comment"), str):
                rec["comment"] = re.sub(r"data:image/[^\"'<> )]+", "[image removed]", rec["comment"])
            rows.append(rec)
            have.add(rec["id"])
            parent = rec["parent_id"][0] if rec.get("parent_id") else None
            if parent and parent not in have and parent not in queue:
                queue.append(parent)  # a child never travels without its parent
    missing = sorted(wanted - have)
    write_private("partners.json", {"records": rows})  # noqa: F821
    print(f"partners read: {len(rows)} (requested {len(wanted)}, parents added {len(rows) - len(wanted & have)}, "
          f"missing {len(missing)})")


try:
    client = Client()  # noqa: F821
    mode, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])  # noqa: F821
    modes = {"fields": lambda: cmd_fields(client, args), "related": lambda: cmd_related(client),
             "balances": lambda: cmd_balances(client), "partners": lambda: cmd_partners(client, args[0])}
    if mode not in modes:
        print("ERROR unknown_mode")
        sys.exit(2)  # noqa: F821
    modes[mode]()
except O17Error as exc:  # noqa: F821
    fail(exc)  # noqa: F821
