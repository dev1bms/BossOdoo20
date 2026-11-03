"""[PRUEBA] files modelled on real Odoo 17 cases (docs/hoja-de-ruta.md, item 2), on boss20.

Each case is a quotation of a real customer already on boss20 with the route, parties, cargo and services of the Odoo 17
file it copies (dates moved to the coming weeks). No Odoo 17 amount is copied: costs come from the boss20 tariffs; where
none exists the line is «cost on request» (named supplier without price, M2-19) or, for freight, a fictitious amount
typed as manual cost. Selling prices come from the pricelists (BOSS's Odoo 17 prices since 03/11/2026, item 3): the
customer's agreed prices, the general «Standard» prices, else cost + %; a service still without one gets a fictitious
typed price of 100 for the whole service. Every such step is printed as MANUAL.
    IMB-FCL  sea import FCL, model E260883 (Xingang → Valencia, 1×20' DV + 1×40' HC, MSC, origin agent)
    IAB      air import, model E260167 (Guangzhou → Madrid, Qatar Airways, handler WFS)
    EMB-LCL  sea export LCL, model E260769 (Algeciras → Conakry, MSC)
    IMA-LCL  sea import LCL for an agent, model E250834 (Hong Kong → Valencia)

MODE «dry»: everything rolled back. MODE «commit»: the quotations are kept (idempotent: a case whose quotation exists,
by its customer reference, is reused) and accepted, so each file shows its next step. Then each file is walked with
«Siguiente paso» up to the financial close (RFQs confirmed, in transit, arrived, delivered, services performed, customer invoice
and supplier bills posted) inside a savepoint that is rolled back: the kept file stays where acceptance left it. Payments
are not repeated here (dev/check_file_e2e.py proves them). Sequence numbers used by the walk are not given back.
Prints «CASE …», «LINE …», «MANUAL …», «GAP …», «WALK …», «CHECK PASS|FAIL …» and «RESULT …», never an amount of a
boss20 tariff or pricelist (real prices).
    dev/uat_run.sh sample_real_cases.py boss20"""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
MODE = "commit"
belal = env["res.users"].search([("login", "=", "devbms")], limit=1)  # noqa: F821
env = env(user=belal, context=dict(env.context, tracking_disable=True, lang="en_US"))  # noqa: F821
ref = env.ref
o17 = lambda i: ref(f"o17_partner.res_partner_{i}")  # noqa: E731
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
template = lambda code: env["sale.order.template"].search([("name", "=like", f"{code} · %")], limit=1)  # noqa: E731
gaps, manual_steps = [], []
ERRORS = (UserError, ValidationError, AccessError)


def gap(case, text):
    gaps.append((case, text))
    print(f"GAP {case}: {text}")


def manual(case, text):
    manual_steps.append((case, text))
    print(f"MANUAL {case}: {text}")


MSC, ADUCEX, PORTEVER, SINOTECH, QATAR, WFS, BARBICAN = (o17(23762), o17(22998), o17(38815), o17(38861), o17(23150),
                                                        o17(23336), o17(23007))
