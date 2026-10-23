from odoo import models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        self._boss_check_post()
        return super()._post(soft)

    def _boss_check_post(self):
        """No document is posted with an undecided VAT treatment (ADR-004/005). Customer documents also need the
        recipient data of a complete invoice; a supplier bill of a file's service waits until that service is
        invoiced to the customer (Cristina, requirements «Facturación» A3), unless BOSS bears the cost."""
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
                missing = move.partner_id._boss_invoice_missing() if lines else []
                if missing:
                    problems.append(_("customer %(partner)s: %(missing)s missing",
                                      partner=move.partner_id.commercial_partner_id.display_name,
                                      missing=", ".join(missing)))
            elif move.move_type in ("in_invoice", "in_refund"):
                for line in lines.filtered(lambda l: not l.tax_ids):
                    problems.append(_("%s: choose the tax shown on the supplier invoice (0 %% included)",
                                      line.product_id.display_name))
                if move.move_type == "in_invoice":
                    for line in lines.filtered("purchase_line_id.boss_cost_id"):
                        need = line.purchase_line_id.boss_cost_id
                        if need.extra_class in ("approval", "disputed"):
                            problems.append(_("%(service)s: extra cost still '%(cls)s'", service=need.display_name,
                                              cls=dict(need._fields["extra_class"]._description_selection(
                                                  self.env))[need.extra_class]))
                            continue
                        sale_line = need.sale_line_id or need.rebill_line_id
                        if need.extra_class not in ("absorb", "covered") and sale_line and not sale_line.qty_invoiced:
                            problems.append(_("%s: not invoiced to the customer yet", need.display_name))
            if problems:
                raise UserError(_("%(move)s cannot be posted:\n%(problems)s",
                                  move=move.display_name, problems="\n".join(f"- {p}" for p in problems)))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _related_analytic_distribution(self):
        """A bill entered from a file (cost without purchase order) is charged to the file's analytic account."""
        values = super()._related_analytic_distribution()
        default = self.env.context.get("boss_default_analytic")
        if default and not values and self.display_type == "product":
            values = dict(default)
        return values
