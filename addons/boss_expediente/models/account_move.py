from odoo import api, fields, models
from odoo.exceptions import UserError

BILL_TYPES = ("in_invoice", "in_refund", "in_receipt")


class ResCompany(models.Model):
    _inherit = "res.company"

    # Cristina's requirement («Nuevo Odoo», Facturación A3, Facturación y costes A11): a supplier bill is not posted
    # or paid before its service is invoiced to the customer. Approved 23/10/2026 (Belal, P30): the bill is posted on
    # time (it must be recorded when received) and its PAYMENT waits for the customer invoice.
    boss_bill_before_invoice = fields.Selection(
        [("warn", "Warn only"), ("block_payment", "Block payment (posting allowed)"),
         ("block", "Block posting and payment")],
        "Supplier bill before the customer invoice", default="block_payment", required=True)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    boss_bill_before_invoice = fields.Selection(related="company_id.boss_bill_before_invoice", readonly=False)


class AccountMove(models.Model):
    _inherit = "account.move"

    boss_bill_warning = fields.Text("Supplier bill checks", compute="_compute_boss_bill_warning")

    def _boss_bill_needs(self):
        """File services billed by this vendor bill: through its purchase lines, or (amounts paid on behalf, billed
        without purchase order) through the service and the file's analytic account."""
        self.ensure_one()
        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == "product" and l.product_id)
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
            elif not sale_line._boss_posted_invoiced_qty():
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
            if problems:
                raise UserError(_("%(move)s cannot be posted:\n%(problems)s",
                                  move=move.display_name, problems="\n".join(f"- {p}" for p in problems)))

    def action_register_payment(self):
        for move in self.filtered(lambda m: m.move_type == "in_invoice"
                                  and m.company_id.boss_bill_before_invoice in ("block", "block_payment")):
            problems = move._boss_bill_order_problems()
            if problems:
                raise UserError(self.env._("%(move)s cannot be paid yet:\n%(problems)s", move=move.display_name,
                                           problems="\n".join(f"- {p}" for p in problems)))
        return super().action_register_payment()

    def _boss_refresh_file_needs(self):
        """Services billed without purchase order follow their bills (state and billed amount)."""
        needs = self.env["boss.expediente.cost"]
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

    def _related_analytic_distribution(self):
        """A bill entered from a file (cost without purchase order) is charged to the file's analytic account."""
        values = super()._related_analytic_distribution()
        default = self.env.context.get("boss_default_analytic")
        if default and not values and self.display_type == "product":
            values = dict(default)
        return values
