"""HTTP checks of the customer portal (ADR-010) on boss20 with real portal sessions, AFTER boss_portal is installed.
The web server runs in another process, so the test records are committed: two [PRUEBA] customers, their portal
users (random passwords, never printed), quotations, a file with a published event and document and a tracking link.
At the end the test users are archived, their roles removed and the link revoked (committed); the [PRUEBA] records
stay as test records of boss20. No e-mail is sent (no invitation; users created directly).
Prints «CHECK PASS|FAIL …» and «RESULT n passed, m failed».
    dev/uat_run.sh check_portal_http.py boss20"""
import re
import secrets
from datetime import date, timedelta

import requests

from odoo import Command

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US", no_reset_password=True))  # noqa: F821
assert env["ir.module.module"].search_count([("name", "=", "boss_portal"), ("state", "=", "installed")]), \
    "boss_portal is not installed: nothing to check over HTTP"
BASE = "http://odoo:8069"
RUN = secrets.token_hex(3)
DUMP = False  # True (never committed) prints the HTML served to the portal sessions, base64, for a visual check
results = []


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


ref = env.ref
Partner, Users, Order = env["res.partner"], env["res.users"], env["sale.order"]
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
dv, hc = ref("boss_pricing.container_type_dv"), ref("boss_pricing.container_type_hc")
passwords = {}


def company(name):
    return Partner.create({"name": f"[PRUEBA] {name} {RUN}", "is_company": True, "country_id": ref("base.es").id})


def portal_user(key, parent, role, customer):
    contact = Partner.create({"name": f"[PRUEBA] {key} {RUN}", "parent_id": parent.id, "email": f"{key}.{RUN}@example.invalid",
                              "boss_portal_role": role, "boss_portal_customer_id": customer.id if customer else False})
    passwords[key] = secrets.token_urlsafe(16)
    return Users.create({"login": f"prueba_{key}_{RUN}", "partner_id": contact.id, "password": passwords[key],
                         "group_ids": [Command.set([ref("base.group_portal").id])]})


def quotation(customer, rate=False, lines=()):
    return Order.create({
        "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
        "boss_carrier_id": 6, "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id,
        "boss_destination_port_id": port("ESVLC", "sea").id, "boss_eta": date(2026, 12, 5), "boss_rate_quotation": rate,
        "validity_date": date.today() + timedelta(days=10), "require_signature": True,
        "boss_container_ids": [] if rate else [Command.create({"size": "40", "container_type_id": dv.id, "quantity": 1})],
        "order_line": [Command.create({"product_id": product(code).id, "product_uom_id": product(code).uom_id.id,
                                       "boss_container_size": size, "boss_container_type_id": ctype.id if ctype else False})
                       for code, size, ctype in lines]})


# --- set up (committed) -------------------------------------------------------------------------------------------------
cust_a, cust_b = company("Portal HTTP A"), company("Portal HTTP B")
users = {"a_track": portal_user("a_track", cust_a, "tracking", cust_a), "a_comm": portal_user("a_comm", cust_a, "commercial", cust_a),
         "a_appr": portal_user("a_appr", cust_a, "approver", cust_a), "b_comm": portal_user("b_comm", cust_b, "commercial", cust_b)}
so_a = quotation(cust_a, lines=[("THC", "40", dv), ("BL", False, None)])
so_b = quotation(cust_b, lines=[("THC", "40", dv)])
rate = quotation(cust_a, rate=True, lines=[("THC", "20", dv), ("THC", "40", dv), ("THC", "40", hc), ("BL", False, None)])
for o in (so_a, so_b, rate):
    o.order_line.filtered(lambda l: not l.display_type).write({"price_unit": 300.0})
    o.write({"state": "sent"})
    o._portal_ensure_token()
rate_hc = rate.order_line.filtered(lambda l: l.boss_container_type_id == hc)
rate_hc.price_unit = 310.0
so_file = quotation(cust_a, lines=[("THC", "40", dv)])
so_file.order_line.write({"price_unit": 280.0})
so_file.action_confirm()
file = so_file.boss_expediente_id
file.write({"etd": date(2026, 11, 20), "eta": date(2026, 12, 5), "hbl_ref": f"[PRUEBA] HBL-{RUN}", "mbl_ref": f"[PRUEBA] MBL-{RUN}"})
env["boss.expediente.event"].create({"expediente_id": file.id, "name": "Interno", "note": f"[PRUEBA] secreto-{RUN}"})
env["boss.expediente.event"].create({"expediente_id": file.id, "name": "Salida", "kind": "milestone", "portal_published": True,
                                     "portal_text": f"Loaded on board {RUN}"})
doc = env["ir.attachment"].create({"name": f"[PRUEBA] aviso {RUN}.pdf", "res_model": "boss.expediente", "res_id": file.id,
                                   "raw": b"%PDF-1.4 prueba portal"})
internal_doc = env["ir.attachment"].create({"name": f"[PRUEBA] interno {RUN}.pdf", "res_model": "boss.expediente",
                                            "res_id": file.id, "raw": b"interno"})