CASES = [
    {"key": "IMB-FCL", "model": "E260883", "customer": o17(23155), "template": "IMB FOB", "carrier": MSC,
     "origin": ("CN", "CNXGG", "sea"), "destination": ("ES", "ESVLC", "sea"),
     "etd": date(2026, 11, 12), "eta": date(2026, 12, 16), "containers": [("20", "dv"), ("40", "hc")],
     "cargo": {"boss_goods_description": "[PRUEBA] Extintores", "boss_packages": 30, "boss_package_type": "CT",
               "boss_gross_kg": 35700.0, "boss_volume_m3": 60.0},
     "suppliers": {"FMI": PORTEVER, "THC": MSC, "BL": MSC, "GLO-CCC": MSC, "T3-PAD": MSC, "FAD": ADUCEX,
                   "TTE-FCL": MSC},
     "manual_cost": {"FMI": 1000.0}},
    {"key": "IAB", "model": "E260167", "customer": o17(23012), "template": "IAB FOB", "carrier": QATAR,
     "origin": ("CN", "CAN", "air"), "destination": ("ES", "MAD", "air"),
     "etd": date(2026, 11, 17), "eta": date(2026, 11, 18), "containers": [],
     "cargo": {"boss_goods_description": "[PRUEBA] Latiguillos de fibra (patchcord)", "boss_packages": 14,
               "boss_package_type": "CT", "boss_gross_kg": 172.0, "boss_volume_m3": 0.83},
     "suppliers": {"FAI": SINOTECH, "HAN": WFS, "AWB": WFS, "ETX": WFS, "FAD": ADUCEX, "TTE-CON": BARBICAN},
     "manual_cost": {"FAI": 4.0}},
    {"key": "EMB-LCL", "model": "E260769", "customer": o17(23014), "template": False, "carrier": MSC,
     "direction": "export", "mode": "sea", "load": "lcl",
     "origin": ("ES", "ESALG", "sea"), "destination": ("GN", "GNCKY", "sea"),
     "etd": date(2026, 11, 20), "eta": date(2026, 11, 28), "containers": [],
     "cargo": {"boss_goods_description": "[PRUEBA] Material de bricolaje", "boss_packages": 4,
               "boss_package_type": "PL", "boss_gross_kg": 1800.0, "boss_volume_m3": 6.0},
     "lines": ["FME-LCL", "DEX", "CSM"],
     "suppliers": {"FME-LCL": MSC, "DEX": ADUCEX},
     "manual_cost": {"FME-LCL": 50.0}},
    {"key": "IMA-LCL", "model": "E250834", "customer": o17(23584), "template": False, "carrier": False,
     "business": "agent", "direction": "import", "mode": "sea", "load": "lcl",
     "origin": ("HK", "HKHKG", "sea"), "destination": ("ES", "ESVLC", "sea"),
     "etd": date(2026, 11, 5), "eta": date(2026, 12, 10), "containers": [],
     "cargo": {"boss_goods_description": "[PRUEBA] Libros", "boss_packages": 3, "boss_package_type": "PL",
               "boss_gross_kg": 900.0, "boss_volume_m3": 2.5},
     "lines": ["THC-LCL", "FAD", "TTE-CON", "CSM"],
     "suppliers": {"FAD": ADUCEX, "TTE-CON": BARBICAN},
     "walk_suppliers": {"THC-LCL": 23073},  # the CFS that handled E250834 in Odoo 17 (TRANSGLORY), chosen on the file
     "manual_cost": {}},
]


def air_port(code):
    found = env["boss.port"].search([("kind", "=", "air"), "|", ("code", "=", code), ("code", "=like", f"%{code}")],
                                    limit=1)
    return found


def build(case):
    """The quotation of the case (reused when it exists, by its customer reference)."""
    key = case["key"]
    reference = f"[PRUEBA] caso real {case['model']} ({key})"
    order = env["sale.order"].search([("client_order_ref", "=", reference), ("state", "!=", "cancel")], limit=1)
    if order:
        print(f"CASE {key}: quotation {order.name} reused")
        return order
    origin_country, origin_code, kind = case["origin"]
    destination_country, destination_code, _kind = case["destination"]
    find = air_port if kind == "air" else (lambda code: port(code, "sea"))
    with Form(env["sale.order"]) as form:
        form.partner_id = case["customer"]
        if case.get("template"):
            form.sale_order_template_id = template(case["template"])
        else:
            form.boss_direction = case["direction"]
            form.boss_transport_mode = case["mode"]
            form.boss_load_type = case["load"]
        if case.get("business"):
            form.boss_business = case["business"]
        if case.get("carrier"):
            form.boss_carrier_id = case["carrier"]
        form.boss_origin_country_id = ref(f"base.{origin_country.lower()}")
        form.boss_origin_port_id = find(origin_code)
        form.boss_destination_country_id = ref(f"base.{destination_country.lower()}")
        form.boss_destination_port_id = find(destination_code)
        form.boss_etd = case["etd"]
        form.boss_eta = case["eta"]
        form.client_order_ref = reference
        for size, ctype in case["containers"]:
            with form.boss_container_ids.new() as container:
                container.size = size
                container.container_type_id = ref(f"boss_pricing.container_type_{ctype}")
    order = form.save()
    order.write(case["cargo"])
    for code in case.get("lines", []):
        order.write({"order_line": [Command.create({"product_id": product(code).id,
                                                    "product_uom_id": product(code).uom_id.id})]})
    for code, partner in case["suppliers"].items():
        order.order_line.filtered(lambda l, c=code: l.product_id.default_code == c).boss_supplier_id = partner
    for code, amount in case["manual_cost"].items():
        order.order_line.filtered(lambda l, c=code: l.product_id.default_code == c).write(
            {"boss_manual_cost": amount, "boss_manual_cost_note": "[PRUEBA] importe ficticio, no es el de Odoo 17"})
        manual(key, f"{code}: fictitious freight cost typed (no freight rate for this route on boss20)")
    order.action_boss_update_costs()
    print(f"CASE {key}: quotation {order.name} created for {order.partner_id.name} ({order.boss_traffic_code})")
    return order


