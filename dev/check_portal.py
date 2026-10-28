"""Checks of the customer portal (ADR-010) on boss20, as real portal users (never only the superuser).
Part 1 (always): BOSS costs are refused to portal users at field level (read, search, search_read, export).
Part 2 (when boss_portal is installed): roles and scope per legal entity, invoices without vendor bills, no purchases,
who may sign/pay, booking request, shipments whitelist, published events and documents, tracking token, revocation.
Every record is made here and rolled back (the HTTP pages are checked by dev/check_portal_http.py).
Prints «CHECK PASS|FAIL|SKIP …» and «RESULT n passed, m failed».
    dev/uat_run.sh check_portal.py boss20"""
from datetime import date, timedelta

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError

assert env.cr.dbname == "boss20", env.cr.dbname  # noqa: F821
env = env(context=dict(env.context, tracking_disable=True, lang="en_US", no_reset_password=True))  # noqa: F821
results = []


def check(name, expected, got):
    results.append(expected == got)
    print(f"CHECK {'PASS' if expected == got else 'FAIL'} {name}: expected {expected!r} got {got!r}")


def refused(fn):
    """True when the call is refused; the attempt is rolled back (savepoint) so it leaves nothing behind."""
    try:
        with env.cr.savepoint():
            fn()
            env.flush_all()
        return False
    except (AccessError, UserError, ValidationError):
        env.invalidate_all()
        return True


ref = env.ref
port = lambda code, kind: env["boss.port"].search([("code", "=", code), ("kind", "=", kind)], limit=1)  # noqa: E731
product = lambda code: env["product.product"].search([("default_code", "=", code)], limit=1)  # noqa: E731
Partner, Users, Order = env["res.partner"], env["res.users"], env["sale.order"]
dv, hc = ref("boss_pricing.container_type_dv"), ref("boss_pricing.container_type_hc")
msc = Partner.browse(6)
portal_group = ref("base.group_portal")
installed = bool(env["ir.module.module"].search_count([("name", "=", "boss_portal"), ("state", "=", "installed")]))


def company(name):
    return Partner.create({"name": f"[PRUEBA] {name}", "is_company": True, "country_id": ref("base.es").id,
                           "vat": "ESB12345674"})


def portal_user(login, parent, **partner_values):
    contact = Partner.create(dict({"name": f"[PRUEBA] {login}", "parent_id": parent.id, "email": f"{login}@example.invalid"},
                                  **partner_values))
    return Users.create({"login": f"prueba_{login}", "partner_id": contact.id,
                         "group_ids": [Command.set([portal_group.id])]})


def quotation(customer, rate=False, lines=("THC", "BL"), containers=1):
    return Order.create({
        "partner_id": customer.id, "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
        "boss_carrier_id": msc.id, "boss_origin_country_id": ref("base.cn").id, "boss_origin_port_id": port("CNSHA", "sea").id,
        "boss_destination_port_id": port("ESVLC", "sea").id, "boss_eta": date(2026, 12, 5), "boss_rate_quotation": rate,
        "validity_date": date.today() + timedelta(days=10),
        "boss_container_ids": [Command.create({"size": "40", "container_type_id": dv.id, "quantity": containers})] if containers else [],
        "order_line": [Command.create({"product_id": product(c).id, "product_uom_id": product(c).uom_id.id,
                                       "boss_container_size": "40" if product(c).uom_id.boss_quantity_source == "container" else False,
                                       "boss_container_type_id": dv.id if product(c).uom_id.boss_quantity_source == "container" else False,
                                       "price_unit": 300.0}) for c in lines]})


cust_a, cust_b = company("Portal cliente A"), company("Portal cliente B")
so_a = quotation(cust_a)
so_a.action_quotation_sent() if hasattr(so_a, "action_quotation_sent") else so_a.write({"state": "sent"})

