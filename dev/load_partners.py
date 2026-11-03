"""Permanent load of the approved Odoo 17 contact scope into boss20 (F2). Runs inside dev/server_shell.sh.
    dev/server_shell.sh load_partners.py <scope.json> dev/migrate_partners.py
Refuses any database other than boss20. Idempotent: records already linked by their Odoo 17 id are not created again.
Only the loader's own log is printed (counts, and the exceptions that need a decision). The commit is explicit."""
import json
import os
from collections import Counter

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
files = [f for f in os.environ.get("BOSS_FILES", "").split("|") if f]
scope_file = next(f for f in files if f.endswith(".json"))
loader_file = next(f for f in files if f.endswith(".py"))
ns = {"env": env, "__name__": "lib"}
exec(compile(open(f"/tmp/boss/{loader_file}", encoding="utf-8").read(), loader_file, "exec"), ns)
expected = len(json.load(open(f"/tmp/boss/{scope_file}", encoding="utf-8"))["records"])
log = ns["load"](env, f"/tmp/boss/{scope_file}")  # noqa: F821
env.flush_all()  # noqa: F821
print("LOAD expected", expected, "created", len(log["created"]), "linked_existing", len(log["linked_existing"]),
      "already_linked", len(log["already_linked"]), "filled", len(log["filled"]), "deferred", len(log["deferred"]),
      "skipped", len(log["skipped"]), "ambiguous", len(log["ambiguous"]))
print("LOAD discarded by field:", dict(Counter(d[1] for d in log["discarded"])))
print("LOAD pending decisions:", sorted(log["pending_decisions"]))
print("LOAD skipped (BOSS children, decision pending):", [s[0] for s in log["skipped"]])
print("LOAD deferred:", [d[0] for d in log["deferred"]])
print("LOAD ambiguous:", log["ambiguous"])
env.cr.commit()  # noqa: F821
print("LOAD committed")
