"""F2 acceptance after the permanent contact load (plan F2 «Aceptación en boss20»), in a rolled-back transaction.
    dev/server_shell.sh check_migration_accept.py <scope.json> dev/migrate_partners.py
A. a second run of the loader creates nothing, links nothing new and changes no contact;
B. 20 loaded contacts compared field by field with the Odoo 17 records (as read with read_record);
C. companies sharing a VAT on boss20: only the pairs that already share it in Odoo 17 (listed, never merged);
D. Spanish customers without VAT (P31), counted; E. carrier families: some set, the 5 MSC entities in one family.
Prints ids and field names only (no personal values). Exit 1 on failure."""
import datetime
import hashlib
import json
import os

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


files = [f for f in os.environ.get("BOSS_FILES", "").split("|") if f]
scope_file = next(f for f in files if f.endswith(".json"))
loader_file = next(f for f in files if f.endswith(".py"))
ns = {"env": env, "__name__": "lib"}
exec(compile(open(f"/tmp/boss/{loader_file}", encoding="utf-8").read(), loader_file, "exec"), ns)
records = json.load(open(f"/tmp/boss/{scope_file}", encoding="utf-8"))["records"]
by_id = {r["id"]: r for r in records}
P = env["res.partner"].with_context(active_test=False)
IMD = env["ir.model.data"]
links = {int(i.name.split("_")[-1]): i for i in IMD.search([("module", "=", "o17_partner"), ("model", "=", "res.partner"),
                                                           ("name", "=like", "res_partner_%"), ("name", "not like", "family")])}
print(f"LINKS {len(links)} Odoo 17 ids linked; scope {len(records)}")
FIELDS = ["name", "vat", "ref", "phone", "email", "boss_mobile", "street", "street2", "city", "zip", "parent_id", "type",
          "active", "customer_rank", "supplier_rank", "boss_role_ids", "boss_carrier_group_id", "property_payment_term_id"]


def snapshot():
    out = {}
    for p in P.search([]):
        row = [sorted(p[f].ids) if hasattr(p[f], "ids") else p[f] for f in FIELDS]
        out[p.id] = hashlib.md5(json.dumps(row, default=str).encode()).hexdigest()
    return out


# A. rerun
before = snapshot()
log = ns["load"](env, f"/tmp/boss/{scope_file}")
env.flush_all()
after = snapshot()
check("A second run creates no contact", 0, len(log["created"]))
check("A second run links no new contact", 0, len(log["linked_existing"]))
check("A contact count unchanged", len(before), len(after))
check("A no contact changed by the second run", [], sorted(pid for pid in before if before[pid] != after.get(pid))[:20])
skipped = {s[0] for s in log["skipped"]}
check("A every scope record linked except the BOSS children waiting for a decision", len(records) - len(skipped),
      len(set(links) & set(by_id)))

# B. 20 contacts field by field (created ones: their values all come from Odoo 17)
created = sorted(o for o, imd in links.items()  # created by the load: the contact is not older than its link
                 if o in by_id and P.browse(imd.res_id).create_date >= imd.create_date - datetime.timedelta(seconds=5))
step = max(1, len(created) // 20)
sample = created[::step][:20]
mism = []
for o in sample:
    r, p = by_id[o], P.browse(links[o].res_id)
    exp = {"name": r.get("name") or False, "street": r.get("street") or False, "street2": r.get("street2") or False,
           "city": r.get("city") or False, "zip": r.get("zip") or False, "email": r.get("email") or False,
           "phone": r.get("phone") or False, "boss_mobile": r.get("mobile") or False,
           "active": r.get("active", True), "is_company": bool(r.get("is_company"))}
    for f, v in exp.items():
        if (p[f] or False) != v:
            mism.append((o, f))
    t = r.get("type") or "contact"
    if p.type != (t if t in ("contact", "invoice", "delivery", "other") else "other"):
        mism.append((o, "type"))
    src_parent = r["parent_id"][0] if r.get("parent_id") else None
    if (links[src_parent].res_id if src_parent in links else False) != (p.parent_id.id or False):
        mism.append((o, "parent_id"))
    if not src_parent and ns["norm_vat"](r.get("vat")) and p.vat:
        if not ns["vat_keys"](p.vat, p.country_id.code) & ns["vat_keys"](r["vat"], p.country_id.code):
            mism.append((o, "vat"))
    if (r.get("country_id") or [0, False])[1] and not p.country_id:
        mism.append((o, "country_id"))
print("SAMPLE B:", sample)
check("B 20 loaded contacts equal to Odoo 17 field by field", [], mism)

# C. VAT shared by companies on boss20 vs Odoo 17
env.cr.execute("""SELECT vat, array_agg(id) FROM res_partner WHERE is_company AND parent_id IS NULL AND vat IS NOT NULL
                  AND vat <> '' GROUP BY vat HAVING count(*) > 1""")
groups = env.cr.fetchall()
src_dup = {k for v in log["source_vat_duplicates"] for k in ns["vat_keys"](v)}
new_dups = [ids for vat, ids in groups if not ns["vat_keys"](vat) & src_dup]
print(f"INFO companies sharing a VAT on boss20: {len(groups)} groups; already shared in Odoo 17: "
      f"{len(groups) - len(new_dups)}")
check("C no VAT duplicate created by the migration (only those already in Odoo 17, listed for review)", [], new_dups)

# D. P31 (count only)
es = env.ref("base.es")
no_vat = P.search_count([("id", "in", [i.res_id for i in links.values()]), ("country_id", "=", es.id),
                         ("customer_rank", ">", 0), ("parent_id", "=", False), ("vat", "=", False)])
print(f"INFO P31: Spanish migrated customers without VAT: {no_vat}")

# E. families
fam = P.search_count([("boss_carrier_group_id", "!=", False)])
heads = {P.browse(links[o].res_id).boss_carrier_group_id.id for o in ns["MSC_FAMILY"] if o in links}
check("E contacts with a carrier family > 0", True, fam > 0)
check("E the 5 MSC entities in one family", (5, 1), (len([o for o in ns["MSC_FAMILY"] if o in links]), len(heads)))
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if len(results) - sum(results):
    raise SystemExit(1)