# --- part 1: confidentiality at field level (standard portal access to the customer's own quotation) -----------------
user_a = portal_user("a_comercial", cust_a)
line = so_a.order_line.filtered(lambda l: l.product_id.default_code == "THC")
check("1 THC line has a supplier cost (253 from MSC)", ("ok", True), (line.boss_cost_status, line.boss_cost_amount > 0))
if installed:
    user_a.partner_id.write({"boss_portal_role": "commercial", "boss_portal_customer_id": cust_a.id})
as_a = line.with_user(user_a)
check("1 the portal user reads the selling price of his own line", line.price_unit, as_a.read(["price_unit"])[0]["price_unit"])
protected = ["purchase_price", "margin", "margin_percent", "boss_supplier_id", "boss_execution", "boss_cost_kind",
             "boss_cost_status", "boss_cost_amount", "boss_cost_currency_id", "boss_tariff_line_id", "boss_cost_candidate_ids",
             "boss_cost_missing", "boss_cost_steps", "boss_cost_is_estimate", "boss_cost_explanation", "boss_manual_cost",
             "boss_manual_cost_note", "boss_sale_status", "boss_sale_explanation", "boss_markup", "boss_vat_trace",
             "boss_unknown_cost_reason", "boss_cost_on_request", "boss_allocation_ids"]
leaked = [f for f in protected if not refused(lambda f=f: as_a.read([f]))]
check(f"1 every buying-side field of the line is refused on read ({len(protected)} fields)", [], leaked)
check("1 the cost fields are not even listed to the portal user (fields_get)", [],
      [f for f in protected if f in line.with_user(user_a).fields_get()])
check("1 search_read and a search on the cost are refused", (True, True),
      (refused(lambda: env["sale.order.line"].with_user(user_a).search_read([("order_id", "=", so_a.id)], ["boss_cost_amount"])),
       refused(lambda: env["sale.order.line"].with_user(user_a).search([("boss_cost_amount", ">", 0)]))))
check("1 export of the cost is refused", True, refused(lambda: as_a.export_data(["boss_cost_amount"])))
order_protected = ["margin", "boss_pricing_alert", "boss_snapshot_ids", "boss_haulier_id"]
check("1 quotation-level internal fields are refused (margin, pricing alert, snapshots, haulier)", [],
      [f for f in order_protected if not refused(lambda f=f: so_a.with_user(user_a).read([f]))])
check("1 no access to snapshots, tariffs, tariff prices, files, cost needs", [True] * 5,
      [refused(lambda m=m: env[m].with_user(user_a).search([], limit=1)) for m in
       ("boss.pricing.snapshot", "boss.tariff", "boss.tariff.line", "boss.expediente", "boss.expediente.cost")])
# a customer that is also a BOSS supplier (an agent): standard Odoo lets its portal users read the purchase orders where
# it is the vendor (rule portal_purchase_order_user_rule); boss_portal closes it (part 2)
po_a = env["purchase.order"].create({"partner_id": cust_a.id, "order_line": [Command.create({
    "product_id": product("THC").id, "product_qty": 1, "price_unit": 253.0, "name": "[PRUEBA] compra"})]})
po_seen = bool(env["purchase.order"].with_user(user_a).search_count([("id", "=", po_a.id)]))
check("1 purchase order where the customer is the vendor: visible only while boss_portal is not installed",
      not installed, po_seen)

if not installed:
    print("CHECK SKIP 2..9 boss_portal is not installed on boss20 yet: roles, scope, signing, booking, shipments, "
          "tracking token are checked after its installation")
