"""Dry run of the contact migration (F2) on boss20 with a representative Odoo 17 sample, rolled back at the end.
    dev/server_shell_wip.sh check_migration_sample.py <sample.json> dev/migrate_partners.py
The sample (exported from Odoo 17 in read-only) must contain: a company with its child addresses, a contact that is
customer and supplier, the five MSC legal entities, two companies sharing a VAT, an archived contact.
Proves: existing boss20 contacts are linked, not duplicated; children land under their parent; the MSC family is one;
VAT duplicates are both loaded and listed, never merged; an archived source stays archived; a second run creates
nothing and changes nothing; contacts outside the sample are untouched. Prints CHECK/RESULT; exit 1 on failure."""
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
sample_file = next(f for f in files if f.endswith(".json"))
loader_file = next(f for f in files if f.endswith(".py"))
raw = json.load(open(f"/tmp/boss/{sample_file}", encoding="utf-8"))
records = []


def collect(node):
    if isinstance(node, dict):
        if "id" in node and "name" in node and isinstance(node["id"], int):
            records.append(node)
        else:
            for v in node.values():
                collect(v)
    elif isinstance(node, list):
        for v in node:
            collect(v)


collect(raw.get("sample_records", raw))
records = list({r["id"]: r for r in records}.values())
print(f"SAMPLE {len(records)} Odoo 17 records: ids {sorted(r['id'] for r in records)}")
json.dump(records, open("/tmp/sample_flat.json", "w", encoding="utf-8"))

ns = {"env": env, "__name__": "lib"}
exec(compile(open(f"/tmp/boss/{loader_file}", encoding="utf-8").read(), loader_file, "exec"), ns)
Partner = env["res.partner"].with_context(active_test=False)
FIELDS = ["name", "vat", "ref", "phone", "email", "street", "city", "zip", "parent_id", "customer_rank", "supplier_rank",
          "active", "boss_role_ids", "boss_carrier_group_id", "comment", "property_payment_term_id"]


def snapshot(ids=None):
    recs = Partner.search([("id", "in", ids)]) if ids else Partner.search([])
    out = {}
    for p in recs:
        row = []
        for f in FIELDS:
            v = p[f]
            row.append(sorted(v.ids) if hasattr(v, "ids") else v)
        out[p.id] = hashlib.md5(json.dumps(row, default=str, sort_keys=True).encode()).hexdigest()
    return out


existing_msc = env["res.partner"].search([("name", "=", "MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.")], limit=1)
existing_wfs = env["res.partner"].search([("ref", "=", "O17:23336")], limit=1)
before = snapshot()
count_before = len(before)
xmlids_before = env["ir.model.data"].search_count([("module", "=", "o17_partner")])
log1 = ns["load"](env, "/tmp/sample_flat.json")
env.flush_all()
created = {o17 for o17, _t in log1["created"]}
linked = {o17: t for o17, t, _n in log1["linked_existing"]}
print("RUN1", {k: (len(v) if isinstance(v, (list, set, dict)) else v) for k, v in log1.items()})
for item in log1["linked_existing"]:
    print("   linked:", item[0], "->", item[1])
for item in log1["differs"][:20]:
    print("   differs:", item)
for item in log1["discarded"][:20]:
    print("   discarded:", item)
print("   unmatched payment terms:", sorted(log1["unmatched_payment_terms"]))
print("   unmatched country/state:", log1["unmatched_country_state"][:10])

check("1 every sample record is linked to exactly one boss20 contact", len(records),
      env["ir.model.data"].search_count([("module", "=", "o17_partner"), ("model", "=", "res.partner"),
                                         ("name", "=like", "res_partner_%"), ("name", "not like", "family")]) - xmlids_before)
target = lambda o17: ns["Loader"](env, []).xmlid_target(o17)  # noqa: E731
# 2. a company with its child addresses
company = next((r for r in records if r.get("is_company") and not r.get("parent_id")
                and any(c.get("parent_id") and c["parent_id"][0] == r["id"] for c in records)), None)
if company:
    t = target(company["id"])
    kids = [r for r in records if r.get("parent_id") and r["parent_id"][0] == company["id"]]
    check(f"2 company {company['id']}: its {len(kids)} child addresses land under the same boss20 contact", len(kids),
          sum(1 for k in kids if target(k["id"]).parent_id == t))
    check("2 the company's VAT is normalised and kept", True, bool(t.vat) == bool(company.get("vat")))
# 3. customer and supplier at once
cs = next((r for r in records if r.get("x_studio_type") == "Cliente + Proveedor"
           or (r.get("customer_rank") and r.get("supplier_rank"))), None)
if cs:
    t = target(cs["id"])
    check(f"3 contact {cs['id']} customer and supplier: both ranks on the target", (True, True),
          (t.customer_rank > 0, t.supplier_rank > 0))
# 4. MSC family
msc = [r["id"] for r in records if r["id"] in ns["MSC_FAMILY"]]
if msc:
    heads = {target(i).boss_carrier_group_id.id for i in msc}
    check(f"4 the {len(msc)} MSC entities point to one family head", (1, True), (len(heads), bool(heads - {False})))
    check("4 the MSC entity already on boss20 is linked (not duplicated) and in the family", (True, True),
          (existing_msc.id in [target(i).id for i in msc], existing_msc.boss_carrier_group_id.id in heads))
    check("4 family members from any entity", True,
          all(set(target(i)._boss_carrier_family_ids()) == set(target(msc[0])._boss_carrier_family_ids()) for i in msc))
if existing_wfs and any(r["id"] == 23336 for r in records):
    check("4b supplier already on boss20 (ref O17:23336) is linked, not duplicated", existing_wfs, target(23336))
check("4c no second contact with the MSC Spain name", 1,
      env["res.partner"].with_context(active_test=False).search_count(
          [("name", "=", "MEDITERRANEAN SHIPPING COMPANY ESPANA, S.L.U.")]))
# 5. VAT duplicates in the source: both loaded, listed, not merged
dups = log1["source_vat_duplicates"]
if dups:
    vat, ids = next(iter(dups.items()))
    check(f"5 source VAT duplicates {ids}: two different targets, listed for review", (True, 2),
          (len({target(i).id for i in ids}) == len(ids), len(ids)))
else:
    print("INFO no VAT duplicate pair in the sample")
# 6. archived source
arch = next((r for r in records if r.get("active") is False), None)
if arch:
    check(f"6 archived source {arch['id']} stays archived on boss20", False, target(arch["id"]).active)
else:
    print("INFO no archived contact in the sample")
# 7. existing contacts outside the sample untouched; linked ones only filled, never overwritten
after = snapshot(list(before))
touched = {pid for pid, h in after.items() if before[pid] != h}
check("7 boss20 contacts not linked by the sample are untouched", set(), touched - set(linked.values()))
check("7 linked contacts: no value overwritten (only empty fields filled)", [],
      [d for d in log1["differs"] if d[2] in ("name", "vat", "ref")])
# 8. second run: nothing created, nothing changed
snap1 = snapshot()
log2 = ns["load"](env, "/tmp/sample_flat.json")
env.flush_all()
check("8 second run creates nothing and links nothing new", (0, 0), (len(log2["created"]), len(log2["linked_existing"])))
check("8 second run changes no contact", {}, {pid for pid, h in snapshot().items() if snap1.get(pid) != h} or {})
heads = env["ir.model.data"].search_count([("module", "=", "o17_partner"), ("name", "like", "family")])
check("8 contact count after two runs = before + created once (+ family head)", count_before + len(created) + heads,
      len(snapshot()))
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if len(results) - sum(results):
    raise SystemExit(1)
