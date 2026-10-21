"""Quotation pricing end to end on a throw-away database. FICTITIOUS amounts and partners only."""
import base64
from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged

DOC = base64.b64encode(b"%PDF-1.4 fictitious supplier tariff").decode()


@tagged("post_install", "-at_install")
class TestQuotationPricing(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.salesman = new_test_user(cls.env, "boss_sales", groups="sales_team.group_sale_salesman,"
                                     "boss_pricing.group_tariff_user")
        cls.approver = new_test_user(cls.env, "boss_approver", groups="sales_team.group_sale_manager,"
                                     "boss_pricing.group_tariff_approver")
        Partner = cls.env["res.partner"]
        cls.carrier_a = Partner.create({"name": "NAVIERA A (FICTICIA)"})
        cls.carrier_b = Partner.create({"name": "NAVIERA B (FICTICIA)"})
        cls.customer = Partner.create({"name": "CLIENTE PRUEBA (FICTICIO)"})
        cls.eur = cls.env.company.currency_id  # company currency (USD on a new database)
        cls.thc = ref("boss_services.service_thc").product_variant_id
        cls.c20, cls.c40 = ref("boss_services.uom_c20"), ref("boss_services.uom_c40")
        cls.tariff = cls._tariff(cls.carrier_a, {cls.c20: 180.0, cls.c40: 240.0})
        cls.tariff.action_submit()
        cls.tariff.with_user(cls.approver).action_approve()

    @classmethod
    def _tariff(cls, carrier, prices, **vals):
        return cls.env["boss.tariff"].create({
            "name": f"{carrier.name} THC import", "partner_id": carrier.id, "carrier_id": carrier.id,
            "currency_id": cls.eur.id, "valid_from": date(2026, 1, 1), "direction": "import",
            "transport_mode": "sea", "load_type": "fcl", "document": DOC, "document_reference": "Doc 2026",
            "line_ids": [Command.create({"product_id": cls.thc.id, "uom_id": uom.id, "unit_price": price,
                                         "document_page": "4"}) for uom, price in prices.items()],
            **vals,
        })

    def _order(self, carrier=None, **vals):
        order = self.env["sale.order"].with_user(self.salesman).create({
            "partner_id": self.customer.id, "boss_direction": "import", "boss_transport_mode": "sea",
            "boss_load_type": "fcl", "boss_carrier_id": (carrier or self.carrier_a).id,
            "boss_planned_date": date(2026, 11, 2),
            "boss_container_ids": [Command.create({"size": "20", "quantity": 2}),
                                   Command.create({"size": "40", "quantity": 1})],
            **vals,
        })
        wizard = self.env["boss.add.services"].with_user(self.salesman).create(
            {"order_id": order.id, "product_ids": [Command.set(self.thc.ids)]})
        wizard.action_add()
        return order

    def _line(self, order, uom):
        return order.order_line.filtered(lambda l: l.product_uom_id == uom)

    def test_thc_quotation_cost_from_approved_tariff(self):
        order = self._order()
        l20, l40 = self._line(order, self.c20), self._line(order, self.c40)
        self.assertEqual((l20.product_uom_qty, l20.boss_cost_status, l20.boss_cost_amount), (2, "ok", 360.0))
        self.assertEqual((l40.product_uom_qty, l40.boss_cost_amount, l40.purchase_price), (1, 240.0, 240.0))
        self.assertIn(self.tariff.name, l40.boss_cost_explanation)
        # No sale price yet: zero is "missing", never "free".
        self.assertEqual(l40.boss_sale_status, "missing")
        self.assertTrue(order.boss_pricing_alert)
        l40.price_unit = 300.0
        self.assertEqual(l40.boss_sale_status, "manual")
        self.assertAlmostEqual(l40.boss_markup, 0.25)

    def test_missing_price_is_added_approved_and_used(self):
        order = self._order(carrier=self.carrier_b)
        line = self._line(order, self.c40)
        self.assertEqual(line.boss_cost_status, "no_tariff")
        wizard = self.env["boss.supplier.price.wizard"].with_user(self.salesman).create({
            "sale_line_id": line.id, "unit_price": 250.0, "document": DOC, "document_name": "b.pdf"})
        self.assertEqual((wizard.partner_id, wizard.direction, wizard.load_type), (self.carrier_b, "import", "fcl"))
        wizard.action_save()
        self.assertEqual(line.boss_cost_status, "pending_approval")
        tariff = line.boss_cost_candidate_ids.tariff_id
        with self.assertRaises(UserError):
            tariff.with_user(self.salesman).action_approve()
        tariff.with_user(self.approver).action_approve()
        self.assertEqual((line.boss_cost_status, line.boss_cost_amount), ("ok", 250.0))

    def test_missing_input_and_other_currency(self):
        order = self._order(boss_carrier_id=False)
        self.assertEqual(self._line(order, self.c40).boss_cost_status, "missing_input")
        other = self.env.ref("base.EUR") if self.eur != self.env.ref("base.EUR") else self.env.ref("base.USD")
        other.active = True
        usd_tariff = self._tariff(self.carrier_b, {self.c40: 260.0}, currency_id=other.id)
        usd_tariff.action_submit()
        usd_tariff.with_user(self.approver).action_approve()
        line = self._line(self._order(carrier=self.carrier_b), self.c40)
        self.assertEqual((line.boss_cost_status, line.purchase_price), ("currency", 0.0))

    def test_accepted_quotation_is_frozen_until_repriced(self):
        order = self._order()
        line = self._line(order, self.c40)
        line.price_unit = 300.0
        order.action_confirm()
        snapshot = order.boss_snapshot_ids
        self.assertEqual(snapshot.kind, "acceptance")
        accepted = {v["uom"]: v for v in snapshot.data["lines"]}
        self.assertEqual(accepted[self.c40.name]["tariff_id"], self.tariff.id, snapshot.data)
        # A newer approved version does not touch the accepted line, nor can a user edit it.
        new = self.env["boss.tariff"].browse(self.tariff.action_new_version()["res_id"])
        new.line_ids.filtered(lambda l: l.uom_id == self.c40).unit_price = 270.0
        new.write({"valid_from": date(2026, 10, 1), "document": DOC})
        new.action_submit()
        new.with_user(self.approver).action_approve()
        order.action_boss_update_costs()
        self.assertEqual((line.boss_cost_amount, line.price_unit), (240.0, 300.0))
        with self.assertRaises(UserError):
            line.with_user(self.salesman).price_unit = 310.0
        # Re-pricing is explicit and recorded.
        wizard = self.env["boss.reprice.wizard"].with_user(self.approver).create(
            {"order_id": order.id, "reason": "Naviera actualiza THC (prueba)"})
        wizard.line_ids.filtered(lambda wl: wl.sale_line_id == line).new_price = 330.0
        wizard.action_apply()
        self.assertEqual((line.boss_cost_amount, line.price_unit), (270.0, 330.0))
        self.assertEqual(order.boss_snapshot_ids[0].kind, "repricing")