else:
    # --- part 2: roles and scope per legal entity --------------------------------------------------------------------
    user_a.partner_id.write({"boss_portal_role": "commercial", "boss_portal_customer_id": cust_a.id})
    a_track = portal_user("a_seguimiento", cust_a, boss_portal_role="tracking", boss_portal_customer_id=cust_a.id)
    a_appr = portal_user("a_apoderado", cust_a, boss_portal_role="approver", boss_portal_customer_id=cust_a.id)
    a_none = portal_user("a_sin_rol", cust_a)
    a_wrong = portal_user("a_otra_entidad", cust_a, boss_portal_role="commercial", boss_portal_customer_id=cust_b.id)
    b_comm = portal_user("b_comercial", cust_b, boss_portal_role="commercial", boss_portal_customer_id=cust_b.id)
    so_a2 = quotation(cust_a, rate=True, containers=0)
    so_b = quotation(cust_b)
    so_a2.write({"state": "sent"})
    so_b.write({"state": "sent"})
    seen = lambda u: set(Order.with_user(u).search([("id", "in", (so_a | so_a2 | so_b).ids)]).ids)  # noqa: E731
    check("2 commercial A sees A's quotations only", {so_a.id, so_a2.id}, seen(user_a))
    check("2 approver A sees A's quotations only", {so_a.id, so_a2.id}, seen(a_appr))
    check("2 tracking A sees no quotation", set(), seen(a_track))
    check("2 a contact of A without role sees nothing (the standard portal rule alone no longer opens A's orders)", set(), seen(a_none))
    check("2 a contact of A granted customer B sees nothing (scope must be his own legal entity)", set(), seen(a_wrong))
    check("2 commercial B sees B only", {so_b.id}, seen(b_comm))
    check("2 opening A's quotation by id as B is refused", True, refused(lambda: so_a.with_user(b_comm).read(["name"])))
    check("2 lines follow their quotation: B cannot read A's lines", True,
          refused(lambda: so_a.order_line.with_user(b_comm).read(["price_unit"])))
    # invoices: customer invoices of A only, never vendor bills, drafts or B's
    sale_tax = env["account.tax"].search([("type_tax_use", "=", "sale"), ("amount", "=", 0), ("company_id", "=", env.company.id)], limit=1)
    inv_a = env["account.move"].create({"move_type": "out_invoice", "partner_id": cust_a.id, "invoice_date": date.today(),
                                        "invoice_line_ids": [Command.create({"name": "[PRUEBA] servicio", "quantity": 1, "price_unit": 100,
                                                                             "tax_ids": [Command.set(sale_tax.ids)]})]})
    inv_a.action_post()
    bill = env["account.move"].create({"move_type": "in_invoice", "partner_id": cust_a.id, "invoice_date": date.today(),
                                       "invoice_line_ids": [Command.create({"name": "[PRUEBA] coste", "quantity": 1, "price_unit": 60})]})
    bill.action_post()
    moves = lambda u: set(env["account.move"].with_user(u).search([("id", "in", (inv_a | bill).ids)]).ids)  # noqa: E731
    check("3 commercial A sees A's posted invoice, not a vendor bill of the same partner", {inv_a.id}, moves(user_a))
    check("3 tracking A and commercial B see no invoice of A", (set(), set()), (moves(a_track), moves(b_comm)))
    check("3 a purchase order where customer A is the vendor is not visible to A's portal users (standard rule closed)",
          (0, True), (env["purchase.order"].with_user(user_a).search_count([("id", "=", po_a.id)]),
                      refused(lambda: po_a.with_user(user_a).read(["amount_total"]))))
    # who may sign or pay
    so_a.write({"require_signature": True})
    viewer = lambda u: so_a.sudo().with_context(boss_portal_viewer_uid=u.id)  # noqa: E731
    public = ref("base.public_user")
    check("4 sign: approver yes; commercial, tracking, token link (public) no",
          (True, False, False, False),
          tuple(viewer(u)._has_to_be_signed() for u in (a_appr, user_a, a_track, public)))
    check("4 a rate quotation is never signed or paid", (False, False),
          (so_a2.sudo().with_context(boss_portal_viewer_uid=a_appr.id)._has_to_be_signed(),
           so_a2.sudo().with_context(boss_portal_viewer_uid=a_appr.id)._has_to_be_paid()))
    check("4 back-office (no viewer) keeps the standard behaviour", True, so_a.sudo()._has_to_be_signed())
    check("4 the rate quotation uses the rate portal page and the rate e-mail", ("boss_portal.sale_order_portal_content_rate", "boss_portal.email_template_rate_quotation"),
          (so_a2._get_name_portal_content_view(), so_a2._find_mail_template().get_external_id()[so_a2._find_mail_template().id]))
    # booking request
    so_a2.write({"order_line": [Command.create({"product_id": product("THC").id, "product_uom_id": product("THC").uom_id.id,
                                                "boss_container_size": "40", "boss_container_type_id": hc.id, "price_unit": 310.0})]})
    thc_dv = so_a2.order_line.filtered(lambda l: l.boss_container_type_id == dv and l.product_id.default_code == "THC")
    thc_hc = so_a2.order_line.filtered(lambda l: l.boss_container_type_id == hc)
    bl = so_a2.order_line.filtered(lambda l: l.product_id.default_code == "BL")
    check("5 commercial A cannot request a booking (authorised representative only)", True,
          refused(lambda: so_a2._boss_portal_request_booking(user_a, {thc_hc.id: 1})))
    check("5 a line of another quotation, a per-B/L line, 100 containers, nothing chosen: refused", [True] * 4,
          [refused(lambda q=q: so_a2._boss_portal_request_booking(a_appr, q)) for q in
           ({so_b.order_line[:1].id: 1}, {bl.id: 1}, {thc_hc.id: 100}, {thc_hc.id: 0})])
    activities = so_a2.activity_ids
    price_before = thc_hc.price_unit
    rows = so_a2._boss_portal_request_booking(a_appr, {thc_hc.id: 2, thc_dv.id: 0}, "[PRUEBA] cargo listo 15/11")
    check("5 the approver's request is recorded: 2 x 40' HC, pending BOSS review", ("requested", [(thc_hc.id, 2, "40", "HC")], a_appr),
          (so_a2.boss_booking_state, [(r["line_id"], r["quantity"], r["size"], r["type"]) for r in rows], so_a2.boss_booking_requested_by))
    check("5 nothing confirmed, no file, no invoice, prices unchanged", ("sent", False, 0, price_before),
          (so_a2.state, bool(so_a2.boss_expediente_id), len(so_a2.invoice_ids), thc_hc.price_unit))
    check("5 the salesperson gets an activity and an internal note", (True, True),
          (len(so_a2.activity_ids) > len(activities), any(m.subtype_id == ref("mail.mt_note") and "Booking request" in (m.body or "")
                                                          for m in so_a2.message_ids)))
    check("5 a second request while pending is refused", True,
          refused(lambda: so_a2._boss_portal_request_booking(a_appr, {thc_hc.id: 1})))
    so_a2.action_boss_booking_handled()
    so_a2.validity_date = date.today() - timedelta(days=1)
    check("5 expired rates cannot be booked", True, refused(lambda: so_a2._boss_portal_request_booking(a_appr, {thc_hc.id: 1})))
    # shipments: whitelist, events, documents, token
    so_a.write({"order_line": [Command.create({"product_id": product("FMI").id, "product_uom_id": product("FMI").uom_id.id,
                                               "boss_container_size": "40", "boss_container_type_id": dv.id, "price_unit": 2000,
                                               "boss_manual_cost": 1500, "boss_manual_cost_note": "[PRUEBA] nota interna coste"})]})
    so_a.action_confirm()
    file = so_a.boss_expediente_id
    file.write({"etd": date(2026, 11, 20), "eta": date(2026, 12, 5), "hbl_ref": "[PRUEBA] HBL-A1", "mbl_ref": "[PRUEBA] MBL-MASTER"})
    file.container_ids[:1].number = "PRUE1234567"
    ev_internal = env["boss.expediente.event"].create({"expediente_id": file.id, "name": "Llamada naviera", "note": "[PRUEBA] interno: margen bajo"})
    ev_public = env["boss.expediente.event"].create({"expediente_id": file.id, "name": "Salida", "kind": "milestone",
                                                     "note": "[PRUEBA] nota interna", "portal_published": True,
                                                     "portal_text": "Container loaded on board"})
    acc, pub = file._boss_portal_values("account"), file._boss_portal_values("public")
    text = repr(acc) + repr(pub)
    check("6 nothing internal in the shipment values (cost note, internal event, internal note, master B/L, amounts)",
          [False] * 6, [s in text for s in ("nota interna coste", "margen bajo", "[PRUEBA] interno", "[PRUEBA] nota interna", "MBL-MASTER", "1500")])
    check("6 only the published event, with its customer text", ["Container loaded on board"], [e["text"] for e in acc["events"]])
    check("6 estimated dates are not actual ones: ETD/ETA set, ATD/ATA/delivered unknown", (date(2026, 11, 20), date(2026, 12, 5), None, None, None),
          (acc["etd"], acc["eta"], acc["atd"], acc["ata"], acc["delivered"]))
    check("6 the tracking view has no parties, references, container numbers or documents", [],
          [k for k in ("customer_reference", "carrier", "house_reference", "container_numbers", "documents", "id") if k in pub])
    check("6 the account view shows the house B/L and the container number", ("[PRUEBA] HBL-A1", ["PRUE1234567"]),
          (acc["house_reference"], [c["number"] for c in acc["container_numbers"]]))
    own = env["ir.attachment"].create({"name": "[PRUEBA] aviso de llegada.pdf", "res_model": "boss.expediente", "res_id": file.id, "raw": b"%PDF-1.4 prueba"})
    foreign = env["ir.attachment"].create({"name": "[PRUEBA] otro.pdf", "res_model": "sale.order", "res_id": so_b.id, "raw": b"x"})
    check("7 a document of another record cannot be published on the file", True,
          refused(lambda: file.write({"portal_attachment_ids": [Command.link(foreign.id)]})))
    file.portal_attachment_ids = [Command.link(own.id)]
    check("7 the published document is listed; the attachment stays private", ([own.name], False),
          ([d["name"] for d in file._boss_portal_values("account")["documents"]], own.public))
    check("7 an event cannot be published without its customer text", True,
          refused(lambda: env["boss.expediente.event"].create({"expediente_id": file.id, "name": "x", "portal_published": True})))
    File = env["boss.expediente"]
    file.action_boss_share_tracking()
    token = file.portal_tracking_token
    check("8 the link finds its shipment; a wrong or short token does not", (file, File, File),
          (File._boss_find_by_tracking_token(token), File._boss_find_by_tracking_token(token[:-1] + "x"), File._boss_find_by_tracking_token("abc")))
    file.action_boss_share_tracking()
    check("8 a new link stops the earlier one", (File, file), (File._boss_find_by_tracking_token(token), File._boss_find_by_tracking_token(file.portal_tracking_token)))
    file.action_boss_revoke_tracking()
    check("8 a revoked link stops working", File, File._boss_find_by_tracking_token(token))
    check("8 the shipment scope: tracking A has A's file, B has none", (True, False),
          (a_track._boss_portal_can("track", file.partner_id), b_comm._boss_portal_can("track", file.partner_id)))
    # revocation and who grants roles
    user_a.partner_id.write({"boss_portal_role": False})
    check("9 role removed: commercial A sees no quotation and no invoice at once", (set(), set()), (seen(user_a), moves(user_a)))
    a_appr.active = False
    check("9 portal access revoked (user archived): no scope", (False, False), a_appr._boss_portal_scope()[0:1] + (False,))
    salesman = Users.create({"name": "[PRUEBA] comercial interno", "login": "prueba_comercial_interno",
                             "group_ids": [Command.set([ref("base.group_user").id, ref("sales_team.group_sale_salesman").id])]})
    check("9 only a sales manager grants portal roles (a salesperson cannot)", True,
          refused(lambda: a_track.partner_id.with_user(salesman).write({"boss_portal_role": "approver"})))
print(f"RESULT {sum(results)} passed, {len(results) - sum(results)} failed")
env.cr.rollback()  # noqa: F821
if len(results) - sum(results):  # a failed check fails the run (dev/uat_run.sh records the exit status)
    raise SystemExit(1)
