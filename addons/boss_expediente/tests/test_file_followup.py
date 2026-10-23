"""Follow-up of an accepted shipment: cost recomputed from the file data, services added after acceptance, agreement
for several shipments, partial / cancelled / replaced purchases, purchase basis and who sees which figure.
FICTITIOUS partners, prices and taxes only."""
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import new_test_user, tagged

from odoo.addons.boss_pricing_sale.models import vat_rules

from .test_cycle import CycleCommon


@tagged("post_install", "-at_install")
class TestFileFollowUp(CycleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["res.partner"].create({"name": "ALMACEN (FICTICIO)", "boss_is_supplier": True})
        # storage: 2 free days, then 25 per day (per shipment)
        cls._tariff(cls.warehouse, cls.alm, {"method": "time", "free_days": 2, "free_mode": "deduct",
                                             "bracket_ids": [Command.create({"up_to": 0, "unit_price": 25.0})]})

    def _accepted(self, products, prices, **vals):
        order = self._order(products, **vals)
        for product, price in prices.items():
            self._line(order, product).price_unit = price
        order.with_user(self.sales).action_confirm()
        return order, order.boss_expediente_id.with_env(self.env)

    def _need(self, file, product):
        return file.cost_ids.filtered(lambda n: n.product_id == product)

    def test_storage_days_and_containers_change_the_expected_cost(self):
        order, file = self._accepted(self.thc | self.alm, {self.thc: 300.0, self.alm: 120.0}, boss_storage_days=5)
        alm, thc = self._need(file, self.alm), self._need(file, self.thc)
        accepted = order.boss_snapshot_ids.data["lines"]
        self.assertEqual((alm.days, alm.expected_amount, thc.expected_amount), (5, 75.0, 240.0))  # (5-2) x 25

        # Storage ends after 9 days and a second 40'HC is loaded: recompute with the file data.
        alm.days = 9
        file.container_ids = [Command.create({"size": "40", "container_type_id": self.hc.id})]
        file.with_user(self.sales).action_recompute_costs()
        self.assertEqual((alm.expected_amount, thc.quantity, thc.expected_amount), (175.0, 2.0, 480.0))
        revisions = file.revision_ids
        self.assertEqual(sorted(revisions.mapped("new_amount")), [175.0, 480.0])
        self.assertEqual(sorted(revisions.mapped("old_amount")), [75.0, 240.0])
        self.assertIn("9", alm.revision_ids.explanation)
        # The accepted sale and its snapshot never change.
        self.assertEqual((self._line(order, self.alm).price_unit, self._line(order, self.alm).purchase_price),
                         (120.0, 75.0))
        self.assertEqual(order.boss_snapshot_ids.data["lines"], accepted)
        self.assertEqual(len(order.boss_snapshot_ids), 1)
        # Nothing changed: no new revision.
        file.action_recompute_costs()
        self.assertEqual(len(file.revision_ids), 2)

        # After the order to the warehouse is confirmed, a longer stay is still forecast and the order is flagged.
        file.with_user(self.sales).action_create_rfqs()
        self.assertEqual(sum(thc.purchase_line_ids.mapped("product_qty")), 2.0)
        alm.purchase_line_ids.order_id.with_user(self.manager).button_confirm()
        alm.days = 11
        file.action_recompute_costs()
        file.invalidate_recordset()
        self.assertEqual((alm.expected_amount, alm.pending_amount_company, alm.po_to_review), (225.0, 225.0, True))
        self.assertIn("purchase orders to review", file.with_user(self.manager).completeness)

    def test_services_added_after_acceptance(self):
        order, file = self._accepted(self.thc, {self.thc: 300.0})
        margin_before = file.amount_margin_accepted
        with self.assertRaises((AccessError, UserError)):  # sales managers only
            self.env["boss.add.service.wizard"].with_user(self.sales).create(
                {"order_id": order.id, "product_id": self.csm.id, "price_unit": 90.0, "reason": "x"}).action_apply()
        # A BOSS service: no supplier cost, nothing to buy.
        self.env["boss.add.service.wizard"].with_user(self.manager).create({
            "order_id": order.id, "product_id": self.csm.id, "price_unit": 90.0,
            "reason": "Cliente pide consignación (prueba)"}).action_apply()
        # A supplier service: bought from the broker at its tariff.
        self.env["boss.add.service.wizard"].with_user(self.manager).create({
            "order_id": order.id, "product_id": self.fad.id, "execution": "supplier", "supplier_id": self.broker.id,
            "price_unit": 80.0, "reason": "Despacho añadido (prueba)"}).action_apply()
        csm = self._line(order, self.csm)
        self.assertEqual((csm.boss_execution, csm.boss_added_after_acceptance, csm.boss_price_frozen),
                         ("boss", True, True))
        self.assertFalse(self._need(file, self.csm))
        self.assertEqual(self._need(file, self.fad).partner_id, self.broker)
        self.assertEqual(order.boss_snapshot_ids.mapped("kind"), ["addition", "addition", "acceptance"])
        self.assertEqual(len(order.boss_snapshot_ids[-1].data["lines"]), 1, "the accepted agreement is kept as it was")
        file.invalidate_recordset()
        self.assertEqual((file.amount_sale_added, file.amount_margin_accepted), (170.0, margin_before))

    def test_one_quotation_several_files(self):
        order, file = self._accepted(self.thc, {self.thc: 300.0}, boss_container_ids=[
            Command.create({"size": "40", "container_type_id": self.hc.id, "quantity": 2})])
        line = self._line(order, self.thc)
        split = self.env["boss.expediente.split"].with_user(self.sales).with_context(
            default_expediente_id=file.id).create({})
        split.line_ids.quantity = 1  # the second container travels on another vessel
        second = self.env["boss.expediente"].browse(split.action_split()["res_id"])
        self.assertFalse(self._need(second, self.thc).closed)
        self.assertNotEqual(second, file)
        self.assertEqual((file.allocation_ids.quantity, second.allocation_ids.quantity), (1.0, 1.0))
        self.assertEqual((self._need(file, self.thc).quantity, self._need(second, self.thc).quantity), (1.0, 1.0))
        self.assertEqual((order.boss_expediente_count, order in second.sale_order_ids), (2, True))
        self.assertEqual(line.analytic_distribution, {str(file.analytic_account_id.id): 50.0,
                                                      str(second.analytic_account_id.id): 50.0})
        with self.assertRaises(ValidationError):  # never more than accepted
            second.allocation_ids.quantity = 2
            second.allocation_ids.flush_recordset()
        # each file invoices its own part
        wizard = self.env["boss.invoice.services"].with_user(self.sales).with_context(
            default_expediente_id=second.id).create({})
        move = self.env["account.move"].browse(wizard.action_create()["res_id"])
        self.assertEqual((move.invoice_line_ids.quantity, move.invoice_line_ids.boss_expediente_id), (1.0, second))
        self.assertEqual(move.invoice_line_ids.analytic_distribution, {str(second.analytic_account_id.id): 100.0})
        (file | second).allocation_ids.invalidate_recordset()
        self.assertEqual((second.allocation_ids.to_invoice_quantity, file.allocation_ids.to_invoice_quantity),
                         (0.0, 1.0))
        (file | second).invalidate_recordset()
        self.assertEqual((file.amount_sale, second.amount_sale), (300.0, 300.0))
        self.assertEqual((file.amount_cost_accepted, second.amount_cost_accepted), (240.0, 240.0))
        # Moving everything that is left to a new file: the first file keeps no part and its service is closed.
        split = self.env["boss.expediente.split"].with_context(default_expediente_id=file.id).create({})
        split.line_ids.quantity = 1
        third = self.env["boss.expediente"].browse(split.action_split()["res_id"])
        self.assertEqual((len(file.allocation_ids), third.allocation_ids.quantity), (0, 1.0))
        self.assertEqual((self._need(file, self.thc).closed, self._need(third, self.thc).closed,
                          self._need(third, self.thc).quantity), (True, False, 1.0))
        self.assertEqual(line.analytic_distribution, {str(second.analytic_account_id.id): 50.0,
                                                      str(third.analytic_account_id.id): 50.0})

    def test_partial_purchase_cancel_replace_and_purchase_basis(self):
        carrier_b = self.env["res.partner"].create({"name": "NAVIERA B CICLO (FICTICIA)", "boss_is_supplier": True})
        self._tariff(carrier_b, self.thc, {"container_size": "40", "basis": "containers", "unit_price": 230.0})
        order, file = self._accepted(self.thc, {self.thc: 300.0}, boss_container_ids=[
            Command.create({"size": "40", "container_type_id": self.hc.id, "quantity": 2})])
        thc = self._need(file, self.thc)
        self.assertEqual((thc.quantity, thc.expected_unit_cost), (2.0, 240.0))
        # Partial: one container ordered now, the other later.
        file.action_create_rfqs()
        first = thc.purchase_line_ids
        first.product_qty = 1
        first.order_id.with_user(self.manager).button_confirm()
        second = file.action_create_rfqs()
        self.assertEqual(sum(thc.purchase_line_ids.filtered(lambda l: l.state != "cancel").mapped("product_qty")), 2)
        # The second order is cancelled: one container is to order again.
        self.env["purchase.order"].browse(second["res_id"]).button_cancel()
        self.assertEqual(thc._boss_remaining_qty(), 1.0)
        # Supplier replaced: not while an order is active; after cancelling it, the new supplier's tariff applies.
        with self.assertRaises(UserError):
            thc.partner_id = carrier_b
        first.order_id.button_cancel()
        thc.partner_id = carrier_b
        file.action_recompute_costs()
        self.assertEqual((thc.expected_unit_cost, thc.state), (230.0, "to_order"))
        file.action_create_rfqs()
        self.assertEqual(thc.purchase_line_ids.filtered(lambda l: l.state == "draft").order_id.partner_id, carrier_b)

        # Purchase basis different from the sale: sold per shipment, bought per chargeable kg.
        tte = self.env.ref("boss_services.service_tte_con").product_variant_id
        haulier = self.env["res.partner"].create({"name": "TRANSPORTES (FICTICIO)", "boss_is_supplier": True})
        self._tariff(haulier, tte, {"unit_price": 0.18})
        road = self._order(tte)
        line = self._line(road, tte)
        line.write({"product_uom_id": self.env.ref("boss_services.uom_shipment").id, "price_unit": 350.0})
        self.assertEqual(line.boss_cost_kind, "unknown")  # no supplier price per shipment
        line.with_user(self.manager).boss_unknown_cost_reason = "El transportista cobra por kg (prueba)"
        road.with_user(self.sales).action_confirm()
        need = self._need(road.boss_expediente_id, tte)
        need.write({"uom_id": tte.uom_id.id, "quantity": 1200, "partner_id": haulier.id})
        road.boss_expediente_id.action_recompute_costs()
        self.assertEqual((need.uom_id, need.expected_amount, need.cost_unknown), (tte.uom_id, 216.0, False))
        self.assertEqual((line.product_uom_id.name, line.product_uom_qty, line.price_unit), ("Shipment", 1.0, 350.0))

    def test_who_sees_which_figures(self):
        order, file = self._accepted(self.thc, {self.thc: 300.0})
        sales = new_test_user(self.env, "boss_cycle_sales_only", groups="sales_team.group_sale_salesman")
        file.user_id = sales
        other_sales = new_test_user(self.env, "boss_cycle_sales2", groups="sales_team.group_sale_salesman")
        buyer = new_test_user(self.env, "boss_cycle_buyer", groups="purchase.group_purchase_user")
        # Sales: sale side and the cost shown on the quotation; never vendor-side amounts.
        self.assertEqual(file.with_user(sales).amount_sale, 300.0)
        self.assertEqual(file.with_user(sales).amount_margin_accepted, 60.0)
        for fname in ("amount_cost_actual", "amount_cost_forecast", "amount_margin_forecast", "amount_paid",
                      "bill_ids", "profit_explanation"):
            with self.assertRaises(AccessError, msg=fname):
                file.with_user(sales).read([fname])
        with self.assertRaises(AccessError):
            self._need(file, self.thc).with_user(sales).read(["billed_amount_company"])
        self.assertNotIn("cost not billed", file.with_user(sales).completeness or "")
        # Another salesman does not see this file.
        with self.assertRaises(AccessError):
            file.with_user(other_sales).read(["name"])
        # Purchasing: vendor side, not the sale.
        self.assertEqual(file.with_user(buyer).amount_cost_forecast, 240.0)
        with self.assertRaises(AccessError):
            file.with_user(buyer).read(["amount_sale"])
        # Accounting: everything.
        self.assertEqual(file.with_user(self.accountant).amount_margin_forecast, 60.0)
        # Another company never sees the file.
        company_b = self.env["res.company"].create({"name": "OTRA EMPRESA (FICTICIA)"})
        stranger = new_test_user(self.env, "boss_cycle_other_company", groups="sales_team.group_sale_manager",
                                 company_id=company_b.id, company_ids=[Command.set(company_b.ids)])
        with self.assertRaises(AccessError):
            file.with_user(stranger).read(["name"])

    def test_posting_checks_and_costs_without_order(self):
        ara = self.env.ref("boss_services.service_ara").product_variant_id
        order = self._order(self.thc | ara)
        self._line(order, self.thc).price_unit = 300.0
        self._line(order, ara).write({"boss_manual_cost": 350.0, "boss_manual_cost_note": "DUA 26ES0000001 (prueba)",
                                      "price_unit": 350.0})
        order.with_user(self.sales).action_confirm()
        file = order.boss_expediente_id.with_env(self.env)
        duty = self._need(file, ara)
        self.assertEqual((duty.without_order, duty.state), (True, "awaiting_bill"))
        file.customs_broker_id = self.broker
        duty.partner_id = self.broker
        file.action_create_rfqs()
        self.assertFalse(duty.purchase_line_ids, "duties are billed by the broker without purchase order")
        # The broker's bill of the duties, entered on the file: matched to the service, counted once.
        bill = self.env["account.move"].with_context(
            boss_default_analytic={str(file.analytic_account_id.id): 100.0}).create({
                "move_type": "in_invoice", "partner_id": self.broker.id, "invoice_date": date(2026, 11, 5),
                "invoice_line_ids": [Command.create({"product_id": ara.id, "quantity": 1, "price_unit": 350.0,
                                                     "tax_ids": [Command.set(self.purchase_tax.ids)]})]})
        self.assertIn("not invoiced to the customer yet", bill.boss_bill_warning)
        # approved 23/10 (P30): the bill is posted on time, its payment waits for the customer invoice
        self.assertEqual(self.env.company.boss_bill_before_invoice, "block_payment")
        bill.with_user(self.accountant).action_post()
        with self.assertRaises(UserError):
            bill.with_user(self.accountant).action_register_payment()
        file.invalidate_recordset()
        duty.invalidate_recordset()
        self.assertEqual((duty.state, duty.billed_amount_company), ("billed", 350.0))
        # A receipt without order on the file (also what an employee expense posts): actual cost.
        receipt = self.env["account.move"].create({
            "move_type": "in_receipt", "partner_id": self.broker.id, "invoice_date": date(2026, 11, 5),
            "invoice_line_ids": [Command.create({"name": "Taxi aduana (prueba)", "quantity": 1, "price_unit": 20.0,
                                                 "analytic_distribution": {str(file.analytic_account_id.id): 100}})]})
        receipt.action_post()
        file.invalidate_recordset()
        self.assertEqual(file.amount_cost_actual, 370.0)
        self.assertEqual(file.amount_cost_pending, 240.0)  # THC still to order; duties not counted twice

        # Ceuta and Melilla belong to the CAN zone (approved 23/10, P17)
        self.assertEqual((vat_rules.zone("ES", "CE"), vat_rules.zone("ES", "ME"), vat_rules.zone("ES", "V")),
                         ("CAN", "CAN", "PRO"))
        # Customer in Spain without identification: not posted. A customer abroad without VAT: posted.
        spanish = self.env["res.partner"].create({"name": "CLIENTE SIN NIF (FICTICIO)",
                                                  "country_id": self.env.ref("base.es").id})
        foreign = self.env["res.partner"].create({"name": "CLIENTE CHINO (FICTICIO)",
                                                  "country_id": self.env.ref("base.cn").id})
        for partner, posts in ((spanish, False), (foreign, True)):
            other = self._order(self.thc, partner_id=partner.id)
            self._line(other, self.thc).price_unit = 300.0
            other.with_user(self.sales).action_confirm()
            invoice = other._create_invoices()
            if posts:
                invoice.with_user(self.accountant).action_post()
                self.assertEqual(invoice.state, "posted")
            else:
                with self.assertRaises(UserError):
                    invoice.with_user(self.accountant).action_post()
                if "l10n_es_passport" in partner._fields:  # Spanish localization: another identification counts
                    partner.l10n_es_passport = "X0000000T"
                    invoice.with_user(self.accountant).action_post()
                    self.assertEqual(invoice.state, "posted")
