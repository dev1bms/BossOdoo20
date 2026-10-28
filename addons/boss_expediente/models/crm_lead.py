from odoo import Command, api, fields, models

from .boss_expediente import PACKAGE_TYPES

# Opportunity field -> quotation field (same names, one meaning). Passed once to a new quotation, never synchronised.
# Route (ADR-006): the stored inputs only; the quotation derives its Spanish port, country abroad, province and date.
ROUTE_FIELDS = ("boss_business", "boss_direction", "boss_transport_mode", "boss_load_type", "boss_carrier_id",
                "boss_shipper_id", "boss_origin_country_id", "boss_origin_port_id", "boss_pickup_address_id",
                "boss_origin_place", "boss_consignee_id", "boss_destination_country_id", "boss_destination_port_id",
                "boss_delivery_address_id", "boss_destination_place", "boss_inland_state_id", "boss_etd", "boss_eta",
                "boss_gross_kg",
                "boss_volume_m3", "boss_awb_kg")
TO_QUOTATION = {
    **{name: name for name in ROUTE_FIELDS},
    "boss_pallets": "boss_pallets", "boss_packages": "boss_packages", "boss_goods_value": "boss_goods_value",
    "boss_package_type": "boss_package_type", "boss_hs_code": "boss_hs_code",
    "boss_goods_description": "boss_goods_description", "boss_incoterm_id": "incoterm",
    "boss_scope_pickup": "boss_scope_pickup", "boss_scope_origin_customs": "boss_scope_origin_customs",
    "boss_scope_main": "boss_scope_main", "boss_scope_destination_customs": "boss_scope_destination_customs",
    "boss_scope_delivery": "boss_scope_delivery",
}
# Opportunities written before ADR-006 have no origin/destination: their pricing inputs are passed as they are.
LEGACY_TO_QUOTATION = ("boss_port_id", "boss_country_id", "boss_planned_date")


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "boss.shipment.route"]

    # What the customer asks for, completed little by little; the quotation receives it once. Route, dates and
    # weights: boss.shipment.route (ADR-006).
    boss_incoterm_id = fields.Many2one("account.incoterms", "Incoterm")
    boss_scope_pickup = fields.Boolean("Pickup")
    boss_scope_origin_customs = fields.Boolean("Customs at origin")
    boss_scope_main = fields.Boolean("Main carriage")
    boss_scope_destination_customs = fields.Boolean("Customs at destination")
    boss_scope_delivery = fields.Boolean("Delivery")
    boss_goods_description = fields.Char("Goods")
    boss_packages = fields.Integer("Packages")
    boss_package_type = fields.Selection(PACKAGE_TYPES, "Type of unit")
    boss_hs_code = fields.Char("Goods code (HS)")
    boss_pallets = fields.Integer("Pallets")
    boss_goods_value = fields.Monetary("Goods value", currency_field="company_currency")
    boss_container_ids = fields.One2many("boss.shipment.container", "lead_id", "Containers")
    boss_service_ids = fields.Many2many(
        "product.product", string="Requested services",
        domain="[('boss_pricing_mode', '!=', False), ('sale_ok', '=', True)]",
        help="Services the customer asks for; proposed when services are added to the quotation.")

    @api.onchange("partner_id", "boss_direction", "boss_business")
    def _onchange_boss_orderer_party(self):
        self._boss_apply_orderer_party()

    def _prepare_opportunity_quotation_context(self):
        context = super()._prepare_opportunity_quotation_context()
        fields_map = dict(TO_QUOTATION)
        if not self._boss_route_known():
            fields_map.update({name: name for name in LEGACY_TO_QUOTATION})
        for lead_field, order_field in fields_map.items():
            value = self[lead_field]
            if isinstance(value, models.BaseModel):
                value = value.id
            if value:
                context[f"default_{order_field}"] = value
        if self.boss_container_ids:
            context["default_boss_container_ids"] = [
                Command.create({"size": c.size, "container_type_id": c.container_type_id.id, "quantity": c.quantity})
                for c in self.boss_container_ids]
        if self.boss_service_ids:
            context["default_boss_requested_service_ids"] = [Command.set(self.boss_service_ids.ids)]
        return context
