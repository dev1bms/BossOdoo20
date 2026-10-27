from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES


class BossSupplierPriceWizard(models.TransientModel):
    """Missing supplier price on a quotation line: record it where it belongs (a supplier tariff),
    with the shipment context pre-filled, then come back to the quotation (ADR-003)."""

    _name = "boss.supplier.price.wizard"
    _description = "Add a supplier price from a quotation"

    sale_line_id = fields.Many2one("sale.order.line", required=True)
    product_id = fields.Many2one(related="sale_line_id.product_id")
    uom_id = fields.Many2one(related="sale_line_id.product_uom_id", string="Charge basis")
    partner_id = fields.Many2one("res.partner", "Supplier",  # required in the form; checked on save
                                 compute="_compute_partner_id", store=True, readonly=False, precompute=True)
    tariff_id = fields.Many2one(
        "boss.tariff", "Add to draft tariff",
        domain="[('partner_id', '=', partner_id), ('state', '=', 'draft')]",
        help="Empty: a new tariff is created with the data below.")
    # New tariff: header and scope, pre-filled from the quotation (editable).
    tariff_name = fields.Char("Tariff name", compute="_compute_tariff_name", store=True, readonly=False, precompute=True)
    valid_from = fields.Date(compute="_compute_valid_from", store=True, readonly=False, precompute=True)
    valid_to = fields.Date(compute="_compute_valid_to", store=True, readonly=False, precompute=True,
                           help="A freight offer is valid for days, not a year: a week by default.")
    currency_id = fields.Many2one("res.currency", compute="_compute_currency_id", store=True, readonly=False, precompute=True)
    document = fields.Binary("Supplier document")
    document_name = fields.Char()
    document_reference = fields.Char()
    direction = fields.Selection(DIRECTIONS, compute="_compute_scope", store=True, readonly=False, precompute=True)
    transport_mode = fields.Selection(TRANSPORT_MODES, compute="_compute_scope", store=True, readonly=False, precompute=True)
    load_type = fields.Selection(LOAD_TYPES, compute="_compute_scope", store=True, readonly=False, precompute=True)
    carrier_id = fields.Many2one("res.partner", "Carrier", compute="_compute_carrier_id", store=True, readonly=False, precompute=True)
    port_ids = fields.Many2many("boss.port", string="Ports", compute="_compute_port_ids", store=True,
                                readonly=False, precompute=True)
    foreign_port_ids = fields.Many2many(
        "boss.port", "boss_supplier_price_wizard_foreign_port_rel", "wizard_id", "port_id", "Ports / airports abroad",
        compute="_compute_foreign_port_ids", store=True, readonly=False, precompute=True,
        help="The route of this price: origin port of an import, destination port of an export. Empty: any.")
    spot_rate = fields.Boolean(compute="_compute_spot_rate", help="Freight offer valid for a short time.")
    country_ids = fields.Many2many("res.country", string="Countries abroad", compute="_compute_country_ids",
                                   store=True, readonly=False, precompute=True)
    container_size = fields.Selection(related="sale_line_id.boss_container_size", string="Container size")
    container_type_id = fields.Many2one(related="sale_line_id.boss_container_type_id", string="Container type")
    price_by_container_type = fields.Boolean(
        "Only for this container type", help="The document prices this container type differently.")
    only_this_customer = fields.Boolean(help="Price agreed for this customer only.")
    # The price itself.
    unit_price = fields.Float(min_display_digits="Product Price")  # required in the form; checked on save
    min_amount = fields.Float("Minimum", min_display_digits="Product Price")
    max_amount = fields.Float("Maximum", min_display_digits="Product Price")
    document_page = fields.Char("Page")
    tariff_scope = fields.Char(related="tariff_id.scope_summary", string="Tariff applies to")
    tariff_scope_confirmed = fields.Boolean(
        "Tariff scope reviewed", compute="_compute_tariff_scope_confirmed", store=True, readonly=False,
        help="The scope of the chosen draft tariff matches its supplier document (empty fields = applies to any). "
        "Needed to send it for approval.")
    submit = fields.Boolean("Send for approval now", default=True,
                            help="Needs the supplier document. Approval is always a separate step.")

    # One compute per field: a value given by the caller (form, import, RPC) never blanks the others
    # (the ORM leaves the siblings of a shared compute empty: odoo/orm/models.py, _add_precomputed_values).
    @api.depends("sale_line_id")
    def _compute_partner_id(self):
        for wiz in self:
            wiz.partner_id = wiz.sale_line_id.boss_supplier_id or wiz.sale_line_id.order_id.boss_carrier_id

    @api.depends("sale_line_id", "partner_id", "valid_from")
    def _compute_tariff_name(self):
        for wiz in self:
            year = (wiz.valid_from or fields.Date.today()).year
            wiz.tariff_name = f"{wiz.partner_id.name or ''} {wiz.sale_line_id.product_id.default_code or ''} {year}".strip()

    @api.depends("sale_line_id")
    def _compute_valid_from(self):
        for wiz in self:
            wiz.valid_from = wiz.sale_line_id.order_id.boss_planned_date or fields.Date.today()

    @api.depends("sale_line_id")
    def _compute_spot_rate(self):
        for wiz in self:
            wiz.spot_rate = wiz.sale_line_id.product_id.boss_pricing_mode == "manual"

    @api.depends("valid_from", "spot_rate")
    def _compute_valid_to(self):
        for wiz in self:
            wiz.valid_to = (wiz.valid_from + timedelta(days=6)) if wiz.spot_rate and wiz.valid_from else wiz.valid_to

    @api.depends("sale_line_id")
    def _compute_foreign_port_ids(self):
        for wiz in self:
            wiz.foreign_port_ids = wiz.sale_line_id.order_id._boss_foreign_port()

    @api.depends("sale_line_id")
    def _compute_currency_id(self):
        for wiz in self:
            wiz.currency_id = wiz.sale_line_id.order_id.currency_id

    @api.depends("sale_line_id")
    def _compute_scope(self):
        for wiz in self:
            order = wiz.sale_line_id.order_id
            wiz.direction = order.boss_direction
            wiz.transport_mode = order.boss_transport_mode
            wiz.load_type = order.boss_load_type

    @api.depends("sale_line_id")
    def _compute_carrier_id(self):
        for wiz in self:
            wiz.carrier_id = wiz.sale_line_id.order_id.boss_carrier_id

    @api.depends("sale_line_id")
    def _compute_port_ids(self):
        for wiz in self:
            wiz.port_ids = wiz.sale_line_id.order_id.boss_port_id

    @api.depends("sale_line_id")
    def _compute_country_ids(self):
        for wiz in self:
            wiz.country_ids = wiz.sale_line_id.order_id.boss_country_id

    def _check_complete(self):
        """Clear message instead of a database error when the caller left out what a price needs."""
        _ = self.env._
        missing = [label for label, ok in (
            (_("supplier"), self.partner_id), (_("currency"), self.tariff_id or self.currency_id),
            (_("valid from"), self.tariff_id or self.valid_from), (_("tariff name"), self.tariff_id or self.tariff_name),
            (_("unit price"), self.unit_price > 0),
        ) if not ok]
        if missing:
            raise UserError(_("The supplier price cannot be saved, missing: %s.", ", ".join(missing)))

    def _tariff_values(self):
        order = self.sale_line_id.order_id
        return {
            "name": self.tariff_name, "partner_id": self.partner_id.id, "currency_id": self.currency_id.id,
            "valid_from": self.valid_from, "valid_to": self.valid_to, "document": self.document,
            "document_name": self.document_name, "document_reference": self.document_reference,
            "direction": self.direction, "transport_mode": self.transport_mode, "load_type": self.load_type,
            "carrier_id": self.carrier_id.id, "port_ids": [(6, 0, self.port_ids.ids)],
            "foreign_port_ids": [(6, 0, self.foreign_port_ids.ids)],
            "country_ids": [(6, 0, self.country_ids.ids)],
            "customer_id": order.partner_id.commercial_partner_id.id if self.only_this_customer else False,
            # the scope was shown and edited here (taken from the quotation): reviewed
            "scope_confirmed": True,
            "is_demo": order.partner_id.commercial_partner_id.boss_demo,
        }

    @api.depends("tariff_id")
    def _compute_tariff_scope_confirmed(self):
        for wizard in self:
            wizard.tariff_scope_confirmed = wizard.tariff_id.scope_confirmed

    def action_save(self):
        self.ensure_one()
        self._check_complete()
        if self.submit and not (self.document or (self.tariff_id and self.tariff_id.document)):
            raise UserError(self.env._("Attach the supplier document to send the price for approval."))
        if self.tariff_id and self.tariff_scope_confirmed and not self.tariff_id.scope_confirmed:
            self.tariff_id.scope_confirmed = True  # reviewed here, next to the scope summary
        tariff = self.tariff_id or self.env["boss.tariff"].create(self._tariff_values())
        self.env["boss.tariff.line"].create({
            "tariff_id": tariff.id, "product_id": self.product_id.id, "uom_id": self.uom_id.id,
            "unit_price": self.unit_price, "min_amount": self.min_amount, "max_amount": self.max_amount,
            "document_page": self.document_page, "container_size": self.container_size,
            "container_type_ids": [(6, 0, self.container_type_id.ids if self.price_by_container_type else [])],
        })
        if self.submit:
            tariff.action_submit()
        self.sale_line_id._boss_recompute_cost()
        return {"type": "ir.actions.act_window_close"}
