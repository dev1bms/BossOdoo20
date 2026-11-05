"""Load test on boss20 (go-live tracker P2-15): about 1,500 files created inside a transaction that is rolled back,
then the times of the main lists, a file form and the margin report are measured. Nothing stays in the database
(the file sequence is not consumed: names are given directly). Prints CHECK lines against the target in TARGET_S.
    dev/uat_run.sh check_load_1500.py boss20"""
import time
from datetime import date, timedelta

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, mail_create_nolog=True, mail_notrack=True))  # noqa: F821
TARGET_S = {"list": 3.0, "form": 2.0, "report": 10.0}  # seconds; acceptance target still to be agreed (P2-15 note)
results = []


def check(name, expected, got):
    ok = expected == got
    results.append(ok)
    print(f"CHECK {'PASS' if ok else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def timed(label, fn):
    t0 = time.perf_counter()
    fn()
    s = round(time.perf_counter() - t0, 2)
    print(f"      {label}: {s} s")
    return s


File = env["boss.expediente"]
before = File.search_count([])
customer = env["res.partner"].search([("is_company", "=", True), ("customer_rank", ">", 0)], limit=1) or \
    env["res.partner"].search([("is_company", "=", True)], limit=1)
N = 1500
t0 = time.perf_counter()
vals = []
for i in range(N):
    vals.append({"name": f"[PRUEBA-CARGA] L{i:05d}", "partner_id": customer.id,
                 "direction": "import" if i % 2 else "export", "transport_mode": "sea" if i % 3 else "air",
                 "etd": date.today() - timedelta(days=i % 90), "eta": date.today() - timedelta(days=i % 90) + timedelta(days=20)})
files = File.create(vals)
env.flush_all()
print(f"      created {len(files)} files in {round(time.perf_counter() - t0, 1)} s (files before: {before})")
env.invalidate_all()

list_fields = ["name", "partner_id", "state", "direction", "transport_mode", "etd", "eta", "next_step", "next_step_detail",
               "user_id", "traffic_code"]
list_fields = [f for f in list_fields if f in File._fields]
s_list = timed("files list, 80 rows with next step (as the list view reads)", lambda: File.search_read(
    [], list_fields, limit=80, order="id desc"))
s_list_all = timed("files list, 1,000 rows", lambda: File.search_read([], list_fields, limit=1000, order="id desc"))
s_filter = timed("files filtered by state open, count", lambda: File.search_count([("state", "=", "open")]))
form_fields = [f for f in ("name", "partner_id", "state", "amount_sale", "amount_cost_forecast", "amount_margin_forecast",
                           "next_step", "completeness", "cost_ids", "invoice_ids", "bill_ids", "rating_missing")
               if f in File._fields]
env.invalidate_all()
s_form = timed("one file form (amounts, next step, documents)", lambda: files[-1].read(form_fields))
env.invalidate_all()
s_report = timed("margin report refresh of every open file", lambda: env["boss.margin.report"]._boss_refresh())
s_report_read = timed("margin report list, 80 rows", lambda: env["boss.margin.report"].search_read(
    [], ["expediente_id", "amount_margin_forecast", "amount_margin_final"], limit=80))

check("list of 80 files under target", True, s_list <= TARGET_S["list"])
check("file form under target", True, s_form <= TARGET_S["form"])
check("margin report refresh under target", True, s_report <= TARGET_S["report"])
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed | {N} files | list80 {s_list}s list1000 {s_list_all}s "
      f"count {s_filter}s form {s_form}s report {s_report}s report80 {s_report_read}s")
env.cr.rollback()  # noqa: F821
env.invalidate_all()
assert File.search_count([]) == before, "rollback failed"
print(f"      rolled back: {File.search_count([])} files, as before")
if not all(results):
    raise SystemExit(1)
