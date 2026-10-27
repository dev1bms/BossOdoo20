from odoo import fields, models


class BossAddServices(models.TransientModel):
    _name = "boss.add.services"
    _description = "Add BOSS services to a quotation"

    order_id = fields.Many2one("sale.order", required=True)
    supplier_id = fields.Many2one(
        "res.partner", "Supplier", help="Supplier of these services (only its tariffs). Empty: any supplier.")
    product_ids = fields.Many2many(
        "product.product", string="Services", required=True,
        domain="[('boss_pricing_mode', '!=', False), ('sale_ok', '=', True)]")

    def _line_values(self, product):
        """Container services: one line per container size and type of the shipment (they may be priced
        and sold differently); other services: one line in their main charge basis."""
        base = {"order_id": self.order_id.id, "product_id": product.id, "product_uom_id": product.uom_id.id,
                "boss_supplier_id": self.supplier_id.id}
        if product.uom_id.boss_quantity_source not in ("container", "teu"):
            return [base]
        groups = sorted({(c.size, c.container_type_id) for c in self.order_id.boss_container_ids},
                        key=lambda g: (g[0], g[1].sequence))
        return [dict(base, boss_container_size=size, boss_container_type_id=ctype.id) for size, ctype in groups] or [base]

    def _is_on_order(self, vals):
        """Already on the quotation: same service, unit and container group, and the same supplier, or any supplier
        when none is chosen here (a service is added twice only on purpose, for a second supplier; found in Chrome on
        boss20, 27/10/2026: HAN was added again silently)."""
        lines = self.order_id.order_line.filtered(
            lambda l: l.product_id.id == vals["product_id"] and l.product_uom_id.id == vals["product_uom_id"]
            and (l.boss_container_size or False) == vals.get("boss_container_size", False)
            and l.boss_container_type_id.id == vals.get("boss_container_type_id", False))
        return bool(lines.filtered(lambda l: not self.supplier_id or l.boss_supplier_id == self.supplier_id))

    def action_add(self):
        self.ensure_one()
        _ = self.env._
        new, present = [], []
        for product in self.product_ids:
            values = [vals for vals in self._line_values(product) if not self._is_on_order(vals)]
            (new.extend(values) if values else present.append(product.default_code or product.name))
        lines = self.env["sale.order.line"].create(new)
        if not present:
            return {"type": "ir.actions.act_window_close"}
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {
            "title": _("Not added twice"),
            "message": _("Already on the quotation: %(present)s. Added: %(added)s. To add a service again for a "
                         "second supplier, choose that supplier here.", present=", ".join(present),
                         added=", ".join(lines.product_id.mapped("default_code")) or "-"),
            "type": "warning", "next": {"type": "ir.actions.act_window_close"}}}
