"""Quotation pricing end to end on a throw-away database. FICTITIOUS amounts and partners only."""
import base64
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError
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
        cls.customer = Partner.create({"name": "CLIENTE PRUEBA (FICTICIO)", "country_id": ref("base.es").id})
        cls.cur = cls.env.company.currency_id
        cls.thc = ref("boss_services.service_thc").product_variant_id
        cls.dv, cls.hc = ref("boss_pricing.container_type_dv"), ref("boss_pricing.container_type_hc")
        cls.tariff = cls._approved(cls._tariff(cls.carrier_a, [("20", 180.0), ("40", 240.0)]))
        # Fictitious taxes standing for the VAT mapping Ángel will choose (B02).
        Tax = cls.env["account.tax"]
        cls.taxes = {k: Tax.create({"name": f"TEST {k}", "amount": rate, "type_tax_use": "sale"})
                     for k, rate in (("nr", 21.0), ("ex", 0.0), ("ns", 0.0))}

    @classmethod
    def _tariff(cls, carrier, prices, product=None, **vals):
        product = product or cls.thc
        return cls.env["boss.tariff"].create({
            "name": f"{carrier.name} {product.default_code}", "partner_id": carrier.id, "carrier_id": carrier.id,
            "currency_id": cls.cur.id, "valid_from": date(2026, 1, 1), "direction": "import",
            "transport_mode": "sea", "load_type": "fcl", "document": DOC, "document_reference": "Doc 2026",
            "line_ids": [Command.create({"product_id": product.id, "uom_id": product.uom_id.id,
                                         "container_size": size, "basis": "containers", "unit_price": price,
                                         "document_page": "4"}) for size, price in prices],
            **vals,
        })

    @classmethod
    def _approved(cls, tariff):
        tariff.action_submit()
        tariff.with_user(cls.approver).action_approve()
        return tariff

    def _map_vat(self):
        self.env.company.write({f"boss_tax_{k}_id": tax.id for k, tax in self.taxes.items()})

    def _order(self, carrier=None, services=None, **vals):
        order = self.env["sale.order"].with_user(self.salesman).create({
            "partner_id": self.customer.id, "boss_direction": "import", "boss_transport_mode": "sea",
            "boss_load_type": "fcl", "boss_carrier_id": (carrier or self.carrier_a).id,
            "boss_port_id": self.env.ref("boss_pricing.port_esvlc").id, "boss_country_id": self.env.ref("base.cn").id,
            "boss_planned_date": date(2026, 11, 2),
            "boss_container_ids": [Command.create({"size": "20", "container_type_id": self.dv.id, "quantity": 2}),
                                   Command.create({"size": "40", "container_type_id": self.hc.id, "quantity": 1})],
            **vals,
        })
        self.env["boss.add.services"].with_user(self.salesman).create(
            {"order_id": order.id, "product_ids": [Command.set((services or self.thc).ids)]}).action_add()
        return order

    def _line(self, order, size, product=None):
        return order.order_line.filtered(
            lambda l: l.boss_container_size == size and l.product_id == (product or self.thc))

    def test_thc_lines_per_container_group_with_cost_and_explanation(self):
        order = self._order()
        l20, l40 = self._line(order, "20"), self._line(order, "40")
        self.assertEqual((l20.product_uom_qty, l20.boss_cost_status, l20.boss_cost_amount), (2, "ok", 360.0))
        self.assertEqual((l40.product_uom_qty, l40.boss_container_type_id, l40.purchase_price), (1, self.hc, 240.0))
        self.assertIn(self.tariff.name, l40.boss_cost_explanation)
        # No sale price yet: zero is "missing", never "free"; VAT class from the rules, tax not mapped yet.
        self.assertEqual((l40.boss_sale_status, l40.boss_vat_class, l40.boss_vat_status), ("missing", "EX", "pending"))
        self.assertTrue(order.boss_pricing_alert)
        l40.price_unit = 300.0
        self.assertEqual(l40.boss_sale_status, "manual")
        self.assertAlmostEqual(l40.boss_markup, 0.25)

    def test_missing_price_is_added_approved_and_used(self):
        order = self._order(carrier=self.carrier_b)
        line = self._line(order, "40")
        self.assertEqual(line.boss_cost_status, "no_tariff")
        wizard = self.env["boss.supplier.price.wizard"].with_user(self.salesman).create({
            "sale_line_id": line.id, "unit_price": 250.0, "document": DOC, "document_name": "b.pdf"})
        self.assertEqual((wizard.partner_id, wizard.direction, wizard.container_size), (self.carrier_b, "import", "40"))
        wizard.action_save()
        self.assertEqual(line.boss_cost_status, "pending_approval")
        tariff = line.boss_cost_candidate_ids.tariff_id
        with self.assertRaises(UserError):
            tariff.with_user(self.salesman).action_approve()
        tariff.with_user(self.approver).action_approve()
        self.assertEqual((line.boss_cost_status, line.boss_cost_amount), ("ok", 250.0))
        self.assertEqual(self._line(order, "20").boss_cost_status, "no_tariff")  # only the 40' price was added

    def test_tariff_approval_cannot_be_bypassed(self):
        Tariff = self.env["boss.tariff"].with_user(self.salesman)
        with self.assertRaises(UserError):
            Tariff.create({"name": "X", "partner_id": self.carrier_a.id, "state": "approved"})
        draft = self._tariff(self.carrier_b, [("40", 1.0)]).with_user(self.salesman)
        with self.assertRaises(UserError):
            draft.write({"state": "approved"})
        with self.assertRaises(AccessError):  # prices of a submitted tariff are locked by ir.access
            self.tariff.line_ids[0].with_user(self.salesman).unit_price = 1.0
        with self.assertRaises(UserError):
            self.tariff.with_user(self.approver).valid_from = date(2026, 2, 1)

    def test_missing_input_other_currency_and_vat_rules(self):
        order = self._order(boss_carrier_id=False)
        self.assertEqual(self._line(order, "40").boss_cost_status, "missing_input")
        other = self.env.ref("base.EUR") if self.cur != self.env.ref("base.EUR") else self.env.ref("base.USD")
        other.active = True
        self._approved(self._tariff(self.carrier_b, [("40", 260.0)], currency_id=other.id))
        line = self._line(self._order(carrier=self.carrier_b), "40")
        self.assertEqual((line.boss_cost_status, line.purchase_price), ("currency", 0.0))
        # VAT: an NR service imported from a third country for a Spanish customer stays NR.
        self._map_vat()
        bl = self._order(services=self.env.ref("boss_services.service_bl").product_variant_id).order_line
        self.assertEqual((bl.boss_vat_class, bl.boss_vat_status, bl.tax_ids), ("NR", "ok", self.taxes["nr"]))

    def test_time_estimate(self):
        dem = self.env.ref("boss_services.service_dem").product_variant_id
        tariff = self.env["boss.tariff"].create({
            "name": "DEM test", "partner_id": self.carrier_a.id, "carrier_id": self.carrier_a.id,
            "currency_id": self.cur.id, "valid_from": date(2026, 1, 1), "document": DOC,
            "line_ids": [Command.create({
                "product_id": dem.id, "uom_id": dem.uom_id.id, "method": "time", "basis": "containers",
                "free_days": 4, "free_mode": "deduct",
                "bracket_ids": [Command.create({"up_to": 7, "unit_price": 10}),
                                Command.create({"up_to": 0, "unit_price": 20})]})]})
        self._approved(tariff)
        line = self._line(self._order(services=dem, boss_storage_days=9), "20", dem)
        # days 5..9 charged: 3 x 10 + 2 x 20 = 70 per container, 2 containers of 20'
        self.assertEqual((line.boss_cost_amount, line.boss_cost_is_estimate), (140.0, True))
        self.assertIn("9", line.boss_cost_explanation)

    def test_accepted_quotation_is_frozen_until_repriced(self):
        order = self._order()
        order.order_line.write({"price_unit": 300.0})
        with self.assertRaises(UserError):  # VAT treatment undecided: not ready to accept
            order.action_confirm()
        self._map_vat()
        self.env.add_to_compute(order.order_line._fields["boss_vat_status"], order.order_line)
        order.order_line._recompute_recordset(["boss_vat_status", "tax_ids"])
        order.action_confirm()
        line = self._line(order, "40")
        accepted = {v["container_size"]: v for v in order.boss_snapshot_ids.data["lines"]}
        self.assertEqual((accepted["40"]["tariff_id"], accepted["40"]["vat_class"]), (self.tariff.id, "EX"),
                         order.boss_snapshot_ids.data)
        new = self.env["boss.tariff"].browse(self.tariff.action_new_version()["res_id"])
        new.line_ids.filtered(lambda l: l.container_size == "40").unit_price = 270.0
        new.write({"valid_from": date(2026, 10, 1), "document": DOC})
        self._approved(new)
        order.action_boss_update_costs()
        self.assertEqual((line.boss_cost_amount, line.price_unit), (240.0, 300.0))
        with self.assertRaises(UserError):  # the context flag alone does not unlock an accepted line
            line.with_user(self.salesman).with_context(boss_reprice=True).price_unit = 310.0
        wizard = self.env["boss.reprice.wizard"].with_user(self.approver).create(
            {"order_id": order.id, "reason": "Naviera actualiza THC (prueba)"})
        wizard.line_ids.filtered(lambda wl: wl.sale_line_id == line).new_price = 330.0
        wizard.action_apply()
        self.assertEqual((line.boss_cost_amount, line.price_unit), (270.0, 330.0))
        self.assertEqual(order.boss_snapshot_ids[0].kind, "repricing")
