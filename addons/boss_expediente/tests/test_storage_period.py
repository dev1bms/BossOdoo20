"""Airport storage (ALM) from the quotation estimate to the supplier bill, with the actual period on the file.
FICTITIOUS handler tariff: per 100 kg and 24 hours, 48 h free as a threshold, Friday with a Monday exit 72 h, Saturday
free until Monday included, 10 € up to 7 periods / 20 € more (reading not decided), minimum 50. 500 kg = 5 units.
Expected values computed by hand."""
from datetime import date, datetime

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .test_cycle import CycleCommon


def utc(day, hour, minute=0, month=10):
    """Odoo datetime (UTC) of a Madrid time in 2026: CEST (UTC+2) until Sunday 25 October, then CET (UTC+1)."""
    offset = 2 if (month, day) < (10, 25) or (month, day) == (10, 25) and hour < 3 else 1
    return datetime(2026, month, day, hour - offset, minute)


@tagged("post_install", "-at_install")
class TestStoragePeriod(CycleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = cls.env["res.partner"].create({"name": "HANDLER AEREO CICLO (FICTICIO)", "boss_is_supplier": True})
        cls.mad = cls.env.ref("boss_pricing.port_esmad_air")
        cls.tariff = cls._tariff(cls.handler, cls.alm, {
            "method": "time", "basis": "awb_kg", "unit_size": 100, "period_unit": "24h", "free_hours": 48,
            "free_mode": "threshold", "friday_monday_free": 72, "saturday_until_monday": True,
            "tier_mode": "undecided", "min_amount": 50,
            "bracket_ids": [Command.create({"up_to": 7, "unit_price": 10}), Command.create({"up_to": 0, "unit_price": 20})],
        }, transport_mode="air", load_type="air", port_ids=[Command.set(cls.mad.ids)])

    def test_estimate_actual_period_purchase_and_bill(self):
        # An operations user cannot decide a reading on an approved price, nor approve one.
        with self.assertRaises((AccessError, UserError)):
            self.tariff.line_ids.with_user(self.sales).write({"tier_mode": "positional"})
        with self.assertRaises(UserError):
            self.tariff.with_user(self.sales).action_approve()
        # Quotation: estimate of 3 days from the planned arrival (a Friday): the Friday exception is not assumed.
        order = self._order(self.alm, boss_transport_mode="air", boss_load_type="air", boss_port_id=self.mad.id,
                            boss_carrier_id=False, boss_container_ids=False, boss_awb_kg=500,
                            boss_planned_date=date(2026, 10, 16), boss_storage_days=3)
        line = self._line(order, self.alm)
        self.assertEqual((line.boss_cost_status, line.boss_cost_amount, line.boss_cost_is_estimate), ("ok", 150.0, True))
        self.assertIn("Friday", line.boss_cost_explanation)
        line.price_unit = 180.0
        order.with_user(self.sales).action_confirm()
        file = order.boss_expediente_id.with_env(self.env)
        need = file.cost_ids.filtered(lambda n: n.product_id == self.alm)
        accepted = order.boss_snapshot_ids.data["lines"]
        self.assertEqual((need.partner_id, need.quantity, need.expected_amount, need.days), (self.handler, 1.0, 150.0, 3))

        # The period ends before it starts: refused.
        with self.assertRaises(ValidationError):
            need.write({"period_start": utc(19, 8), "period_end": utc(16, 9)})
        # Actual period: NOA Friday 09:00 -> pickup Monday 08:00 (71 h): free with a Monday exit.
        need.write({"period_start": utc(16, 9), "period_end": utc(19, 8)})
        file.with_user(self.sales).action_recompute_costs()
        self.assertEqual((need.expected_amount, need.days), (0.0, 3))
        # Pickup at 10:00 instead (73 h): 4 periods from the NOA, 4 x 5 x 10.
        need.period_end = utc(19, 10)
        file.with_user(self.sales).action_recompute_costs()
        self.assertEqual((need.expected_amount, need.days), (200.0, 4))
        self.assertEqual(sorted(need.revision_ids.mapped("new_amount")), [0.0, 200.0])
        self.assertIn("19/10/2026 10:00", need.revision_ids.sorted("id")[-1].explanation)
        # The accepted sale and its snapshot never change.
        self.assertEqual((line.price_unit, order.boss_snapshot_ids.data["lines"]), (180.0, accepted))

        # Purchase: one RFQ line 1 x 200; recomputing again creates nothing.
        file.with_user(self.sales).action_create_rfqs()
        po_line = need.purchase_line_ids
        self.assertEqual((len(po_line), po_line.product_qty, po_line.price_unit), (1, 1.0, 200.0))
        file.with_user(self.sales).action_recompute_costs()
        self.assertEqual((len(need.revision_ids), len(file.purchase_order_ids.order_line)), (2, 1))
        po_line.order_id.with_user(self.manager).button_confirm()

        # The stay goes on to Thursday 22/10 10:00 (145 h = 7 periods: both tier readings 350): the order is flagged.
        need.period_end = utc(22, 10)
        file.with_user(self.sales).action_recompute_costs()
        file.invalidate_recordset()
        self.assertEqual((need.expected_amount, need.days, need.po_to_review), (350.0, 7, True))
        self.assertEqual(po_line.price_unit, 200.0, "a confirmed order is a commitment: unchanged")
        # Until Monday 26/10 10:00 (242 real hours with the change of time = 11 periods): the readings differ
        # (day by day 7 x 50 + 4 x 100 = 750; whole stay 11 x 100 = 1,100): not priced, the expected cost stays.
        need.period_end = utc(26, 10)
        file.with_user(self.sales).action_recompute_costs()
        revision = need.revision_ids.sorted("id")[-1]
        self.assertEqual((revision.status, revision.applied, need.expected_amount), ("not_ready", False, 350.0))
        self.assertIn("750", revision.explanation)
        file.with_user(self.sales).action_recompute_costs()
        self.assertEqual(need.revision_ids.sorted("id")[-1], revision, "the same result is not recorded twice")

        # Supplier bill of the order (200), then a credit note of 50: the actual cost is the bill net of the credit
        # note, never the order plus its bill.
        need.with_user(self.sales).action_mark_performed()
        po_line.order_id.with_user(self.accountant).action_create_invoice()
        bill = po_line.order_id.invoice_ids
        bill.write({"invoice_date": fields.Date.today()})
        bill.invoice_line_ids.tax_ids = self.purchase_tax
        need.invalidate_recordset()
        # a draft bill is not a cost yet: the service is not billed and its cost is still expected
        self.assertEqual((need.state, need.billed_amount_company, need.pending_amount_company), ("performed", 0.0, 350.0))
        bill.with_user(self.accountant).action_post()
        need.invalidate_recordset()
        self.assertEqual((need.state, need.billed_amount_company, need.pending_amount_company), ("billed", 200.0, 0.0))
        credit = bill._reverse_moves(default_values_list=[{"invoice_date": fields.Date.today()}], cancel=False)
        credit.invoice_line_ids.price_unit = 50.0
        credit.with_user(self.accountant).action_post()
        file.invalidate_recordset()
        need.invalidate_recordset()
        self.assertEqual((need.state, need.billed_amount_company, file.amount_cost_actual), ("billed", 150.0, 150.0))
        # billed 150 against the forecast 350 (expected after the order, never below it): -200 to review
        self.assertEqual((need.pending_amount_company, need.variance_company), (0.0, -200.0))
        self.assertEqual(file.amount_cost_forecast, 150.0)
