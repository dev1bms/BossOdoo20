from odoo import api, fields, models

from odoo.addons.boss_pricing.models.boss_tariff import DIRECTIONS, LOAD_TYPES, TRANSPORT_MODES

# Air cargo: 1 m³ counts as 167 kg (IATA 1:6000). The chargeable weight is the higher of the real (gross) weight and
# this volume weight (Ángel, meeting of 27/10/2026, ADR-006). Supplier documents with their own factor keep theirs.
AIR_VOLUMETRIC_FACTOR = 167
# Whose business the shipment is: the third letter of the traffic code (decision B13, Cristina 27/08/2026).
BUSINESSES = [("boss", "BOSS client"), ("agent", "Agent's client")]
_LETTERS = {"import": "I", "export": "E", "air": "A", "sea": "M", "road": "T", "boss": "B", "agent": "A"}


def traffic_code(direction, mode, business):
    """IMB, EAB, IMA...: direction, transport mode, whose client (empty until the three are known)."""
    if direction and mode and business:
        return _LETTERS[direction] + _LETTERS[mode] + _LETTERS[business]
    return False


def spanish_side(direction):
    """BOSS works in Spain: the destination of an import and the origin of an export."""
    return {"import": "destination", "export": "origin"}.get(direction)


def chargeable_kg(mode, gross_kg, volume_m3):
    """Air: higher of gross weight and volume weight; other modes have no general factor (each document says)."""
    if mode != "air" or not (gross_kg or volume_m3):
        return 0.0, 0.0
    volume_kg = (volume_m3 or 0.0) * AIR_VOLUMETRIC_FACTOR
    return volume_kg, max(gross_kg or 0.0, volume_kg)


