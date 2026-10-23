from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

from odoo.addons.boss_pricing.models.boss_pricing import COST_STATUSES
from odoo.addons.boss_pricing_sale.models.sale_order_line import COST_KINDS

from .boss_expediente import COST_GROUPS, account_share

NEED_STATES = [
    ("no_supplier", "Supplier missing"),
    ("awaiting_bill", "Bill without order expected"),
    ("to_order", "To order"),
    ("rfq", "RFQ"),
    ("ordered", "Ordered"),
    ("performed", "Performed"),
    ("billed", "Billed"),
    ("closed", "Closed"),
]
EXTRA_CLASSES = [
    ("covered", "Covered by the agreed price"),
    ("rebill", "Re-invoice to the customer"),
    ("approval", "Needs customer approval"),
    ("absorb", "BOSS bears it"),
    ("disputed", "Disputed with the supplier"),
]


class BossExpedienteCost(models.Model):
    """One external cost of a file: a service sold and bought from a supplier, or an extra cost found later. The
    purchase basis (unit, quantity, currency) is its own: never copied blindly from the sale, never converted."""

    _name = "boss.expediente.cost"
    _description = "Service to buy or extra cost of a shipment file"
    _order = "expediente_id, kind desc, id"

    expediente_id = fields.Many2one("boss.expediente", "File", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="expediente_id.company_id", store=True)
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    kind = fields.Selection([("sale", "Sold service"), ("extra", "Extra cost")], required=True, default="extra",
                            readonly=True)
    sale_line_id = fields.Many2one("sale.order.line", "Sale line", readonly=True, index="btree_not_null")
    product_id = fields.Many2one("product.product", "Service", required=True,
                                 domain="[('purchase_ok', '=', True), ('type', '=', 'service')]")
    name = fields.Char("Description")
    partner_id = fields.Many2one("res.partner", "Supplier", help="Can be changed while nothing is ordered "
                                 "(cancel the purchase order first to replace the supplier).")
    currency_id = fields.Many2one("res.currency", required=True,
                                  default=lambda self: self.env.company.currency_id)
    uom_id = fields.Many2one("uom.uom", "Purchase unit", required=True)
    quantity = fields.Float("Purchase quantity", digits="Product Unit", default=1.0, required=True)
    expected_unit_cost = fields.Monetary("Expected unit cost", currency_field="currency_id")
    expected_amount = fields.Monetary("Expected cost", currency_field="currency_id",
                                      compute="_compute_expected_amount", store=True)
    accepted_unit_cost = fields.Monetary("Unit cost at acceptance", currency_field="currency_id", readonly=True)
    accepted_amount_company = fields.Monetary("Cost at acceptance (company currency)",
                                              currency_field="company_currency_id", readonly=True)
    accepted_cost_kind = fields.Selection(COST_KINDS, "Cost kind at acceptance", readonly=True)
    tariff_line_id = fields.Many2one("boss.tariff.line", "Supplier price", readonly=True)
    extra_class = fields.Selection(EXTRA_CLASSES, "Extra cost is",
                                   help="Who bears an extra cost found after acceptance.")
    reason = fields.Text("Reason")
    rebill_line_id = fields.Many2one("sale.order.line", "Re-invoiced in", readonly=True, copy=False)
    without_order = fields.Boolean(
        "Billed without purchase order", compute="_compute_without_order", store=True, readonly=False,
        help="Documented exception to the purchase order: amounts paid on behalf of the customer (duties, import VAT "
        "of the customs declaration) are known from the declaration and billed by the customs broker at cost. Their "
        "bill is entered with 'Cost without purchase order' on the file and matched here by service.")
    paid_in_advance = fields.Boolean(
        "Paid in advance", help="Freight paid in advance to an agent: its bill may be posted once the sale line exists, "
        "before the customer is invoiced (Cristina, «Nuevo Odoo», Facturación A3).")
    closed = fields.Boolean("No more cost expected", help="Nothing more will be ordered or billed (service cancelled, "
                            "supplier replaced, cost not incurred).")
    purchase_line_ids = fields.One2many("purchase.order.line", "boss_cost_id", "Purchase lines", readonly=True)
    state = fields.Selection(NEED_STATES, compute="_compute_state", store=True)
    qty_ordered = fields.Float("Ordered", compute="_compute_quantities", compute_sudo=True, digits="Product Unit")
    qty_received = fields.Float("Performed", compute="_compute_quantities", compute_sudo=True, digits="Product Unit")
    qty_billed = fields.Float("Billed", compute="_compute_quantities", compute_sudo=True, digits="Product Unit")
    ordered_amount_company = fields.Monetary("Ordered amount", currency_field="company_currency_id",
                                             compute="_compute_amounts", compute_sudo=True, groups=COST_GROUPS)
    billed_amount_company = fields.Monetary("Billed amount", currency_field="company_currency_id",
                                            compute="_compute_amounts", compute_sudo=True, groups=COST_GROUPS, help="Posted bills minus credit notes.")
    pending_amount_company = fields.Monetary("Still expected", currency_field="company_currency_id",
                                             compute="_compute_amounts", compute_sudo=True, groups=COST_GROUPS)
    variance_company = fields.Monetary("Variance", currency_field="company_currency_id", compute="_compute_amounts", compute_sudo=True, groups=COST_GROUPS,
                                       help="Billed minus ordered (or expected when nothing was ordered).")
    cost_unknown = fields.Boolean("Cost unknown", compute="_compute_amounts", compute_sudo=True)
    variance_to_review = fields.Boolean(compute="_compute_amounts", compute_sudo=True)
    po_to_review = fields.Boolean("Order to review", compute="_compute_amounts", compute_sudo=True,
                                  help="The expected cost was recomputed after the purchase order was confirmed and "
                                  "differs from it: agree the change with the supplier or close the difference.")
    cost_method = fields.Selection(related="product_id.boss_cost_method")
    days = fields.Integer(
        "Days", help="Time-based services (storage, demurrage, port occupancy): days of the period. At acceptance, the "
        "days quoted; type the actual days and recompute the expected cost.")
    expected_date = fields.Datetime("Expected cost set on", readonly=True, copy=False)
    revision_ids = fields.One2many("boss.expediente.cost.revision", "cost_id", "Recalculations", readonly=True)
    variance_reviewed = fields.Boolean("Variance reviewed", copy=False)
    variance_note = fields.Char("Variance note")

    @api.depends("product_id")
    def _compute_without_order(self):
        for need in self:
            need.without_order = need.product_id.boss_paid_on_behalf

    @api.depends("quantity", "expected_unit_cost")
    def _compute_expected_amount(self):
        for need in self:
            need.expected_amount = need.quantity * need.expected_unit_cost

    @api.model
    def _values_from_sale_line(self, line, expediente, quantity=None):
        """Purchase need of an accepted line (or of the part of it in this file), in the basis and currency of its
        supplier price."""
        order = line.order_id
        quantity = line.product_uom_qty if quantity is None else quantity
        tariff_line = line.boss_tariff_line_id if line.boss_cost_status == "ok" else self.env["boss.tariff.line"]
        if tariff_line:
            currency = line.boss_cost_currency_id
            unit = line.boss_cost_amount / line.product_uom_qty if line.product_uom_qty else 0.0
            uom = tariff_line.uom_id or line.product_uom_id
        else:
            currency = line.currency_id
            unit = line.boss_manual_cost if line.boss_cost_status in ("manual", "not_ready") else 0.0
            uom = line.product_uom_id
        company = expediente.company_id
        accepted = currency._convert(unit * quantity, company.currency_id, company,
                                     fields.Date.to_date(order.date_order) or fields.Date.today())
        return {
            "expediente_id": expediente.id, "kind": "sale", "sale_line_id": line.id, "product_id": line.product_id.id,
            "name": line.product_id.display_name,
            # amounts paid on behalf (duties, import VAT) are paid by the customs broker and billed by it at cost
            "partner_id": (line._boss_purchase_partner() or (
                expediente.customs_broker_id if line.product_id.boss_paid_on_behalf else self.env["res.partner"])).id,
            "currency_id": currency.id, "uom_id": uom.id, "quantity": quantity,
            "expected_unit_cost": unit, "accepted_unit_cost": unit, "accepted_amount_company": accepted,
            "accepted_cost_kind": line.boss_cost_kind, "tariff_line_id": tariff_line.id,
            "days": line.boss_days if line.product_id.boss_cost_method == "time" else 0,
            "expected_date": fields.Datetime.now(),
        }

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id and not self.uom_id:
            self.uom_id = self.product_id.uom_id
        if self.product_id and not self.name:
            self.name = self.product_id.display_name

    def _boss_active_lines(self):
        return self.purchase_line_ids.filtered(lambda l: l.state != "cancel")

    def _boss_direct_bill_items(self):
        """Posted bill lines of a service billed without purchase order: same service, file's analytic account."""
        self.ensure_one()
        account = self.expediente_id.analytic_account_id
        if not self.without_order or not account or not self.product_id:
            return self.env["account.move.line"]
        return self.env["account.move.line"].sudo().search([
            ("product_id", "=", self.product_id.id), ("purchase_line_id", "=", False),
            ("display_type", "=", "product"), ("parent_state", "=", "posted"),
            ("move_id.move_type", "in", ("in_invoice", "in_refund", "in_receipt")),
            ("distribution_analytic_account_ids", "in", account.ids)])

    def _boss_remaining_qty(self):
        self.ensure_one()
        return self.quantity - sum(self._boss_active_lines().mapped("product_qty"))

    @api.depends("closed", "partner_id", "quantity", "purchase_line_ids.state", "purchase_line_ids.product_qty",
                 "purchase_line_ids.qty_received", "purchase_line_ids.qty_invoiced")
    def _compute_state(self):
        digits = self.env["decimal.precision"].precision_get("Product Unit")
        for need in self:
            lines = need._boss_active_lines()
            confirmed = lines.filtered(lambda l: l.state == "purchase")
            ordered = sum(confirmed.mapped("product_qty"))
            billed = sum(lines.mapped("qty_invoiced"))
            direct = need._boss_direct_bill_items()
            billed += sum(-l.quantity if l.move_id.move_type == "in_refund" else l.quantity for l in direct)
            if need.closed:
                state = "closed"
            elif billed > 0 and float_compare(billed, need.quantity, precision_digits=digits) >= 0:
                state = "billed"
            elif confirmed and float_compare(sum(confirmed.mapped("qty_received")), ordered,
                                             precision_digits=digits) >= 0:
                state = "performed"
            elif confirmed:
                state = "ordered"
            elif lines:
                state = "rfq"
            elif need.without_order:
                state = "awaiting_bill"
            elif not need.partner_id:
                state = "no_supplier"
            else:
                state = "to_order"
            need.state = state

    def _compute_quantities(self):
        for need in self:
            confirmed = need._boss_active_lines().filtered(lambda l: l.state == "purchase")
            need.qty_ordered = sum(confirmed.mapped("product_qty"))
            need.qty_received = sum(confirmed.mapped("qty_received"))
            need.qty_billed = sum(need._boss_active_lines().mapped("qty_invoiced"))

    @api.model
    def _boss_billed_by_purchase_line(self, purchase_lines):
        """Posted bill amounts (minus vendor credit notes) per purchase line, company currency."""
        if not purchase_lines:
            return {}
        groups = self.env["account.move.line"].sudo()._read_group(
            [("purchase_line_id", "in", purchase_lines.ids), ("parent_state", "=", "posted"),
             ("display_type", "=", "product")], ["purchase_line_id"], ["balance:sum"])
        return {line.id: balance for line, balance in groups}

    def _compute_amounts(self):
        billed_by_line = self._boss_billed_by_purchase_line(self.purchase_line_ids)
        today = fields.Date.today()
        for need in self:
            company = need.company_id or self.env.company
            currency = company.currency_id
            confirmed = need._boss_active_lines().filtered(lambda l: l.state == "purchase")
            ordered = sum(l.currency_id._convert(l.price_subtotal, currency, company,
                                                 fields.Date.to_date(l.order_id.date_order) or today)
                          for l in confirmed)
            billed = sum(billed_by_line.get(line.id, 0.0) for line in need.purchase_line_ids)
            billed += sum(item.balance * account_share(item, need.expediente_id.analytic_account_id)
                          for item in need._boss_direct_bill_items())
            unit = need.currency_id._convert(need.expected_unit_cost, currency, company, today, round=False)
            expected = unit * need.quantity
            ordered_qty = sum(confirmed.mapped("product_qty"))
            approved = [d for d in confirmed.order_id.mapped("date_approve") if d]
            # The latest information wins: an order confirmed after the expected cost was set is the commitment
            # (plus what is not ordered yet); an expected cost recomputed after the order (actual days, weight,
            # containers) is the forecast, never below what was ordered, and the order is flagged for review.
            if confirmed and (not need.expected_date or (approved and max(approved) > need.expected_date)):
                reference = ordered + unit * max(need.quantity - ordered_qty, 0.0)
                po_to_review = False
            else:
                reference = max(expected, ordered)
                po_to_review = bool(confirmed) and not currency.is_zero(expected - ordered)
            unknown = (not need.closed and not confirmed and not billed
                       and need.currency_id.is_zero(need.expected_unit_cost) and need.accepted_cost_kind != "zero")
            variance = billed - reference if need.state in ("billed", "closed") and billed else 0.0
            need.update({
                "po_to_review": po_to_review and need.state not in ("billed", "closed"),
                "ordered_amount_company": ordered, "billed_amount_company": billed,
                "pending_amount_company": 0.0 if need.closed or need.state == "billed" else max(reference - billed, 0.0),
                "variance_company": variance, "cost_unknown": unknown,
                "variance_to_review": not currency.is_zero(variance) and not need.variance_reviewed,
            })

    def write(self, vals):
        if "partner_id" in vals or "currency_id" in vals or "uom_id" in vals:
            for need in self.filtered(lambda n: n._boss_active_lines()):
                if vals.get("partner_id", need.partner_id.id) != need.partner_id.id or vals.get(
                        "currency_id", need.currency_id.id) != need.currency_id.id or vals.get(
                        "uom_id", need.uom_id.id) != need.uom_id.id:
                    raise UserError(self.env._(
                        "%s is already in a purchase order: cancel that order before changing supplier, currency or "
                        "unit.", need.display_name))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_sold_or_ordered(self):
        for need in self:
            if need.kind == "sale" or need.purchase_line_ids:
                raise UserError(self.env._("%s comes from the accepted sale or is ordered: close it instead of "
                                           "deleting it.", need.display_name))

    @api.depends("product_id", "name", "expediente_id")
    def _compute_display_name(self):
        for need in self:
            need.display_name = f"{need.expediente_id.name or ''} · {need.name or need.product_id.display_name}"

    def _boss_purchase_line_values(self, quantity):
        self.ensure_one()
        file = self.expediente_id
        planned = (file.eta if file.direction == "import" else file.etd) or fields.Date.context_today(self)
        return {
            "product_id": self.product_id.id, "name": f"{file.name} · {self.name or self.product_id.display_name}",
            "product_qty": quantity, "uom_id": self.uom_id.id, "price_unit": self.expected_unit_cost,
            "boss_cost_id": self.id, "sale_line_id": (self.sale_line_id or self.rebill_line_id).id,
            "analytic_distribution": {str(file.analytic_account_id.id): 100.0},
            "date_planned": fields.Datetime.to_datetime(planned),
        }

    def action_mark_performed(self):
        """The supplier performed the service: received quantity = ordered quantity (services have no stock move).
        With the bill control 'on received quantities' only performed services can be billed."""
        for line in self._boss_active_lines().filtered(lambda l: l.state == "purchase"):
            line.qty_received = line.product_qty

    def action_rebill(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "boss.rebill.wizard", "view_mode": "form",
            "views": [(False, "form")], "target": "new", "name": self.env._("Re-invoice to the customer"),
            "context": {"default_cost_id": self.id},
        }

    def action_open_purchase_lines(self):
        self.ensure_one()
        orders = self.purchase_line_ids.order_id
        return self.expediente_id._boss_action("purchase.order", orders, self.env._("Purchase orders"))

    # --- expected cost from the file's current data ----------------------------------------------------------------

    def _boss_recompute(self, reason=False):
        """Expected cost of each open service again, with the file's current data (containers, weights, volume, days,
        dates, supplier) and the same pricing engine as the quotation. The accepted sale and its snapshot are never
        touched; every change (or a price that cannot be found any more) is kept as a revision."""
        candidates = self.filtered(lambda n: not n.closed and n.state != "billed"
                                   and (n.kind == "sale" or n.tariff_line_id))
        percent = candidates.filtered(lambda n: n.product_id.boss_cost_method == "percent")
        results, related = {}, []
        for need in candidates - percent:
            results[need] = need._boss_price_now()
            res = results[need][0]
            if res.status == "ok" and res.line:
                related.append({"product_id": need.product_id.id, "supplier_id": res.line.partner_id.id,
                                "amount": res.amount, "currency": res.line.currency_id.name})
        for need in percent:  # percentages of other services of the same supplier, as on the quotation
            results[need] = need._boss_price_now(related)
        revisions = self.env["boss.expediente.cost.revision"]
        for need, (res, quantity, inputs) in results.items():
            revisions |= need._boss_apply(res, quantity, inputs, reason)
        return revisions

    def _boss_price_now(self, related_costs=None):
        self.ensure_one()
        file = self.expediente_id
        line = self.sale_line_id or self.rebill_line_id
        size, ctype = line.boss_container_size, line.boss_container_type_id
        quantity = file._boss_quantity(self.uom_id.boss_quantity_source, size, ctype)
        if quantity is None:
            quantity = self.quantity  # entered by a person (declarations, AWB...)
        inputs = dict(file._boss_inputs(), line_qty=quantity, container_size=size or None,
                      container_type_id=ctype.id or None, supplier_id=self.partner_id.id or None)
        if self.product_id.boss_cost_method == "time":
            inputs["storage_days"] = self.days
        if related_costs is not None:
            inputs["related_costs"] = related_costs
        res = self.env["boss.pricing"].price_cost(self.product_id, self.uom_id, inputs, file._boss_pricing_date(),
                                                  file.company_id)
        return res, quantity, inputs

    def _boss_apply(self, res, quantity, inputs, reason):
        self.ensure_one()
        before = {"quantity": self.quantity, "unit": self.expected_unit_cost, "currency": self.currency_id}
        status, values = res.status, {}
        if status == "ok" and res.line:
            currency = res.line.currency_id
            if currency != self.currency_id and self._boss_active_lines():
                status = "currency"  # ordered in another currency: a person decides
            else:
                values = {"quantity": quantity, "expected_unit_cost": res.amount / quantity if quantity else 0.0,
                          "currency_id": currency.id, "tariff_line_id": res.line.id}
        elif status == "manual" or not self.tariff_line_id:
            status, values = "manual", {"quantity": quantity}  # typed cost per unit kept, quantity from the file
        currency = self.env["res.currency"].browse(values.get("currency_id")) or self.currency_id
        changed = bool(values) and bool(
            float_compare(values["quantity"], before["quantity"], precision_digits=6)
            or currency != before["currency"]
            or currency.compare_amounts(values.get("expected_unit_cost", before["unit"]), before["unit"]))
        if not changed and status in ("ok", "manual"):
            return self.env["boss.expediente.cost.revision"]
        if changed:
            super(BossExpedienteCost, self).write(dict(values, expected_date=fields.Datetime.now()))
            self._boss_update_draft_rfqs()
        explanation = self.env["boss.pricing"].explain(
            self.product_id, self.uom_id, res.status, res.amount, res.line, res.candidates, res.missing, res.steps)
        return self.env["boss.expediente.cost.revision"].create({
            "cost_id": self.id, "reason": reason, "status": status, "applied": changed,
            "old_quantity": before["quantity"], "new_quantity": self.quantity,
            "old_unit_cost": before["unit"], "new_unit_cost": self.expected_unit_cost,
            "old_currency_id": before["currency"].id, "currency_id": self.currency_id.id,
            "explanation": explanation, "inputs": {k: v for k, v in inputs.items() if k != "related_costs"},
        })

    def _boss_update_draft_rfqs(self):
        """Draft RFQs (not sent) follow the new expectation; sent or confirmed orders are commitments: unchanged and
        flagged for review."""
        drafts = self._boss_active_lines().filtered(lambda l: l.order_id.state == "draft")
        if not drafts:
            return
        drafts.filtered(lambda l: l.currency_id == self.currency_id).write({"price_unit": self.expected_unit_cost})
        excess = -self._boss_remaining_qty()
        for line in drafts.sorted("id", reverse=True):
            if excess <= 0:
                break
            cut = min(excess, line.product_qty)
            line.product_qty -= cut
            excess -= cut

    def action_open_revisions(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "boss.expediente.cost.revision", "view_mode": "list",
                "views": [(False, "list")], "domain": [("cost_id", "=", self.id)],
                "name": self.env._("Recalculations of %s", self.display_name)}


