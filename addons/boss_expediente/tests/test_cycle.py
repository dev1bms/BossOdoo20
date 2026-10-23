"""Opportunity -> quotation -> file -> purchase -> invoices -> profitability on a throw-away database.
FICTITIOUS partners, prices and taxes only."""
import base64
from datetime import date

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged

DOC = base64.b64encode(b"%PDF-1.4 fictitious supplier tariff").decode()


class CycleCommon(TransactionCase):
    """Fictitious users, partners, tariffs and taxes shared by the file tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.sales = new_test_user(cls.env, "boss_cycle_sales", groups="sales_team.group_sale_salesman,"
                                  "boss_pricing.group_tariff_user,purchase.group_purchase_user")
        cls.manager = new_test_user(cls.env, "boss_cycle_manager", groups="sales_team.group_sale_manager,"
                                    "boss_pricing.group_tariff_approver,purchase.group_purchase_manager")
        cls.accountant = new_test_user(cls.env, "boss_cycle_accountant",
                                       groups="account.group_account_invoice,purchase.group_purchase_user")
        cls.env.company.boss_fx_policy = "rate_quotation"
        # a supplier currency other than the company's (the template company may be in EUR or USD)
        cls.foreign = ref("base.EUR") if cls.env.company.currency_id == ref("base.USD") else ref("base.USD")
        cls.foreign.active = True
        cls.env["res.currency.rate"].create({"currency_id": cls.foreign.id, "name": date(2026, 1, 1), "rate": 1.25,
                                             "company_id": cls.env.company.id})
        Partner = cls.env["res.partner"]
        cls.carrier = Partner.create({"name": "NAVIERA CICLO (FICTICIA)", "boss_is_supplier": True})
        cls.broker = Partner.create({"name": "AGENTE ADUANAS (FICTICIO)", "boss_is_supplier": True})
        cls.customer = Partner.create({
            "name": "CLIENTE CICLO (FICTICIO)", "boss_is_customer": True,
            "country_id": ref("base.es").id, "street": "Calle Ficticia 1", "city": "Valencia", "zip": "46001",
            "vat": "ESA00000000", "email": "cliente@example.com"})
        cls.thc = ref("boss_services.service_thc").product_variant_id
        cls.fad = ref("boss_services.service_fad").product_variant_id
        cls.alm = ref("boss_services.service_alm").product_variant_id
        cls.csm = ref("boss_services.service_csm").product_variant_id
        cls.hc = ref("boss_pricing.container_type_hc")
        cls._tariff(cls.carrier, cls.thc, {"container_size": "40", "basis": "containers", "unit_price": 240.0},
                    carrier_id=cls.carrier.id)
        cls._tariff(cls.broker, cls.fad, {"unit_price": 50.0}, currency_id=cls.foreign.id)
        Tax = cls.env["account.tax"]
        sale_tax = Tax.create({"name": "TEST VENTA 21", "amount": 21.0, "type_tax_use": "sale"})
        cls.env["boss.vat.tax"].create([{"vat_class": vat_class, "tax_id": sale_tax.id}
                                        for vat_class in ("NR", "EX", "NS")])
        cls.purchase_tax = Tax.create({"name": "TEST COMPRA 21", "amount": 21.0, "type_tax_use": "purchase"})

    @classmethod
    def _tariff(cls, supplier, product, line, **vals):
        tariff = cls.env["boss.tariff"].create({
            "name": f"{supplier.name} {product.default_code}", "partner_id": supplier.id,
            "currency_id": cls.env.company.currency_id.id, "valid_from": date(2026, 1, 1), "direction": "import",
            "transport_mode": "sea", "load_type": "fcl", "document": DOC, "document_reference": "Doc 2026",
            "scope_confirmed": True,
            "line_ids": [Command.create({"product_id": product.id, "uom_id": product.uom_id.id, **line})],
            **vals,
        })
        tariff.action_submit()
        tariff.with_user(cls.manager).action_approve()
        return tariff

    def _order(self, products, **vals):
        order = self.env["sale.order"].with_user(self.sales).create({
            "partner_id": self.customer.id, "boss_direction": "import", "boss_transport_mode": "sea",
            "boss_load_type": "fcl", "boss_carrier_id": self.carrier.id,
            "boss_port_id": self.env.ref("boss_pricing.port_esvlc").id, "boss_country_id": self.env.ref("base.cn").id,
            "boss_planned_date": date(2026, 11, 2), "boss_storage_days": 0,
            "boss_container_ids": [Command.create({"size": "40", "container_type_id": self.hc.id, "quantity": 1})],
            **vals,
        })
        self.env["boss.add.services"].with_user(self.sales).create(
            {"order_id": order.id, "product_ids": [Command.set(products.ids)]}).action_add()
        return order

    def _line(self, order, product):
        return order.order_line.filtered(lambda l: l.product_id == product)[:1]


@tagged("post_install", "-at_install")
class TestShipmentCycle(CycleCommon):
    def test_opportunity_to_quotation_and_repeat(self):
        lead = self.env["crm.lead"].with_user(self.sales).create({
            "name": "Importación China (prueba)", "type": "opportunity", "partner_id": self.customer.id,
            "boss_direction": "import", "boss_transport_mode": "sea", "boss_load_type": "fcl",
            "boss_port_id": self.env.ref("boss_pricing.port_esvlc").id, "boss_country_id": self.env.ref("base.cn").id,
            "boss_origin_place": "Ningbo", "boss_scope_destination_customs": True,
            "boss_service_ids": [Command.set((self.thc | self.fad).ids)],
            "boss_container_ids": [Command.create({"size": "40", "container_type_id": self.hc.id, "quantity": 2})],
        })
        context = lead._prepare_opportunity_quotation_context()
        order = self.env["sale.order"].with_user(self.sales).with_context(**context).create(
            {"partner_id": self.customer.id})
        self.assertEqual((order.boss_direction, order.boss_origin_place, order.boss_scope_destination_customs,
                          order.opportunity_id), ("import", "Ningbo", True, lead))
        self.assertEqual(sum(order.boss_container_ids.mapped("quantity")), 2)
        self.assertEqual(lead.boss_container_ids.quantity, 2, "the opportunity keeps its own request")
        wizard = self.env["boss.add.services"].with_user(self.sales).with_context(default_order_id=order.id).create({})
        self.assertEqual(wizard.product_ids, self.thc | self.fad, "requested services are proposed")
        # Repeat shipment: same route and services, prices looked up again, nothing accepted is copied.
        source = self._order(self.thc)
        self._line(source, self.thc).price_unit = 300.0
        source.with_user(self.sales).action_confirm()
        repeat = source.copy()
        line = self._line(repeat, self.thc)
        self.assertEqual((repeat.boss_pricing_frozen, repeat.boss_expediente_id.id, len(repeat.boss_snapshot_ids)),
                         (False, False, 0))
        self.assertEqual((line.boss_price_frozen, line.boss_cost_amount, line.boss_tariff_line_id.partner_id),
                         (False, 240.0, self.carrier))

    def test_unknown_cost_blocks_acceptance(self):
        order = self._order(self.thc | self.alm)
        order.order_line.write({"price_unit": 100.0})
        self.assertEqual(self._line(order, self.alm).boss_cost_kind, "unknown")
        with self.assertRaises(UserError):
            order.with_user(self.sales).action_confirm()
        with self.assertRaises(UserError):  # only a sales manager records the exception
            self._line(order, self.alm).with_user(self.sales).boss_unknown_cost_reason = "Almacén a confirmar"
        self._line(order, self.alm).with_user(self.manager).boss_unknown_cost_reason = "Almacén a confirmar"
        order.with_user(self.sales).action_confirm()
        need = order.boss_expediente_id.cost_ids.filtered(lambda n: n.product_id == self.alm)
        self.assertTrue(need.cost_unknown)
        self.assertFalse(order.boss_expediente_id.cost_complete)

    def test_full_cycle(self):
        order = self._order(self.thc | self.fad | self.csm)
        for product, price in ((self.thc, 300.0), (self.fad, 80.0), (self.csm, 90.0)):
            self._line(order, product).price_unit = price
        self.assertEqual(self._line(order, self.csm).boss_execution, "boss")
        self.assertEqual(self._line(order, self.fad).boss_cost_currency_id, self.foreign)
        order.with_user(self.sales).action_confirm()

        # one file, opened once, with an analytic account and a purchase need per bought service
        file = order.boss_expediente_id.with_env(self.env)  # figures read as administrator
        self.assertTrue(file.name.startswith("E"))
        order._boss_open_files()
        self.assertEqual(len(self.env["boss.expediente"].search([("sale_order_ids", "in", order.ids)])), 1)
        self.assertEqual(file.cost_ids.product_id, self.thc | self.fad, "BOSS services are not bought")
        self.assertEqual(len(file.container_ids), 1)
        key = str(file.analytic_account_id.id)
        self.assertTrue(all(key in (l.analytic_distribution or {}) for l in order.order_line))
        thc_need = file.cost_ids.filtered(lambda n: n.product_id == self.thc)
        fad_need = file.cost_ids.filtered(lambda n: n.product_id == self.fad)
        self.assertEqual((thc_need.partner_id, thc_need.expected_unit_cost, thc_need.currency_id),
                         (self.carrier, 240.0, self.env.company.currency_id))
        self.assertEqual((fad_need.partner_id, fad_need.expected_unit_cost, fad_need.currency_id),
                         (self.broker, 50.0, self.foreign))
        snapshot = order.boss_snapshot_ids.data["lines"]
        self.assertEqual({v["service"]: v["execution"] for v in snapshot}, {"THC": "supplier", "FAD": "supplier",
                                                                           "CSM": "boss"})

        # RFQs: one per supplier and currency, never twice
        file.with_user(self.sales).action_create_rfqs()
        self.assertEqual(len(file.purchase_order_ids), 2)
        with self.assertRaises(UserError):
            file.with_user(self.sales).action_create_rfqs()
        self.assertEqual(len(file.purchase_order_ids.order_line), 2)
        carrier_po = file.purchase_order_ids.filtered(lambda p: p.partner_id == self.carrier)
        broker_po = file.purchase_order_ids - carrier_po
        self.assertEqual(broker_po.currency_id, self.foreign)
        po_line = carrier_po.order_line
        self.assertEqual((po_line.price_unit, po_line.sale_line_id), (240.0, self._line(order, self.thc)))
        po_line.product_qty = 2  # the BOSS price is kept (no supplier info, no product cost)
        self.assertEqual(po_line.price_unit, 240.0)
        po_line.product_qty = 1
        self.assertEqual(thc_need.state, "rfq")
        (carrier_po | broker_po).with_user(self.manager).button_confirm()
        thc_need.with_user(self.sales).action_mark_performed()
        self.assertEqual(thc_need.state, "performed")

        # vendor bill: tax of the supplier invoice required; waits until the service is invoiced to the customer
        carrier_po.with_user(self.accountant).action_create_invoice()
        bill = carrier_po.invoice_ids
        bill.invoice_date = fields.Date.today()
        with self.assertRaises(UserError):
            bill.with_user(self.accountant).action_post()
        bill.invoice_line_ids.tax_ids = self.purchase_tax
        # Cristina's requirement (customer invoiced first) is a pending decision: a warning by default, a block only
        # when the company chooses it.
        self.assertIn("not invoiced to the customer yet", bill.boss_bill_warning)
        self.env.company.boss_bill_before_invoice = "block"
        with self.assertRaises(UserError):
            bill.with_user(self.accountant).action_post()

        # customer invoice of the THC only (milestone), then the rest
        thc_part = file.allocation_ids.filtered(lambda a: a.product_id == self.thc)
        wizard = self.env["boss.invoice.services"].with_user(self.sales).create({
            "expediente_id": file.id, "allocation_ids": [Command.set(thc_part.ids)]})
        invoice = self.env["account.move"].browse(wizard.action_create()["res_id"])
        self.assertEqual(invoice.invoice_line_ids.product_id, self.thc)
        self.assertIn(key, invoice.invoice_line_ids.analytic_distribution)
        invoice.with_user(self.accountant).action_post()
        bill.with_user(self.accountant).action_post()
        self.assertEqual(thc_need.state, "billed")
        file.invalidate_recordset()
        self.assertEqual((file.amount_invoiced, file.amount_cost_actual), (300.0, 240.0))
        self.assertEqual(file.amount_sale, 470.0)
        # FAD: 50 in the supplier currency at 1.25 = 40 EUR still expected; margin after external costs = 470 - 240 - 40
        self.assertAlmostEqual(file.amount_cost_pending, 40.0)
        self.assertAlmostEqual(file.amount_margin_forecast, 190.0)
        self.assertFalse(file.cost_complete)

        rest = self.env["boss.invoice.services"].with_user(self.sales).with_context(
            default_expediente_id=file.id).create({})
        self.assertEqual(rest.allocation_ids.sale_line_id, order.order_line - self._line(order, self.thc))
        second = self.env["account.move"].browse(rest.action_create()["res_id"])
        second.with_user(self.accountant).action_post()
        file.invalidate_recordset()
        self.assertAlmostEqual(file.amount_invoiced, 470.0)

        # customer credit note of the first invoice: the THC is to invoice again
        credit = invoice._reverse_moves(cancel=False)
        credit.with_user(self.accountant).action_post()
        file.invalidate_recordset()
        self.assertAlmostEqual(file.amount_invoiced, 170.0)
        self.assertEqual(self._line(order, self.thc).qty_to_invoice, 1.0)

        # extra cost after acceptance, re-invoiced through the sales manager with a reason
        with self.assertRaises(UserError):
            self.env["sale.order.line"].with_user(self.sales).create(
                {"order_id": order.id, "product_id": self.alm.id, "price_unit": 50.0})
        extra = self.env["boss.expediente.cost"].with_user(self.sales).create({
            "expediente_id": file.id, "product_id": self.alm.id, "uom_id": self.alm.uom_id.id, "quantity": 1,
            "partner_id": self.carrier.id, "expected_unit_cost": 100.0, "extra_class": "approval",
            "reason": "Almacenaje adicional (prueba)"})
        rebill = self.env["boss.rebill.wizard"].with_user(self.manager).with_context(
            default_cost_id=extra.id).create({"price_unit": 150.0, "reason": "Cliente pide 4 días más (prueba)"})
        rebill.action_apply()
        new_line = extra.rebill_line_id
        self.assertEqual((new_line.price_unit, new_line.boss_price_frozen, extra.extra_class), (150.0, True, "rebill"))
        self.assertEqual(order.boss_snapshot_ids[0].kind, "addition")
        self.assertEqual(len(file.cost_ids), 3, "the re-invoiced line does not open a second need")
        file.with_user(self.sales).action_create_rfqs()
        self.assertEqual(extra.purchase_line_ids.order_id.state, "draft")
        file.invalidate_recordset()
        self.assertAlmostEqual(file.amount_sale, 620.0)
        # margin at acceptance: accepted sale 470 - accepted cost (240 + 40); the re-invoiced 150 came later
        self.assertAlmostEqual(file.amount_margin_accepted, 190.0)
        self.assertIn("RFQ", file.completeness)

    def test_contact_switches_and_invoice_data(self):
        partner = self.env["res.partner"].with_user(self.sales).create({"name": "NUEVO CLIENTE (FICTICIO)",
                                                                         "boss_is_customer": True})
        self.assertEqual(partner.customer_rank, 1)
        self.assertIn(partner, self.env["res.partner"].search([("boss_is_customer", "=", True)]))
        self.assertIn("tax ID", partner.boss_missing_data)