class BossShipmentRoute(models.AbstractModel):
    """Route of a shipment as BOSS describes it (ADR-006): origin and destination (country, port or airport, address),
    ETD and ETA, whose client it is. The pricing inputs (Spanish port, country abroad, inland province, tariff date)
    are derived from it, so tariffs and VAT keep one meaning per field."""
    _name = "boss.shipment.route"
    _description = "Shipment route"

    boss_business = fields.Selection(
        BUSINESSES, "Business of", default="boss", tracking=True,
        help="BOSS client: the customer orders the shipment from BOSS. Agent's client: a partner forwarder abroad "
        "orders it for its own client (the agent is who orders and is invoiced).")
    boss_direction = fields.Selection(DIRECTIONS, "Direction", tracking=True)
    boss_transport_mode = fields.Selection(TRANSPORT_MODES, "Transport mode", tracking=True)
    boss_load_type = fields.Selection(LOAD_TYPES, "Load type", tracking=True)
    boss_traffic_code = fields.Char(
        "Traffic", compute="_compute_boss_traffic_code", store=True,
        help="Direction (I/E), mode (M sea, A air, T road) and whose client (B BOSS, A agent): IMB, EAB, IMA...")
    boss_carrier_id = fields.Many2one("res.partner", "Main carrier", tracking=True,
                                      help="Shipping line or airline of the main carriage. The haulier of a pickup or "
                                      "delivery is the supplier of that service.")
    # Origin and destination, as the customer describes the shipment.
    boss_port_kind = fields.Char(compute="_compute_boss_port_kind")
    boss_shipper_id = fields.Many2one("res.partner", "Shipper", tracking=True)
    boss_origin_country_id = fields.Many2one("res.country", "Origin country", tracking=True)
    boss_origin_port_id = fields.Many2one(
        "boss.port", "Origin port / airport", tracking=True,
        domain="[('country_id', '=?', boss_origin_country_id), ('kind', '=?', boss_port_kind)]",
        help="Port or airport of loading.")
    boss_pickup_address_id = fields.Many2one(
        "res.partner", "Pickup address", tracking=True,
        help="Where the goods are collected (export: in Spain, it gives the province of the pickup).")
    boss_origin_place = fields.Char("Origin place", compute="_compute_boss_places", store=True, readonly=False,
                                    precompute=True, help="Town of the pickup; filled from the pickup address.")
    boss_consignee_id = fields.Many2one("res.partner", "Consignee", tracking=True)
    boss_destination_country_id = fields.Many2one("res.country", "Destination country", tracking=True)
    boss_destination_port_id = fields.Many2one(
        "boss.port", "Destination port / airport", tracking=True,
        domain="[('country_id', '=?', boss_destination_country_id), ('kind', '=?', boss_port_kind)]",
        help="Port or airport of discharge.")
    boss_delivery_address_id = fields.Many2one(
        "res.partner", "Delivery address", tracking=True,
        help="Where the goods are delivered (import: in Spain, it gives the province of the delivery). A customer "
        "with several warehouses has one delivery address each.")
    boss_destination_place = fields.Char(
        "Destination place", compute="_compute_boss_places", store=True, readonly=False, precompute=True,
        help="Town of the delivery; filled from the delivery address.")
    boss_etd = fields.Date("ETD", tracking=True, help="Estimated departure from the origin port or airport.")
    boss_eta = fields.Date("ETA", tracking=True, help="Estimated arrival at the destination port or airport.")
    # Pricing inputs derived from the route (one meaning per name, like the tariff scope).
    boss_port_id = fields.Many2one(
        "boss.port", "Spanish port / airport", compute="_compute_boss_pricing_route", store=True, readonly=False,
        precompute=True, help="Port or airport in Spain where BOSS handles the cargo: the destination of an import, "
        "the origin of an export.")
    boss_country_id = fields.Many2one(
        "res.country", "Country abroad", compute="_compute_boss_pricing_route", store=True, readonly=False,
        precompute=True, help="Origin country of an import or destination country of an export. Used by tariffs and "
        "VAT.")
    boss_inland_state_id = fields.Many2one(
        "res.country.state", "Inland province", domain="[('country_id.code', '=', 'ES')]",
        compute="_compute_boss_inland_state", store=True, readonly=False, precompute=True, tracking=True,
        help="Province of the delivery (import) or pickup (export) in Spain, from its address; hauliers price by zone.")
    boss_planned_date = fields.Date(
        "Tariff date", compute="_compute_boss_planned_date", store=True, readonly=False, precompute=True,
        help="The key date of the shipment: ETA for an import, ETD for an export. It chooses the version of each "
        "supplier tariff.")
    boss_gross_kg = fields.Float("Gross weight (kg)", digits=(12, 2))
    boss_volume_m3 = fields.Float("Volume (m³)", digits=(12, 3))
    boss_awb_kg = fields.Float("Chargeable weight (AWB, kg)", digits=(12, 2),
                               help="Chargeable weight written on the air waybill; air handlers price on it. Empty: "
                               "the estimated chargeable weight is used.")
    boss_volume_weight_kg = fields.Float(
        "Volume weight (kg)", digits=(12, 2), compute="_compute_boss_chargeable_kg", store=True,
        help="Air: volume × 167 kg per m³ (IATA 1:6000).")
    boss_chargeable_kg = fields.Float(
        "Chargeable weight (kg)", digits=(12, 2), compute="_compute_boss_chargeable_kg", store=True,
        help="Air: the higher of the gross weight and the volume weight. Used as the AWB weight until the AWB is known.")

    def _valid_field_parameter(self, field, name):
        # tracking applies on the models that use this route (quotation, opportunity: both are mail threads)
        return name == "tracking" or super()._valid_field_parameter(field, name)

    @api.depends("boss_direction", "boss_transport_mode", "boss_business")
    def _compute_boss_traffic_code(self):
        for record in self:
            record.boss_traffic_code = traffic_code(record.boss_direction, record.boss_transport_mode,
                                                    record.boss_business)

    @api.depends("boss_transport_mode")
    def _compute_boss_port_kind(self):
        """Sea shipments choose among sea ports, air shipments among airports (road: any)."""
        for record in self:
            record.boss_port_kind = {"sea": "sea", "air": "air"}.get(record.boss_transport_mode, False)

    @api.depends("boss_pickup_address_id.city", "boss_delivery_address_id.city")
    def _compute_boss_places(self):
        for record in self:
            record.boss_origin_place = record.boss_pickup_address_id.city or record.boss_origin_place
            record.boss_destination_place = record.boss_delivery_address_id.city or record.boss_destination_place

    def _boss_route_known(self):
        """A record written before ADR-006 (or by code that only sets the pricing inputs) keeps them as they are."""
        return any((self.boss_origin_country_id, self.boss_origin_port_id, self.boss_destination_country_id,
                    self.boss_destination_port_id))

    @api.depends("boss_direction", "boss_origin_country_id", "boss_origin_port_id", "boss_destination_country_id",
                 "boss_destination_port_id")
    def _compute_boss_pricing_route(self):
        for record in self:
            side = spanish_side(record.boss_direction)
            if not side or not record._boss_route_known():
                record.boss_port_id, record.boss_country_id = record.boss_port_id, record.boss_country_id
                continue
            abroad = "origin" if side == "destination" else "destination"
            record.boss_port_id = record[f"boss_{side}_port_id"]
            record.boss_country_id = record[f"boss_{abroad}_country_id"]

    @api.depends("boss_direction", "boss_pickup_address_id.state_id", "boss_delivery_address_id.state_id")
    def _compute_boss_inland_state(self):
        for record in self:
            side = spanish_side(record.boss_direction)
            address = record.boss_delivery_address_id if side == "destination" else record.boss_pickup_address_id
            spanish = side and address.state_id.country_id.code == "ES"
            record.boss_inland_state_id = address.state_id if spanish else record.boss_inland_state_id

    @api.depends("boss_direction", "boss_etd", "boss_eta")
    def _compute_boss_planned_date(self):
        for record in self:
            first, second = ((record.boss_etd, record.boss_eta) if record.boss_direction == "export"
                             else (record.boss_eta, record.boss_etd))
            record.boss_planned_date = first or second or record.boss_planned_date

    @api.depends("boss_transport_mode", "boss_gross_kg", "boss_volume_m3")
    def _compute_boss_chargeable_kg(self):
        for record in self:
            record.boss_volume_weight_kg, record.boss_chargeable_kg = chargeable_kg(
                record.boss_transport_mode, record.boss_gross_kg, record.boss_volume_m3)

    def _boss_foreign_port(self):
        """Port or airport abroad for pricing: the origin of an import, the destination of an export."""
        self.ensure_one()
        side = spanish_side(self.boss_direction)
        if side == "destination":
            return self.boss_origin_port_id
        if side == "origin":
            return self.boss_destination_port_id
        return self.env["boss.port"]

    def _boss_apply_orderer_party(self):
        """BOSS business: the party who orders (partner_id of the quotation or opportunity) is the consignee of an
        import or the shipper of an export (Ángel, 27/10/2026). Only fills an empty field; an agent's business never
        copies the agent. Called by the onchange of the models that use this route."""
        if not self.partner_id:
            return
        party = self.partner_id.commercial_partner_id
        if self.boss_business != "boss":
            # an agent is neither the shipper nor the consignee: undo a proposal made while the business was BOSS
            if self.boss_consignee_id == party:
                self.boss_consignee_id = False
            if self.boss_shipper_id == party:
                self.boss_shipper_id = False
            return
        if self.boss_direction == "import" and not self.boss_consignee_id:
            self.boss_consignee_id = party
        elif self.boss_direction == "export" and not self.boss_shipper_id:
            self.boss_shipper_id = party

    def _boss_awb_weight(self):
        """AWB weight for pricing: the one written on the AWB, else the estimated chargeable weight (air)."""
        self.ensure_one()
        return self.boss_awb_kg or self.boss_chargeable_kg or None

    @api.onchange("boss_direction")
    def _onchange_boss_direction_spain(self):
        """The Spanish side of the route is Spain; the side abroad cannot be Spain."""
        spain = self.env.ref("base.es")
        side = spanish_side(self.boss_direction)
        if not side:
            return
        abroad = "origin" if side == "destination" else "destination"
        if not self[f"boss_{side}_country_id"]:
            self[f"boss_{side}_country_id"] = spain
        if self[f"boss_{abroad}_country_id"] == spain:
            self[f"boss_{abroad}_country_id"] = False
