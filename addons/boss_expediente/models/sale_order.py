from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError

from .boss_expediente import FROM_ORDER


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Route and scope agreed with the customer (the quotation basis); the file keeps the actual data.
    boss_origin_place = fields.Char("Origin (place)")
    boss_destination_place = fields.Char("Destination (place)")
    boss_scope_pickup = fields.Boolean("Pickup")
    boss_scope_origin_customs = fields.Boolean("Customs at origin")
    boss_scope_main = fields.Boolean("Main carriage")
    boss_scope_destination_customs = fields.Boolean("Customs at destination")
    boss_scope_delivery = fields.Boolean("Delivery")
    boss_shipper_id = fields.Many2one("res.partner", "Shipper")
    boss_consignee_id = fields.Many2one("res.partner", "Consignee")
    boss_goods_description = fields.Char("Goods")
    boss_packages = fields.Integer("Packages")
    boss_requested_service_ids = fields.Many2many(
        "product.product", string="Requested services",
        domain="[('boss_pricing_mode', '!=', False), ('sale_ok', '=', True)]",
        help="Services the customer asked for (from the opportunity); proposed by 'Add services'.")
    boss_expediente_id = fields.Many2one(
        "boss.expediente", "File", copy=False, index="btree_not_null", tracking=True,
        domain="[('state', '!=', 'cancel'), ('financial_closed', '=', False)]",
        help="Shipment file of this order. Empty: opened when the quotation is accepted. Choose a file to add a "
        "service sold later or to link a file opened before the quotation (pre-alert).")

    @api.constrains("boss_expediente_id", "partner_id")
    def _check_boss_expediente_customer(self):
        for order in self.filtered("boss_expediente_id"):
            if order.partner_id.commercial_partner_id != order.boss_expediente_id.partner_id.commercial_partner_id:
                raise ValidationError(self.env._(
                    "%(order)s and file %(file)s have different customers.", order=order.name,
                    file=order.boss_expediente_id.name))

    def _boss_file_values(self):
        """A new file starts from the accepted quotation; afterwards each keeps its own data."""
        self.ensure_one()
        values = {}
        for file_field, order_field in FROM_ORDER.items():
            value = self[order_field]
            values[file_field] = value.id if isinstance(value, models.BaseModel) else value
        planned = "eta" if self.boss_direction != "export" else "etd"
        values.update({
            "partner_id": self.partner_id.commercial_partner_id.id, "user_id": self.user_id.id,
            "company_id": self.company_id.id, planned: self.boss_planned_date,
            "container_ids": [Command.create({"size": c.size, "container_type_id": c.container_type_id.id})
                              for c in self.boss_container_ids for _ in range(c.quantity)],
        })
        return values

    def _boss_open_files(self):
        """Accepted BOSS orders get a file once: the linked one (preliminary file or service sold later) or a new
        one. Confirming again or twice never opens a second file."""
        File = self.env["boss.expediente"]
        for order in self.filtered(lambda o: o.state == "sale" and o.order_line._boss_lines()):
            file = order.boss_expediente_id or File.create(order._boss_file_values())
            if order.boss_expediente_id != file:
                order.boss_expediente_id = file
            file._boss_link_orders(order)

    def action_confirm(self):
        res = super().action_confirm()
        self._boss_open_files()
        return res

    def action_boss_open_file(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window", "res_model": "boss.expediente", "view_mode": "form",
                "views": [(False, "form")], "res_id": self.boss_expediente_id.id}

    def _get_invoiceable_lines(self, final=False):
        """Invoice selected services only (milestones, partial invoicing): the selection comes from the 'Invoice
        services' wizard; without it the standard rule applies."""
        lines = super()._get_invoiceable_lines(final)
        selected = self.env.context.get("boss_invoice_line_ids")
        if selected is None:
            return lines
        return lines.filtered(lambda l: l.id in selected)


class BossAddServices(models.TransientModel):
    _inherit = "boss.add.services"

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        order = self.env["sale.order"].browse(values.get("order_id") or self.env.context.get("default_order_id"))
        if "product_ids" in fields_list and not values.get("product_ids") and order.boss_requested_service_ids:
            missing = order.boss_requested_service_ids - order.order_line.product_id
            values["product_ids"] = [Command.set(missing.ids)]
        return values