def report(case, order):
    key = case["key"]
    for line in order.order_line.filtered("product_id"):
        # statuses only: the amounts are boss20's real tariffs and selling prices (never in the evidence or Git)
        print(f"LINE {key} {line.product_id.default_code:8} {line.boss_container_size or '-':2} supplier "
              f"{(line.boss_supplier_id.name or '-')[:22]:22} cost {line.boss_cost_status:16} sale "
              f"{line.boss_sale_status:10} vat {line.boss_vat_status}")
    on_request = order.order_line.filtered(lambda l: l.boss_cost_status == "no_tariff" and l.boss_supplier_id)
    if on_request:
        on_request.write({"boss_cost_on_request": True})
        manual(key, f"cost on request (supplier named, no price on boss20): "
                    f"{', '.join(on_request.mapped('product_id.default_code'))}")
    missing = order.order_line.filtered(lambda l: l.product_id and l.boss_sale_status == "missing")
    for line in missing:  # 100 EUR for the whole service, whatever its unit (per kg, per W/M, per container…)
        line.price_unit = round(100.0 / (line.product_uom_qty or 1.0), 4)
    if missing:
        manual(key, f"selling price typed, fictitious 100 EUR per service (no price list for it yet: item 3): "
                    f"{', '.join(missing.mapped('product_id.default_code'))}")
    for line in order.order_line.filtered(lambda l: l.product_id and l.boss_cost_status not in (
            "ok", "manual", "no_tariff") and not l.boss_cost_on_request):
        gap(key, f"{line.product_id.default_code} cost «{line.boss_cost_status}»: "
                 f"{(line.boss_cost_explanation or '').splitlines()[0][:120] if 'boss_cost_explanation' in line._fields else ''}")


class _Undo(Exception):
    pass


