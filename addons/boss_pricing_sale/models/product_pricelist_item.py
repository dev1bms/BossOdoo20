from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from odoo.tools.misc import formatLang

BOSS_LINE_COST = "boss_line_cost"


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    # Sale price from the expected cost of the quotation line (shipment-dependent), with the standard
    # pricelist tools: surcharge % on cost (markup), rounding, extra fee, minimum/maximum margin per unit.
    base = fields.Selection(
        selection_add=[(BOSS_LINE_COST, "Expected cost of the quotation line (BOSS)")],
        ondelete={BOSS_LINE_COST: "set default"})
    boss_sale_margin = fields.Float(
        "Margin on sale (%)", digits=(16, 2),
        help="Price so that (price - cost) / price is this percentage: price = cost / (1 - margin). "
        "Use it instead of the surcharge on cost, not both. Only with the expected cost of the quotation line.")

    @api.model
    def _boss_markup_to_discount(self, vals):
        # The surcharge is stored as a negative discount by an inverse that runs after the constraints:
        # store it up front so that 'markup or margin, not both' sees the final values (form, import, RPC).
        if "price_markup" in vals and "price_discount" not in vals:
            vals = dict(vals, price_discount=-(vals["price_markup"] or 0.0))
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._boss_markup_to_discount(vals) for vals in vals_list])

    def write(self, vals):
        return super().write(self._boss_markup_to_discount(vals))

    @api.constrains("base", "boss_sale_margin", "compute_price", "price_discount")
    def _check_boss_sale_margin(self):
        for item in self:
            if not item.boss_sale_margin:
                continue
            if item.base != BOSS_LINE_COST or item.compute_price == "fixed":
                raise ValidationError(self.env._(
                    "A margin on sale applies only to rules based on the expected cost of the quotation line."))
            if not 0 < item.boss_sale_margin < 100:
                raise ValidationError(self.env._("The margin on sale must be between 0 and 100 %."))
            if item.price_discount:
                raise ValidationError(self.env._(
                    "Use either a surcharge on cost (markup) or a margin on sale, not both."))

    @api.constrains("price_min_margin", "price_max_margin")
    def _check_margin(self):
        # Standard refuses a minimum margin without a maximum, while its price computation reads a 0 maximum
        # as 'no maximum': only compare when a maximum is set (a minimum margin alone is a valid agreement).
        if any(item.price_max_margin and item.price_min_margin > item.price_max_margin for item in self):
            raise ValidationError(self.env._("The minimum margin should be lower than the maximum margin."))

    def _get_price_label_base_str(self):
        if self.base == BOSS_LINE_COST:
            return self.env._("expected cost of the quotation line")
        return super()._get_price_label_base_str()

    @api.depends("boss_sale_margin", "price_min_margin")
    def _compute_price_label(self):
        super()._compute_price_label()
        for item in self.filtered(lambda i: i.base == BOSS_LINE_COST and i.compute_price != "fixed"):
            if item.boss_sale_margin:
                text = self.env._("%(margin)s %% margin on sale over the expected cost of the line",
                                  margin=item._get_integer(item.boss_sale_margin))
            else:
                text = self.env._("Expected cost of the line %(sign)s %(rate)s %%",
                                  sign="+" if item.price_markup >= 0 else "-", rate=item._get_integer(abs(item.price_markup)))
            if item.price_min_margin:
                text += " " + self.env._("(minimum margin %s per unit)", formatLang(
                    self.env, item.price_min_margin, currency_obj=item.currency_id))
            item.price = text

    def _compute_base_price(self, product, quantity, uom, *, currency=None, depth=0, base_prices=None, **kwargs):
        if self.base != BOSS_LINE_COST:
            return super()._compute_base_price(product, quantity, uom, currency=currency, depth=depth,
                                               base_prices=base_prices, **kwargs)
        if not product.boss_pricing_mode:
            # a global «cost + %» rule meets a product that is not a BOSS service: its sales price, like the
            # standard list-price rule
            price = product._price_compute("list_price", uom=uom)[product.id]
            return self._convert_price(price, product.currency_id, currency=currency, **kwargs)
        # Unit cost of the quotation line, already in the order currency (sale.order.line passes it).
        return kwargs.get("boss_unit_cost") or 0.0

    def _compute_price(self, product, quantity, uom, **kwargs):
        if self.base == BOSS_LINE_COST and not product.boss_pricing_mode:
            # the «expected cost + %» rule says nothing about a product that is not a BOSS service: its list price
            return self._compute_base_price(product, quantity, uom or product._get_main_uom(), **kwargs)
        if self.base != BOSS_LINE_COST or not self.boss_sale_margin or self.compute_price == "fixed":
            return super()._compute_price(product, quantity, uom, **kwargs)
        # Same steps as the standard rule (rounding, extra fee, min/max margin over the cost), with the
        # price grossed up to the margin on sale instead of a surcharge on cost.
        uom = uom or product._get_main_uom()
        cost = self._compute_base_price(product, quantity, uom, **kwargs)
        price = cost / (1 - self.boss_sale_margin / 100)
        if self.price_round:
            price = float_round(price, precision_rounding=self.price_round)
        product_uom = product.uom_id
        if self.price_surcharge:
            price += product_uom._compute_price(self.price_surcharge, uom)
        if self.price_min_margin:
            price = max(price, cost + product_uom._compute_price(self.price_min_margin, uom))
        if self.price_max_margin:
            price = min(price, cost + product_uom._compute_price(self.price_max_margin, uom))
        return price

    @api.onchange("product_tmpl_id", "product_id")
    def _onchange_boss_service_uom(self):
        """A BOSS service price needs its charge basis: start from the service's own unit (the form shows «per <unit>»
        next to the price but left the unit empty, so saving failed; found in Chrome on boss20, 27/10/2026)."""
        template = self.product_id.product_tmpl_id or self.product_tmpl_id
        if template.boss_pricing_mode and not self.uom_id:
            self.uom_id = template.uom_id

    # Standard pricelists hold agreed sale prices of BOSS services, with two guards (spike T2b, T3):
    # a price says its charge basis, and two prices for the same case never overlap silently.
    @api.constrains("product_tmpl_id", "product_id", "uom_id", "pricelist_id", "min_quantity",
                    "date_start", "date_end")
    def _check_boss_service_prices(self):
        for item in self:
            template = item.product_id.product_tmpl_id or item.product_tmpl_id
            if not template.boss_pricing_mode:
                continue
            if not item.uom_id and item.compute_price == "fixed":
                raise ValidationError(self.env._(
                    "A price of %s must say its charge basis (container 40', B/L, kg...).",
                    template.display_name))
            same = self.search([
                ("id", "!=", item.id), ("pricelist_id", "=", item.pricelist_id.id),
                ("product_tmpl_id", "=", template.id), ("product_id", "=", item.product_id.id),
                ("uom_id", "=", item.uom_id.id), ("min_quantity", "=", item.min_quantity),
            ])
            for other in same:
                starts_before_end = not other.date_end or not item.date_start or item.date_start <= other.date_end
                ends_after_start = not other.date_start or not item.date_end or item.date_end >= other.date_start
                if starts_before_end and ends_after_start:
                    raise ValidationError(self.env._(
                        "Two prices of %(service)s per %(uom)s overlap in %(pricelist)s: keep one, or "
                        "make their dates consecutive.", service=template.display_name,
                        uom=item.uom_id.name, pricelist=item.pricelist_id.name))
