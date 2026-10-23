"""Airport storage (ALM) with the actual period and readings not decided. FICTITIOUS tariff, shaped like an airport
handler's: per 100 kg and 24 hours, 48 h free as a threshold, Friday with a Monday exit 72 h, Saturday free until
Monday included, 10 € up to 7 periods / 20 € more, minimum 50. Expected values computed by hand."""
import base64
from datetime import date, datetime

from odoo import Command
from odoo.tests import TransactionCase, new_test_user, tagged

DOC = base64.b64encode(b"%PDF-1.4 fictitious handler tariff").decode()


def utc(day, hour, minute=0):
    """Odoo datetime (UTC) of a Madrid time in October 2026 (CEST, UTC+2): Monday 12, Friday 16, Saturday 17."""
    return datetime(2026, 10, day, hour - 2, minute)


@tagged("post_install", "-at_install")
class TestStorageAlm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.salesman = new_test_user(cls.env, "boss_alm_sales", groups="sales_team.group_sale_salesman,"
                                     "boss_pricing.group_tariff_user")
        approver = new_test_user(cls.env, "boss_alm_approver", groups="sales_team.group_sale_manager,"
                                 "boss_pricing.group_tariff_approver")
        cls.handler = cls.env["res.partner"].create({"name": "HANDLER AEREO (FICTICIO)"})
        cls.customer = cls.env["res.partner"].create({"name": "CLIENTE ALM (FICTICIO)", "country_id": ref("base.es").id})
        cls.alm = ref("boss_services.service_alm").product_variant_id
        cls.mad = ref("boss_pricing.port_esmad_air")
        tariff = cls.env["boss.tariff"].create({
            "name": "HANDLER ALM 2026", "partner_id": cls.handler.id, "currency_id": cls.env.company.currency_id.id,
            "valid_from": date(2026, 1, 1), "direction": "import", "transport_mode": "air", "document": DOC,
            "document_reference": "Doc 2026", "scope_confirmed": True, "port_ids": [Command.set(cls.mad.ids)],
            "line_ids": [Command.create({
                "product_id": cls.alm.id, "uom_id": cls.alm.uom_id.id, "method": "time", "basis": "awb_kg",
                "unit_size": 100, "period_unit": "24h", "free_hours": 48, "free_mode": "threshold",
                "friday_monday_free": 72, "saturday_until_monday": True, "tier_mode": "undecided", "min_amount": 50,
                "document_page": "5", "bracket_ids": [Command.create({"up_to": 7, "unit_price": 10}),
                                                      Command.create({"up_to": 0, "unit_price": 20})]})]})
        tariff.action_submit()
        tariff.with_user(approver).action_approve()
        cls.price = tariff.line_ids

    def _panel(self, start, end, kg=500):
        return self.env["boss.pricing.test"].with_user(self.salesman).create({
            "product_id": self.alm.id, "uom_id": self.alm.uom_id.id, "date": date(2026, 10, 12), "direction": "import",
            "transport_mode": "air", "load_type": "air", "port_id": self.mad.id, "customer_id": self.customer.id,
            "awb_kg": kg, "storage_start": start, "storage_end": end})

    def test_actual_period_in_exact_hours_and_weekday_exceptions(self):
        self.assertEqual(self.price.period_unit, "24h")
        cases = [  # (start, end, expected cost)
            (utc(12, 10), utc(14, 10), 0.0),  # 48 h 00 min: free
            (utc(12, 10), utc(14, 10, 1), 150.0),  # 48 h 01 min: 3 periods x 5 x 10 from the start
            (utc(16, 9), utc(19, 8), 0.0),  # Friday -> Monday, 71 h <= 72 h
            (utc(16, 9), utc(19, 10), 200.0),  # Friday -> Monday, 73 h: 4 periods
            (utc(16, 9), utc(20, 8), 200.0),  # Friday -> Tuesday, 95 h: 4 periods
            (utc(17, 9), utc(19, 23, 59), 0.0),  # Saturday -> Monday 23:59 (Madrid)
            (utc(17, 9), utc(20, 8), 150.0),  # Saturday -> Tuesday 08:00: 71 h, 3 periods
        ]
        for start, end, expected in cases:
            panel = self._panel(start, end)
            self.assertEqual((panel.status, panel.cost_amount), ("ok", expected), f"{start} -> {end}")
        self.assertIn("12/10/2026 10:00", self._panel(utc(12, 10), utc(14, 10, 1)).explanation)  # Madrid time shown
        # 80 kg: 3 x 0.8 x 10 = 24 -> minimum 50; the free stay stays 0, never the minimum
        self.assertEqual(self._panel(utc(12, 10), utc(15, 9), kg=80).cost_amount, 50.0)
        self.assertEqual(self._panel(utc(12, 10), utc(14, 10), kg=80).cost_amount, 0.0)

    def test_undecided_tiers_are_not_priced_and_need_a_cost_by_hand(self):
        # 10 periods: day by day 7 x 5 x 10 + 3 x 5 x 20 = 650; whole stay 10 x 5 x 20 = 1,000
        panel = self._panel(utc(12, 10), utc(22, 10))
        self.assertEqual(panel.status, "not_ready")
        self.assertIn("650", panel.explanation)
        self.assertIn("1.000", panel.explanation.replace(",", "."))
        order = self.env["sale.order"].with_user(self.salesman).create({
            "partner_id": self.customer.id, "boss_direction": "import", "boss_transport_mode": "air",
            "boss_load_type": "air", "boss_port_id": self.mad.id, "boss_awb_kg": 500,
            "boss_planned_date": date(2026, 10, 12), "boss_storage_days": 10})
        self.env["boss.add.services"].with_user(self.salesman).create(
            {"order_id": order.id, "product_ids": [Command.set(self.alm.ids)]}).action_add()
        line = order.order_line
        self.assertEqual((line.boss_cost_status, line.boss_cost_kind), ("not_ready", "unknown"))
        line.write({"boss_manual_cost": 650.0, "boss_manual_cost_note": "Factura del handler (ficticia)"})
        self.assertEqual(line.boss_cost_kind, "known")
        # an estimate of 4 days: both readings give 4 x 5 x 10 = 200 -> priced, as an estimate
        order.boss_storage_days = 4
        self.assertEqual((line.boss_cost_status, line.boss_cost_amount, line.boss_cost_is_estimate), ("ok", 200.0, True))
