from odoo import Command, fields, models

from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES

# Opportunity field -> quotation field (same names, one meaning). Passed once to a new quotation, never synchronised.
TO_QUOTATION = {
    "boss_direction": "boss_direction", "boss_transport_mode": "boss_transport_mode",
    "boss_load_type": "boss_load_type", "boss_carrier_id": "boss_carrier_id", "boss_port_id": "boss_port_id",
    "boss_country_id": "boss_country_id", "boss_planned_date": "boss_planned_date",
    "boss_inland_state_id": "boss_inland_state_id", "boss_gross_kg": "boss_gross_kg",
    "boss_volume_m3": "boss_volume_m3", "boss_awb_kg": "boss_awb_kg", "boss_pallets": "boss_pallets",
    "boss_packages": "boss_packages", "boss_goods_value": "boss_goods_value",
    "boss_goods_description": "boss_goods_description", "boss_incoterm_id": "incoterm",
    "boss_origin_place": "boss_origin_place", "boss_destination_place": "boss_destination_place",
    "boss_shipper_id": "boss_shipper_id", "boss_consignee_id": "boss_consignee_id",
    "boss_scope_pickup": "boss_scope_pickup", "boss_scope_origin_customs": "boss_scope_origin_customs",
    "boss_scope_main": "boss_scope_main", "boss_scope_destination_customs": "boss_scope_destination_customs",
    "boss_scope_delivery": "boss_scope_delivery",
}


class CrmLead(models.Model):
    _inherit = "crm.lead"

    # What the customer asks for, completed little by little; the quotation receives it once.
    boss_direction = fields.Selection(DIRECTIONS, "Direction")
    boss_transport_mode = fields.Selection(TRANSPORT_MODES, "Transport mode")
    boss_load_type = fields.Selection(LOAD_TYPES, "Load type")
    boss_carrier_id = fields.Many2one("res.partner", "Carrier")
    boss_port_id = fields.Many2one("boss.port", "Spanish port / airport")
    boss_country_id = fields.Many2one("res.country", "Country abroad")
    boss_planned_date = fields.Date("Planned date", help="ETA for imports, ETD for exports.")
    boss_inland_state_id = fields.Many2one("res.country.state", "Inland province",
                                           domain="[('country_id.code', '=', 'ES')]")
    boss_incoterm_id = fields.Many2one("account.incoterms", "Incoterm")
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
    boss_gross_kg = fields.Float("Gross weight (kg)", digits=(12, 2))
    boss_volume_m3 = fields.Float("Volume (m³)", digits=(12, 3))
    boss_awb_kg = fields.Float("Chargeable weight (AWB, kg)", digits=(12, 2))
    boss_pallets = fields.Integer("Pallets")
    boss_goods_value = fields.Monetary("Goods value", currency_field="company_currency")
    boss_container_ids = fields.One2many("boss.shipment.container", "lead_id", "Containers")
    boss_service_ids = fields.Many2many(
        "product.product", string="Requested services",
        domain="[('boss_pricing_mode', '!=', False), ('sale_ok', '=', True)]",
        help="Services the customer asks for; proposed when services are added to the quotation.")

    def _prepare_opportunity_quotation_context(self):
        context = super()._prepare_opportunity_quotation_context()
        for lead_field, order_field in TO_QUOTATION.items():
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
