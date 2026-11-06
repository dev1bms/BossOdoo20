from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

BILL_TYPES = ("in_invoice", "in_refund", "in_receipt")
# How a status condition of a file is checked (settings study of 04/11/2026, phase 3): it stops the step, it only warns
# (and the warning stays in the history), or it is not checked at all.
CONDITION_LEVELS = [("block", "Required (stops the step)"), ("warn", "Warning only"), ("off", "Not checked")]
# (field, step, label, default): the conditions of the steps of a file. Defaults are today's behaviour: Odoo 17
# practice warns when the file leaves; what Cristina wrote stops «Delivered» and the operational close.
FILE_CONDITIONS = [
    ("boss_cond_transit_atd", "in_transit", "Actual departure (ATD)", "warn"),
    ("boss_cond_transit_booking", "in_transit", "Booking (sea and air)", "warn"),
    ("boss_cond_transit_master", "in_transit", "Master B/L or AWB (sea and air)", "warn"),
    ("boss_cond_transit_containers", "in_transit", "Container numbers (FCL)", "warn"),
    ("boss_cond_delivered_ata", "delivered", "Actual arrival (ATA) of an import", "block"),
    ("boss_cond_delivered_discharge", "delivered", "Vessel discharge of a sea import", "block"),
    ("boss_cond_delivered_release", "delivered", "Customs release when BOSS clears", "block"),
    ("boss_cond_delivered_pickup", "delivered", "Pickup date and time when BOSS picks up", "block"),
    ("boss_cond_delivered_delivery", "delivered", "Delivery date and time when BOSS delivers", "block"),
    ("boss_cond_delivered_hbl", "delivered", "House B/L released or sea waybill (sea import delivered by BOSS)", "block"),
    ("boss_cond_close_invoiced", "close", "Every service invoiced", "block"),
    ("boss_cond_close_margin", "close", "Low margin explained by a sales manager", "block"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    # Cristina's requirement («Nuevo Odoo», Facturación A3, Facturación y costes A11): a supplier bill is not posted
    # or paid before its service is invoiced to the customer. Approved 23/10/2026 (Belal, P30): the bill is posted on
    # time (it must be recorded when received) and its PAYMENT waits for the customer invoice.
    boss_bill_before_invoice = fields.Selection(
        [("warn", "Warn only"), ("block_payment", "Block payment (posting allowed)"),
         ("block", "Block posting and payment")],
        "Supplier bill before the customer invoice", default="block_payment", required=True)
    # F0-C66: Odoo 17 required the ratings of the customer and the suppliers to close a file since 01/03/2025.
    boss_ratings_to_close = fields.Boolean(
        "Ratings required to close operations", default=True,
        help="The customer and every supplier of a file are rated (0-10) before its operations close, as in Odoo 17.")
    # Status conditions of a file (phase 3 of the settings study): one level each, today's behaviour by default. Each
    # change is kept in the company's history (who, when, old and new level).
    boss_cond_transit_atd = fields.Selection(CONDITION_LEVELS, "Leaving: actual departure (ATD)", default="warn",
                                             required=True, tracking=True)
    boss_cond_transit_booking = fields.Selection(CONDITION_LEVELS, "Leaving: booking", default="warn",
                                                 required=True, tracking=True)
    boss_cond_transit_master = fields.Selection(CONDITION_LEVELS, "Leaving: master B/L or AWB", default="warn",
                                                required=True, tracking=True)
    boss_cond_transit_containers = fields.Selection(CONDITION_LEVELS, "Leaving: container numbers", default="warn",
                                                    required=True, tracking=True)
    boss_cond_delivered_ata = fields.Selection(CONDITION_LEVELS, "Delivered: ATA of an import", default="block",
                                               required=True, tracking=True)
    boss_cond_delivered_discharge = fields.Selection(CONDITION_LEVELS, "Delivered: vessel discharge", default="block",
                                                     required=True, tracking=True)
    boss_cond_delivered_release = fields.Selection(CONDITION_LEVELS, "Delivered: customs release", default="block",
                                                   required=True, tracking=True)
    boss_cond_delivered_pickup = fields.Selection(CONDITION_LEVELS, "Delivered: pickup date and time", default="block",
                                                  required=True, tracking=True)
    boss_cond_delivered_delivery = fields.Selection(CONDITION_LEVELS, "Delivered: delivery date and time",
                                                    default="block", required=True, tracking=True)
    boss_cond_delivered_hbl = fields.Selection(CONDITION_LEVELS, "Delivered: house B/L released", default="block",
                                               required=True, tracking=True)
    boss_cond_close_invoiced = fields.Selection(CONDITION_LEVELS, "Close: every service invoiced", default="block",
                                                required=True, tracking=True)
    boss_cond_close_margin = fields.Selection(CONDITION_LEVELS, "Close: low margin explained", default="block",
                                              required=True, tracking=True)
    # Settings study of 04/11/2026 (docs/estudio-ajustes.md): values that change over time leave the code.
    boss_close_days_after_delivery = fields.Integer(
        "Days after the delivery to close operations", default=7,
        help="Cristina: a delivered file closes operations within this many days; afterwards the next step warns.")
    boss_default_allocation_basis = fields.Selection(
        [("chargeable", "Chargeable weight (W/M)"), ("gross", "Gross weight"), ("volume", "Volume"),
         ("equal", "Equal parts"), ("manual", "Manual share")], "Shared costs of a consolidation split by",
        default="chargeable", required=True, help="Proposed on every new master file (ADR-013).")
    boss_invoice_operation_date = fields.Boolean(
        "Operation date on the customer invoice", default=True,
        help="The invoice keeps its issue date and prints the operation date of the file apart (arrival of an "
             "import, departure otherwise; RD 1619/2012 art. 6). Off: the field stays empty unless typed.")
    boss_paid_on_behalf_note = fields.Text(
        "Mention on the invoice of amounts paid on behalf", translate=True,
        help="Printed on the invoice that re-invoices duties, import VAT and other amounts paid in the customer's "
             "name (art. 78.Tres.3º Ley 37/1992). Empty: the standard wording.")

    @api.constrains("boss_close_days_after_delivery", "boss_free_alert_days")
    def _check_boss_file_values(self):
        """Settings values that make sense (a zero or negative number would be replaced or printed as such)."""
        for company in self:
            for field, minimum in (("boss_close_days_after_delivery", 0), ("boss_free_alert_days", 0)):
                if company[field] < minimum:
                    raise ValidationError(self.env._("%(setting)s: enter a value of at least %(minimum)s.",
                                                     setting=self._fields[field].get_description(self.env)["string"],
                                                     minimum=minimum))


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    boss_bill_before_invoice = fields.Selection(related="company_id.boss_bill_before_invoice", readonly=False)
    boss_ratings_to_close = fields.Boolean(related="company_id.boss_ratings_to_close", readonly=False)
    boss_close_days_after_delivery = fields.Integer(related="company_id.boss_close_days_after_delivery", readonly=False)
    boss_cond_transit_atd = fields.Selection(related="company_id.boss_cond_transit_atd", readonly=False)
    boss_cond_transit_booking = fields.Selection(related="company_id.boss_cond_transit_booking", readonly=False)
    boss_cond_transit_master = fields.Selection(related="company_id.boss_cond_transit_master", readonly=False)
    boss_cond_transit_containers = fields.Selection(related="company_id.boss_cond_transit_containers", readonly=False)
    boss_cond_delivered_ata = fields.Selection(related="company_id.boss_cond_delivered_ata", readonly=False)
    boss_cond_delivered_discharge = fields.Selection(related="company_id.boss_cond_delivered_discharge", readonly=False)
    boss_cond_delivered_release = fields.Selection(related="company_id.boss_cond_delivered_release", readonly=False)
    boss_cond_delivered_pickup = fields.Selection(related="company_id.boss_cond_delivered_pickup", readonly=False)
    boss_cond_delivered_delivery = fields.Selection(related="company_id.boss_cond_delivered_delivery", readonly=False)
    boss_cond_delivered_hbl = fields.Selection(related="company_id.boss_cond_delivered_hbl", readonly=False)
    boss_cond_close_invoiced = fields.Selection(related="company_id.boss_cond_close_invoiced", readonly=False)
    boss_cond_close_margin = fields.Selection(related="company_id.boss_cond_close_margin", readonly=False)
    boss_default_allocation_basis = fields.Selection(related="company_id.boss_default_allocation_basis", readonly=False)
    boss_invoice_operation_date = fields.Boolean(related="company_id.boss_invoice_operation_date", readonly=False)
    boss_paid_on_behalf_note = fields.Text(related="company_id.boss_paid_on_behalf_note", readonly=False)


class AccountMove(models.Model):
    _inherit = "account.move"

    # F0-A20 as reviewed (RD 1619/2012 art. 6): the invoice keeps its issue date; the date of the operation goes apart.
    # Odoo's own «Delivery Date» of the invoice (printed, no accounting effect) is that date, from the file.
    delivery_date = fields.Date(string="Operation date")

    @api.depends("invoice_line_ids.boss_expediente_id")
    def _compute_delivery_date(self):
        super()._compute_delivery_date()
        for move in self.filtered(lambda m: m.is_sale_document(include_receipts=True) and not m.delivery_date
                                  and m.company_id.boss_invoice_operation_date):
            dates = [d for d in (f._boss_operation_date() for f in move.invoice_line_ids.boss_expediente_id) if d]
            move.delivery_date = max(dates) if dates else False

    boss_bill_warning = fields.Text("Supplier bill checks", compute="_compute_boss_bill_warning")
    boss_paid_before_invoice = fields.Boolean(
        "Paid before the customer invoice", readonly=True, copy=False,
        help="P30: this supplier bill was matched with a bank movement (a payment already made) before its services "
        "were invoiced to the customer. The movement is recorded, because the books must match the bank; the file "
        "shows it in «To do» until the services are invoiced.")

    def _boss_files(self):
        """Files of this move: on its lines, or through the analytic account of its lines."""
        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == "product")
        files = lines.boss_expediente_id
        accounts = lines.distribution_analytic_account_ids
        if accounts:
            files |= self.env["boss.expediente"].sudo().search([("analytic_account_id", "in", accounts.ids)])
        return files

    def _boss_flag_paid_before_invoice(self):
        """Called after a reconciliation: a bill of the file now (partly) paid while P30 still holds it."""
        for bill in self.filtered(lambda m: m.move_type == "in_invoice" and m.state == "posted"
                                  and not m.boss_paid_before_invoice
                                  and m.company_id.boss_bill_before_invoice in ("block", "block_payment")
                                  and m.payment_state in ("paid", "in_payment", "partial")):
            problems = bill._boss_bill_order_problems()
            if not problems:
                continue
            bill.sudo().boss_paid_before_invoice = True
            note = self.env._("Paid by a bank movement before its services were invoiced to the customer (P30). "
                              "The movement is recorded because it happened; invoice these services:")
            body = Markup("<p>%s</p><ul>%s</ul>") % (note, Markup("").join(Markup("<li>%s</li>") % p for p in problems))
            bill.sudo().message_post(body=body, message_type="comment", subtype_xmlid="mail.mt_note")
            for file in bill._boss_files():
                file.sudo().message_post(body=Markup("<p>%s: %s</p>") % (bill.display_name, note),
                                         message_type="comment", subtype_xmlid="mail.mt_note")

    def _boss_bill_needs(self):
        """File services billed by this vendor bill: through its purchase lines, or (amounts paid on behalf, billed
        without purchase order) through the service and the file's analytic account."""
        self.ensure_one()
        # Odoo 20 puts every purchase line on the bill, with quantity 0 for what is not performed yet: those lines
        # bill nothing and must not hold the payment (defect D-1, 26/10/2026).
        lines = self.invoice_line_ids.filtered(
            lambda l: l.display_type == "product" and l.product_id and l.quantity)
        needs = lines.purchase_line_id.boss_cost_id
        Need = self.env["boss.expediente.cost"].sudo()
        for line in lines.filtered(lambda l: not l.purchase_line_id and l.product_id.boss_paid_on_behalf):
            accounts = line.distribution_analytic_account_ids
            needs |= Need.search([("without_order", "=", True), ("product_id", "=", line.product_id.id),
                                  ("expediente_id.analytic_account_id", "in", accounts.ids)])
        return needs

    @api.depends("invoice_line_ids.purchase_line_id", "invoice_line_ids.product_id", "move_type", "state")
    def _compute_boss_bill_warning(self):
        for move in self:
            problems = move._boss_bill_order_problems() if move.move_type == "in_invoice" else []
            move.boss_bill_warning = "\n".join(problems) or False

    def _boss_bill_order_problems(self):
        """Order of work: the customer is invoiced before its supplier bill is posted or paid."""
        _ = self.env._
        problems = []
        for need in self._boss_bill_needs():
            if need.extra_class in ("covered", "absorb"):
                continue  # no customer invoice is expected for it
            if need.extra_class in ("approval", "disputed"):
                label = dict(need._fields["extra_class"]._description_selection(self.env))[need.extra_class]
                problems.append(_("%(service)s: extra cost still '%(cls)s'", service=need.display_name, cls=label))
                continue
            sale_line = need.sale_line_id or need.rebill_line_id
            if not sale_line:
                problems.append(_("%s: no sale line (decide whether it is re-invoiced or borne by BOSS)",
                                  need.display_name))
            elif need.paid_in_advance:
                continue  # freight paid in advance to an agent: the sale line is enough
            elif not sale_line.invoice_lines.filtered(
                    lambda l: l.parent_state == "posted" and l.move_id.move_type == "out_invoice"):
                # invoiced once is enough: a later credit note is a sales decision, the supplier is still owed (D-5)
                problems.append(_("%s: not invoiced to the customer yet", need.display_name))
        return problems

    def _post(self, soft=True):
        self._boss_check_post()
        posted = super()._post(soft)
        posted._boss_refresh_file_needs()
        return posted

    def _boss_check_post(self):
        """Never posted with an undecided VAT treatment (Ángel's rules: a missing zone leaves the VAT pending, never
        guessed) or, for a customer in Spain (or without country), without its identification (Odoo 17 practice;
        identification as the Spanish localization reads it). Supplier bills need the tax of the supplier document and
        follow the company setting on the customer invoice order."""
        _ = self.env._
        for move in self:
            lines = move.invoice_line_ids.filtered(
                lambda l: l.display_type == "product" and l.product_id.boss_pricing_mode)
            problems = []
            for file in move._boss_files().filtered("financial_closed"):
                problems.append(_("file %s is financially closed: an accounting manager reopens it first",
                                  file.display_name))
            if move.move_type in ("out_invoice", "out_refund"):
                for line in lines:
                    if line.sale_line_ids.filtered(lambda s: s.boss_vat_status == "pending"):
                        problems.append(_("%s: VAT treatment pending (BOSS VAT table)", line.product_id.display_name))
                    elif not line.tax_ids:
                        problems.append(_("%s: no tax", line.product_id.display_name))
                if lines and not move.partner_id._boss_has_invoice_identification():
                    problems.append(_("customer %s in Spain without tax ID (NIF) or other identification",
                                      move.partner_id.commercial_partner_id.display_name))
            elif move.move_type in ("in_invoice", "in_refund"):
                for line in lines.filtered(lambda l: not l.tax_ids):
                    problems.append(_("%s: choose the tax shown on the supplier invoice (0 %% included)",
                                      line.product_id.display_name))
                if move.move_type == "in_invoice" and move.company_id.boss_bill_before_invoice == "block":
                    problems += move._boss_bill_order_problems()
                if move.duplicated_ref_ids and not (self.env.su or self.env.user.has_group("account.group_account_manager")):
                    # a bill with a supplier reference already registered is posted only by an accounting manager
                    # (P2-12 default rule, 05/11/2026); Odoo alone only warns
                    problems.append(_("supplier reference «%(ref)s» already registered on %(moves)s: an accounting "
                                      "manager confirms it is not a duplicate", ref=move.ref,
                                      moves=", ".join(move.duplicated_ref_ids.mapped("name"))))
            if problems:
                raise UserError(_("%(move)s cannot be posted:\n%(problems)s",
                                  move=move.display_name, problems="\n".join(f"- {p}" for p in problems)))

    def _boss_check_payment_allowed(self):
        """P30: a supplier bill of a file service is not paid before that service is invoiced to the customer."""
        for move in self.filtered(lambda m: m.move_type == "in_invoice"
                                  and m.company_id.boss_bill_before_invoice in ("block", "block_payment")):
            problems = move._boss_bill_order_problems()
            if problems:
                raise UserError(self.env._("%(move)s cannot be paid yet:\n%(problems)s", move=move.display_name,
                                           problems="\n".join(f"- {p}" for p in problems)))

    def action_register_payment(self):
        self._boss_check_payment_allowed()
        return super().action_register_payment()

    def _boss_late_bill_needs(self):
        """A posted vendor bill line that reaches a file through its analytic account, without purchase line and
        without a service line to receive it (a late detention bill on a closed file, for instance), gets its own
        service line of the file: extra cost «to approve», billed without order. The financial close then waits
        for the decision re-invoice or absorb (P2-12 default rule, 05/11/2026)."""
        Need = self.env["boss.expediente.cost"].sudo()
        File = self.env["boss.expediente"].sudo()
        created = Need
        for move in self.filtered(lambda m: m.move_type == "in_invoice" and m.state == "posted"):
            for line in move.invoice_line_ids.filtered(
                    lambda l: l.display_type == "product" and l.product_id and l.quantity and not l.purchase_line_id
                    and l.product_id.boss_pricing_mode and not l.product_id.boss_paid_on_behalf):
                accounts = line.distribution_analytic_account_ids
                if not accounts:
                    continue
                for file in File.search([("analytic_account_id", "in", accounts.ids)]):
                    if Need.search_count([("expediente_id", "=", file.id), ("product_id", "=", line.product_id.id),
                                          ("without_order", "=", True)]):
                        continue
                    need = Need.create({
                        "expediente_id": file.id, "kind": "extra", "product_id": line.product_id.id,
                        "name": line.name or line.product_id.display_name, "partner_id": move.partner_id.id,
                        "currency_id": move.currency_id.id, "uom_id": line.product_uom_id.id or line.product_id.uom_id.id,
                        "quantity": line.quantity, "expected_unit_cost": line.price_unit, "without_order": True,
                        "extra_class": "approval"})
                    created |= need
                    file.message_post(body=self.env._(
                        "%(bill)s: late cost %(service)s received without a service line. Added as an extra cost to "
                        "approve: decide whether it is re-invoiced or borne by BOSS before the financial close.",
                        bill=move.display_name, service=line.product_id.display_name))
        return created

    def _boss_refresh_file_needs(self):
        """Services billed without purchase order follow their bills (state and billed amount)."""
        needs = self._boss_late_bill_needs()
        for move in self.filtered(lambda m: m.move_type in BILL_TYPES):
            needs |= move._boss_bill_needs().filtered("without_order")
        if needs:
            self.env.add_to_compute(needs._fields["state"], needs)
            needs._recompute_recordset(["state"])

    def button_draft(self):
        res = super().button_draft()
        self._boss_refresh_file_needs()
        return res

    def button_cancel(self):
        res = super().button_cancel()
        self._boss_refresh_file_needs()
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    boss_expediente_id = fields.Many2one("boss.expediente", "File", index="btree_not_null", copy=True,
                                         help="File this invoice line belongs to (one sale line may be in several "
                                         "files).")

    def reconcile(self):
        bills = self.move_id.filtered(lambda m: m.move_type == "in_invoice")
        res = super().reconcile()
        bills._boss_flag_paid_before_invoice()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """A bill entered from a file («Cost without purchase order») carries the file on its product lines."""
        file_id = self.env.context.get("boss_default_file")
        if file_id:
            for vals in vals_list:
                if vals.get("display_type", "product") == "product" and not vals.get("boss_expediente_id"):
                    vals["boss_expediente_id"] = file_id
        return super().create(vals_list)

    def _related_analytic_distribution(self):
        """A bill entered from a file (cost without purchase order) is charged to the file's analytic account."""
        values = super()._related_analytic_distribution()
        default = self.env.context.get("boss_default_analytic")
        if default and not values and self.display_type == "product":
            values = dict(default)
        return values


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        """The payment block holds every path that registers a payment on the bill (its button, the bills list, the
        wizard opened on its lines), not only the button of the bill."""
        self.line_ids.move_id._boss_check_payment_allowed()
        return super()._create_payments()