file.portal_attachment_ids = [Command.link(doc.id)]
file.action_boss_share_tracking()
token = file.portal_tracking_token
thc_line = so_a.order_line.filtered(lambda l: l.product_id.default_code == "THC")
env.cr.commit()  # noqa: F821  the web process needs the records


def session(key=None):
    s = requests.Session()
    if key:
        page = s.get(f"{BASE}/web/login", timeout=30).text
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        s.post(f"{BASE}/web/login", data={"login": users[key].login, "password": passwords[key], "csrf_token": csrf,
                                         "redirect": "/my"}, timeout=30)
    return s


def rpc(s, model, method, args, kwargs=None):
    r = s.post(f"{BASE}/web/dataset/call_kw/{model}/{method}", json={
        "jsonrpc": "2.0", "method": "call", "params": {"model": model, "method": method, "args": args, "kwargs": kwargs or {}}},
        timeout=30)
    return r.json()


try:
    s = {k: session(k) for k in users}
    anon = session()
    check("0 the four portal users log in", [True] * 4, [("session_id" in x.cookies) and x.get(f"{BASE}/my", timeout=30).status_code == 200 for x in s.values()])
    quotes = {k: x.get(f"{BASE}/my/quotes", timeout=30).text for k, x in s.items()}
    check("1 /my/quotes: commercial A lists A's quotations, not B's", (True, False), (so_a.name in quotes["a_comm"], so_b.name in quotes["a_comm"]))
    check("1 /my/quotes: tracking A lists no quotation; B lists only B's", (False, True, False),
          (so_a.name in quotes["a_track"], so_b.name in quotes["b_comm"], so_a.name in quotes["b_comm"]))
    r = s["b_comm"].get(f"{BASE}/my/orders/{so_a.id}", timeout=30, allow_redirects=False)
    check("1 B opening A's quotation by id is sent away", True, r.status_code in (302, 303) and "/my/orders" not in r.headers.get("Location", ""))
    res = rpc(s["a_comm"], "sale.order.line", "read", [thc_line.ids, ["price_unit", "boss_cost_amount"]])
    check("2 RPC read of a cost field by commercial A is refused", True, "error" in res)
    res = rpc(s["a_comm"], "sale.order.line", "read", [thc_line.ids, ["price_unit"]])
    check("2 RPC read of the selling price by commercial A works", 300.0, (res.get("result") or [{}])[0].get("price_unit"))
    res = rpc(s["a_comm"], "boss.tariff", "search_read", [[]], {"fields": ["name"], "limit": 1})
    check("2 RPC on supplier tariffs is refused", True, "error" in res)
    page = s["a_comm"].get(f"{BASE}/my/orders/{rate.id}", timeout=30).text
    thc_label = rate.order_line.filtered(lambda l: not l.display_type)[:1].with_context(lang=cust_a.lang or "es_ES").label
    check("3b rate quotation page: every rate names its service (Odoo 20 line label), no down payment, Spanish captions",
          (True, False, True), (bool(thc_label) and thc_label.splitlines()[0] in page, "Down payment" in page or "Anticipo" in page,
                                "Oferta de tarifas para" in page))
    i = page.find("o_portal_sale_sidebar")
    print("DIAG sidebar:", re.sub(r"\s+", " ", page[max(i - 200, 0):i + 300]))
    j = page.find("<h2")
    print("DIAG first h2:", re.sub(r"\s+", " ", page[j:j + 200]))
    check("3 rate quotation page: three alternatives with their basis, rates, no total, no signature",
          (True, True, True, True, False, False),
          ("20' DV" in page, "40' DV" in page, "40' HC" in page, "Rates" in page or "Tarifas" in page, "Untaxed Amount" in page,
           "Sign &amp; Pay" in page or "modalaccept" in page and "Accept &amp; Sign" in page))
    check("3 no hypothetical total in the page data (attribute absent or 0), «Tax Included» replaced", (True, False),
          ("data-order-amount-total" not in page or 'data-order-amount-total="0' in page, "Tax Included" in page))
    html = s["a_comm"].get(f"{BASE}/my/orders/{rate.id}?report_type=html", timeout=60).text
    check("3 rate quotation document: basis per line, no total table", (True, False), ("40' HC" in html, "o_total_table" in html))
    normal = s["a_comm"].get(f"{BASE}/my/orders/{so_a.id}?report_type=html", timeout=60).text
    check("3 a shipment quotation keeps its totals", True, "o_total_table" in normal)
    accept = lambda x, o, tok=None: x.post(f"{BASE}/my/orders/{o.id}/accept", json={"jsonrpc": "2.0", "method": "call", "params": {  # noqa: E731
        "access_token": tok, "name": "Prueba", "signature": "iVBORw0KGgo="}}, timeout=30).json()
    check("4 commercial A cannot accept; the token link (logged out) cannot accept", (True, True),
          ("error" in (accept(s["a_comm"], so_a).get("result") or {}), "error" in (accept(anon, so_a, so_a.access_token).get("result") or {})))
    tx = anon.post(f"{BASE}/my/orders/{so_a.id}/transaction", json={"jsonrpc": "2.0", "method": "call", "params": {
        "access_token": so_a.access_token, "amount": 1}}, timeout=30).json()
    check("4 the token link cannot start a payment", True, "error" in tx)
    book = lambda k, qty: s[k].post(f"{BASE}/my/orders/{rate.id}/boss_booking", data={  # noqa: E731
        "csrf_token": re.search(r'name="csrf_token" value="([^"]+)"', s[k].get(f"{BASE}/my/orders/{rate.id}", timeout=30).text).group(1),
        f"qty_{rate_hc.id}": str(qty)}, timeout=30, allow_redirects=False)
    r = book("a_comm", 1)
    check("5 commercial A: booking refused (authorised representative only)", True, "boss_booking_error" in r.headers.get("Location", ""))
    r = book("a_appr", 2)
    env.cr.commit()  # noqa: F821  new snapshot: see what the web process committed
    rate.invalidate_recordset()
    check("5 approver A: booking request sent, quotation not confirmed, no file", (True, "requested", "sent", False),
          ("boss_booking=sent" in r.headers.get("Location", ""), rate.boss_booking_state, rate.state, bool(rate.boss_expediente_id)))
    r = book("a_appr", 1)
    check("5 a second request while pending is refused", True, "boss_booking_error" in r.headers.get("Location", ""))
    ships = s["a_track"].get(f"{BASE}/my/shipments", timeout=30).text
    check("6 tracking A sees A's shipment; B does not", (True, False), (file.name in ships, file.name in s["b_comm"].get(f"{BASE}/my/shipments", timeout=30).text))
    detail = s["a_track"].get(f"{BASE}/my/shipments/{file.id}", timeout=30).text
    check("6b shipment page in the customer's language: status and date badges in Spanish, no English captions",
          (True, True, False, False), ("Reservado" in detail, "Previsto" in detail, ">Booked<" in detail,
                                       "Last update recorded" in detail))
    check("6 detail: published event, house B/L, estimated dates; no internal note, no master B/L",
          (True, True, True, False, False),
          (f"Loaded on board {RUN}" in detail, f"HBL-{RUN}" in detail, "Estimated" in detail, f"secreto-{RUN}" in detail, f"MBL-{RUN}" in detail))
    check("6 B opening A's shipment gets 404", 404, s["b_comm"].get(f"{BASE}/my/shipments/{file.id}", timeout=30).status_code)
    d = s["a_track"].get(f"{BASE}/my/shipments/{file.id}/documents/{doc.id}", timeout=30)
    check("7 the published document downloads for A", (200, b"%PDF-1.4 prueba portal"), (d.status_code, d.content))
    check("7 an unpublished document of the same file: 404; B: 404; direct /web/content: refused", (404, 404, True),
          (s["a_track"].get(f"{BASE}/my/shipments/{file.id}/documents/{internal_doc.id}", timeout=30).status_code,
           s["b_comm"].get(f"{BASE}/my/shipments/{file.id}/documents/{doc.id}", timeout=30).status_code,
           s["a_track"].get(f"{BASE}/web/content/{doc.id}", timeout=30).status_code in (403, 404)))
    t = anon.get(f"{BASE}/boss/track/{token}", timeout=30)
    check("8 tracking link: shipment shown without parties, references or documents",
          (200, True, False, False, False), (t.status_code, f"Loaded on board {RUN}" in t.text, cust_a.name in t.text,
                                             f"HBL-{RUN}" in t.text, "aviso" in t.text))
    check("8 a wrong token: 404", 404, anon.get(f"{BASE}/boss/track/{token[:-2]}xx", timeout=30).status_code)
    file.action_boss_revoke_tracking()
    env.cr.commit()  # noqa: F821
    check("8 a revoked link: 404", 404, anon.get(f"{BASE}/boss/track/{token}", timeout=30).status_code)
    if DUMP:
        import base64
        pages = {"shipments": (s["a_track"], "/my/shipments"), "shipment": (s["a_track"], f"/my/shipments/{file.id}"),
                 "rate_quotation": (s["a_comm"], f"/my/orders/{rate.id}"), "quotes": (s["a_comm"], "/my/quotes"),
                 "home": (s["a_comm"], "/my/home")}
        for name, (sess, path) in pages.items():
            html = sess.get(f"{BASE}{path}", timeout=60).text
            print(f"PAGE-BEGIN {name} {path}")
            print(base64.b64encode(html.encode()).decode())
            print(f"PAGE-END {name}")
    users["a_comm"].partner_id.boss_portal_role = False
    env.cr.commit()  # noqa: F821
    check("9 role removed: commercial A no longer lists A's quotations", False, so_a.name in s["a_comm"].get(f"{BASE}/my/quotes", timeout=30).text)
finally:
    for user in users.values():
        user.partner_id.write({"boss_portal_role": False, "boss_portal_customer_id": False})
        user.active = False
    file.action_boss_revoke_tracking()
    env.cr.commit()  # noqa: F821
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