class BossExpedienteCostRevision(models.Model):
    """One recalculation of the expected cost of a file service: what changed, why and with which data."""

    _name = "boss.expediente.cost.revision"
    _description = "Recalculation of an expected cost"
    _order = "date desc, id desc"

    cost_id = fields.Many2one("boss.expediente.cost", "Service", required=True, ondelete="cascade", index=True)
    expediente_id = fields.Many2one(related="cost_id.expediente_id", store=True, index=True)
    company_id = fields.Many2one(related="cost_id.company_id", store=True)
    product_id = fields.Many2one(related="cost_id.product_id")
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    reason = fields.Char()
    status = fields.Selection(COST_STATUSES + [("currency", "Ordered in another currency")], "Result")
    applied = fields.Boolean("Expected cost changed")
    old_quantity = fields.Float("Quantity before", digits="Product Unit")
    new_quantity = fields.Float("Quantity", digits="Product Unit")
    old_currency_id = fields.Many2one("res.currency")
    currency_id = fields.Many2one("res.currency")
    old_unit_cost = fields.Monetary("Unit cost before", currency_field="old_currency_id")
    new_unit_cost = fields.Monetary("Unit cost", currency_field="currency_id")
    old_amount = fields.Monetary("Cost before", currency_field="old_currency_id", compute="_compute_amounts",
                                 store=True)
    new_amount = fields.Monetary("Cost", currency_field="currency_id", compute="_compute_amounts", store=True)
    explanation = fields.Text("How the cost is computed")
    inputs = fields.Json("Data used")

    @api.depends("old_quantity", "old_unit_cost", "new_quantity", "new_unit_cost")
    def _compute_amounts(self):
        for revision in self:
            revision.old_amount = revision.old_quantity * revision.old_unit_cost
            revision.new_amount = revision.new_quantity * revision.new_unit_cost