checks = []
purchase_0 = env["account.tax"].search([("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                                         ("company_id", "=", env.company.id)], limit=1)


def check(name, expected, got):
    checks.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def accept(case, order):
    """Accept when nothing blocks; a cost still unknown gets the sales manager's documented reason (B22)."""
    key = case["key"]
    unknown = order.order_line.filtered(lambda l: l.product_id and l.boss_cost_kind == "unknown"
                                        and not l.boss_unknown_cost_reason)
    for line in unknown:
        reason = ("[PRUEBA] tarifa del proveedor pendiente de aprobación (punto 38)"
                  if line.boss_cost_status == "pending_approval" else "[PRUEBA] proveedor por elegir")
        line.boss_unknown_cost_reason = reason
    if unknown:
        manual(key, f"sales manager records why it is accepted with the cost unknown: "
                    f"{', '.join(unknown.mapped('product_id.default_code'))}")
    try:
        with env.cr.savepoint():
            order.action_confirm()
    except ERRORS as exc:
        gap(key, "not accepted: " + " ".join(str(exc).split())[:300])


def walk(case, file):
    """Every next step of the file, pressed with «Go» or done the way a person does it, up to the financial close;
    rolled back (the committed file stays where acceptance left it)."""
    key = case["key"]
    seen = []
    air = file.transport_mode == "air"
    try:
        with env.cr.savepoint():
            for _i in range(16):
                env.invalidate_all()
                step = file.next_step
                seen.append(step)
                if step in ("done", False):
                    break
                if step == "choose_supplier":
                    for need in file.cost_ids.filtered(lambda n: n.state == "no_supplier"):
                        code = need.product_id.default_code
                        if code not in case.get("walk_suppliers", {}):
                            gap(key, f"walk: no supplier known for {code}")
                            raise _Undo
                        need.partner_id = o17(case["walk_suppliers"][code])
                        manual(key, f"walk: operations chooses the supplier of {code} as in the real file "
                                    f"({need.partner_id.name})")
                elif step == "type_cost":
                    file.cost_ids.filtered("cost_unknown").write({"expected_unit_cost": 50.0})
                elif step == "confirm_rfq":
                    for po in file.purchase_order_ids.filtered(lambda p: p.state in ("draft", "sent")):
                        po.partner_ref = f"[PRUEBA] conf. {key}"
                        po.button_confirm()
                elif step == "in_transit":
                    file.write({"booking_ref": f"[PRUEBA] BK-{key}", "atd": case["etd"],
                                ("mawb_ref" if air else "mbl_ref"): f"[PRUEBA] M-{key}",
                                ("hawb_ref" if air else "hbl_ref"): f"[PRUEBA] H-{key}"})
                    file.action_next_step()
                elif step == "arrived":
                    file.ata = case["eta"]  # typing the ATA marks the file arrived (F0-C22)
                elif step == "delivered":
                    file.write({"ata": case["eta"], "discharge_date": case["eta"], "pickup_date": case["etd"],
                                "delivery_date": case["eta"], "customs_ref": f"[PRUEBA] DUA-{key}",
                                "customs_channel": "green", "customs_release_date": case["eta"],
                                "hbl_release": "released" if file.transport_mode == "sea" else False})
                    file.action_next_step()
                elif step == "perform":
                    file.cost_ids.filtered(lambda n: n.state == "ordered").action_mark_performed()
                elif step == "invoice":
                    wizard = env["boss.invoice.services"].create({
                        "expediente_id": file.id,
                        "allocation_ids": [Command.set(file.allocation_ids.filtered(
                            lambda a: a.to_invoice_quantity > 0).ids)]})
                    invoice = env["account.move"].browse(wizard.action_create()["res_id"])
                    invoice.invoice_date = case["eta"]
                    invoice.action_post()
                elif step == "bills":
                    orders = file.purchase_order_ids.filtered(
                        lambda p: p.state == "purchase" and p.invoice_status == "to invoice")
                    if not orders:
                        gap(key, "walk: cost still expected without a purchase order to bill")
                        break
                    for po in orders:
                        po.action_create_invoice()
                        bill = po.invoice_ids.filtered(lambda m: m.state == "draft")[:1]
                        bill.write({"invoice_date": case["eta"], "ref": f"[PRUEBA] {key} {po.name}"})
                        bill.invoice_line_ids.tax_ids = purchase_0
                        bill.action_post()
                elif step == "review":
                    to_review = file.cost_ids.filtered("variance_to_review")
                    if not to_review:
                        gap(key, "walk: review without a variance")
                        break
                    to_review.write({"variance_reviewed": True, "variance_note": "[PRUEBA] revisado"})
                elif step == "close_operations":
                    if file._boss_margin_warnings():
                        try:
                            with env.cr.savepoint():
                                file.action_close_operations()
                            blocked = False
                        except UserError:
                            blocked = True
                        check(f"{key} operations do not close with a margin below the minimum until a manager writes why",
                              True, blocked)
                        file.sudo().margin_exception_reason = "[PRUEBA] coste ficticio de la prueba"
                        manual(key, "walk: a sales manager writes why it closes with a low margin")
                    file._boss_sync_ratings()  # F0-C66: the parties are rated before closing (as in Odoo 17)
                    file.rating_ids.filtered(lambda r: not r.rating).write({"rating": "8"})
                    file.action_next_step()
                else:  # order, close_financial
                    file.action_next_step()
                env.invalidate_all()
                if file.next_step == step:
                    gap(key, f"walk: «{step}» did not move on")
                    break
            raise _Undo
    except _Undo:
        env.invalidate_all()
        print(f"WALK {key}: " + " → ".join(str(s) for s in seen))
        check(f"{key} walked with «Siguiente paso» from acceptance to the financial close", "done", seen[-1])
    except ERRORS as exc:
        env.invalidate_all()
        gap(key, f"walk stopped at «{seen[-1]}»: " + " ".join(str(exc).split())[:250])
        check(f"{key} walked with «Siguiente paso» from acceptance to the financial close", "done", seen[-1])


results = []
for case in CASES:
    order = build(case)
    if order.state in ("draft", "sent"):
        report(case, order)
        accept(case, order)
    file = order.boss_expediente_id
    print(f"CASE {case['key']}: {order.name} {order.state} file {file.name or '-'} next step {file.next_step or '-'} "
          f"({file.next_step_detail or ''})")
    if file:
        walk(case, file)
        env.invalidate_all()
    results.append((case["key"], order.name, order.state, file.name or "-", file.next_step or "-"))

if MODE == "commit":
    env.cr.commit()
else:
    env.cr.rollback()
print(f"RESULT {sum(checks)} passed, {len(checks) - sum(checks)} failed, {len(gaps)} gaps, {len(manual_steps)} manual "
      f"steps | mode {MODE} | " + " | ".join(" ".join(r) for r in results))
