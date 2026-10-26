"""Follow-up of an accepted shipment: cost recomputed from the file data, services added after acceptance, agreement
for several shipments, partial / cancelled / replaced purchases, purchase basis and who sees which figure.
FICTITIOUS partners, prices and taxes only."""
from datetime import date, datetime

from odoo import SUPERUSER_ID, Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, new_test_user, tagged

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

    def test_zero_quantity_bill_lines_do_not_hold_the_payment(self):
        """D-1 (26/10/2026): Odoo 20 copies every purchase line on the bill, quantity 0 for services not performed;
        once the billed service is invoiced to the customer the payment is free."""
        bl = self.env.ref("boss_services.service_bl").product_variant_id
        self._tariff(self.carrier, bl, {"unit_price": 60.0}, carrier_id=self.carrier.id)
        order, file = self._accepted(self.thc | bl, {self.thc: 300.0, bl: 90.0})
        file.with_user(self.sales).action_create_rfqs()
        po = file.purchase_order_ids
        po.with_user(self.manager).button_confirm()
        with self.assertRaises(UserError):  # nothing performed: no bill of zeros
            po.with_user(self.accountant).action_create_invoice()
        self._need(file, self.thc).with_user(self.sales).action_mark_performed()
        po.with_user(self.accountant).action_create_invoice()
        bill = po.invoice_ids
        self.assertEqual(sorted(bill.invoice_line_ids.mapped("quantity")), [0.0, 1.0])  # BL not performed: 0
        bill.invoice_date = date(2026, 11, 5)
        bill.invoice_line_ids.tax_ids = self.purchase_tax
        bill.with_user(self.accountant).action_post()
        with self.assertRaises(UserError):  # THC not invoiced to the customer yet
            bill.with_user(self.accountant).action_register_payment()
        with self.assertRaises(UserError):  # nor through the payments wizard opened on the bill (list, statement)
            self.env["account.payment.register"].with_user(self.accountant).with_context(
                active_model="account.move", active_ids=bill.ids).create({}).action_create_payments()
        thc_part = file.allocation_ids.filtered(lambda a: a.product_id == self.thc)
        wizard = self.env["boss.invoice.services"].with_user(self.sales).create({
            "expediente_id": file.id, "allocation_ids": [Command.set(thc_part.ids)]})
        self.env["account.move"].browse(wizard.action_create()["res_id"]).with_user(self.accountant).action_post()
        self.assertFalse(bill.boss_bill_warning)
        bill.with_user(self.accountant).action_register_payment()  # the BL line with quantity 0 does not hold it

    def test_paid_on_behalf_on_current_liability_accounts(self):
        """D-2 (26/10/2026): with the accounts proposed to Ángel (sub-accounts of 419, current liabilities, as
        Odoo 17) the broker's bill and the customer invoice of the duties are created and posted; on a payable
        account (419000) neither can be."""
        ara = self.env.ref("boss_services.service_ara").product_variant_id
        Account = self.env["account.account"]
        payable = Account.search([("account_type", "=", "liability_payable")], limit=1)
        charged = Account.create({"code": "419002", "name": "Suplidos aranceles repercutidos (prueba)",
                                  "account_type": "liability_current", "reconcile": False})
        borne = Account.create({"code": "419004", "name": "Suplidos aranceles soportados (prueba)",
                                "account_type": "liability_current", "reconcile": False})
        order = self._order(self.thc | ara)
        self._line(order, self.thc).price_unit = 300.0
        self._line(order, ara).write({"boss_manual_cost": 350.0, "boss_manual_cost_note": "DUA (prueba)",
                                      "price_unit": 350.0})
        order.with_user(self.sales).action_confirm()
        file = order.boss_expediente_id.with_env(self.env)
        ara_part = file.allocation_ids.filtered(lambda a: a.product_id == ara)

        def broker_bill():
            return self.env["account.move"].with_context(
                boss_default_analytic={str(file.analytic_account_id.id): 100.0}).create({
                    "move_type": "in_invoice", "partner_id": self.broker.id, "invoice_date": date(2026, 11, 5),
                    "invoice_line_ids": [Command.create({"product_id": ara.id, "quantity": 1, "price_unit": 350.0,
                                                         "tax_ids": [Command.set(self.purchase_tax.ids)]})]})

        ara.product_tmpl_id.write({"property_account_income_id": payable.id,
                                   "property_account_expense_id": payable.id})
        with self.assertRaises(UserError):  # 419000 (payable): the configuration of 23/10 fails
            broker_bill()
        ara.product_tmpl_id.write({"property_account_income_id": charged.id,
                                   "property_account_expense_id": borne.id})
        bill = broker_bill()
        self.assertEqual(bill.invoice_line_ids.account_id, borne)
        bill.with_user(self.accountant).action_post()
        wizard = self.env["boss.invoice.services"].with_user(self.sales).create({
            "expediente_id": file.id, "allocation_ids": [Command.set(ara_part.ids)]})
        invoice = self.env["account.move"].browse(wizard.action_create()["res_id"])
        self.assertEqual(invoice.invoice_line_ids.account_id, charged)
        invoice.with_user(self.accountant).action_post()
        self.assertEqual((invoice.state, bill.state), ("posted", "posted"))

    def test_acceptance_with_locked_confirmed_orders(self):
        """boss20 has «Lock confirmed sales» on: Odoo locks the order inside the confirmation, then BOSS writes the
        analytic account of the file on its lines. Found on boss20 on 26/10/2026 (S00024)."""
        lock = self.env.ref("sale.group_auto_done_setting")  # what the setting does: the feature group on everybody
        self.env.ref("base.group_user").write({"implied_ids": [Command.link(lock.id)]})
        self.env["res.users"].browse(SUPERUSER_ID).sudo().write({"group_ids": [Command.link(lock.id)]})
        order, file = self._accepted(self.thc, {self.thc: 300.0})
        self.assertTrue(order.locked)
        line = order.order_line.filtered(lambda l: l.product_id == self.thc)
        self.assertIn(str(file.analytic_account_id.id), line.analytic_distribution)
        with self.assertRaises(UserError):  # the lock still protects everything else
            line.with_user(self.sales).price_unit = 1.0

    def test_file_dates_set_the_actual_period_and_recompute(self):
        """Cristina (26/10/2026): ATA and Pickup with date and time on the file; the system computes the dates. The
        storage period follows them (NOA first when set), the cost is recomputed, the sale is untouched; a period
        typed on the service is never overwritten by the file dates."""
        order, file = self._accepted(self.thc | self.alm, {self.thc: 300.0, self.alm: 120.0}, boss_storage_days=5)
        alm = self._need(file, self.alm)
        self.assertEqual(alm.expected_amount, 75.0)  # estimate: (5 - 2 free) x 25
        file.write({"ata": datetime(2026, 11, 2, 8, 0), "pickup_date": datetime(2026, 11, 10, 10, 0)})
        alm.invalidate_recordset()
        self.assertEqual((alm.period_start, alm.period_end), (datetime(2026, 11, 2, 8, 0), datetime(2026, 11, 10, 10, 0)))
        self.assertEqual(alm.expected_amount, 175.0)  # 9 calendar days - 2 free = 7 x 25, from the actual period
        self.assertFalse(alm.period_manual)
        self.assertTrue(file.event_ids.filtered(lambda e: "ALM" in e.name))
        self.assertEqual(self._line(order, self.alm).price_unit, 120.0)  # sale unchanged
        file.noa = datetime(2026, 11, 3, 9, 0)  # the handler counts from the arrival notice
        alm.invalidate_recordset()
        self.assertEqual(alm.period_start, datetime(2026, 11, 3, 9, 0))
        self.assertEqual(alm.expected_amount, 150.0)  # 8 days - 2 = 6 x 25
        alm.period_end = datetime(2026, 11, 12, 10, 0)  # typed by a person
        self.assertTrue(alm.period_manual)
        file.pickup_date = datetime(2026, 11, 20, 10, 0)
        alm.invalidate_recordset()
        self.assertEqual(alm.period_end, datetime(2026, 11, 12, 10, 0))  # the file no longer overwrites it

    def test_handler_of_the_airline_at_the_airport(self):
        """Hoja1 B9/C9/C10: HAN and the other handling services are bought from the handler of the airline at the
        airport. One handler known: proposed on the quotation line and on the file, and the need gets it as
        supplier. Several handlers (IAG at MAD: Iberia or WFS): nothing is chosen for the user, the file only offers
        those; choosing one on the file gives it to the handling needs still without supplier."""
        Partner = self.env["res.partner"]
        han = self.env.ref("boss_services.service_han").product_variant_id
        airline, lh = Partner.create([{"name": "AEROLINEA UNO (FICTICIA)"}, {"name": "AEROLINEA DOS (FICTICIA)"}])
        wfs, iberia = Partner.create([{"name": "HANDLER A (FICTICIO)", "boss_is_supplier": True},
                                      {"name": "HANDLER B (FICTICIO)", "boss_is_supplier": True}])
        mad, bcn = self.env.ref("boss_pricing.port_esmad_air"), self.env.ref("boss_pricing.port_esbcn_air")
        self.env["boss.airline.handler"].create([
            {"airline_id": airline.id, "airport_id": mad.id, "handler_id": wfs.id},
            {"airline_id": lh.id, "airport_id": mad.id, "handler_id": wfs.id},
            {"airline_id": lh.id, "airport_id": mad.id, "handler_id": iberia.id},
        ])
        self._tariff(wfs, han, {"basis": "awb_kg", "unit_price": 0.2}, transport_mode="air", load_type=False,
                     port_ids=[Command.set(mad.ids)])
        air = {"boss_transport_mode": "air", "boss_load_type": False, "boss_carrier_id": airline.id,
               "boss_port_id": mad.id, "boss_container_ids": False, "boss_awb_kg": 500.0}
        order, file = self._accepted(han, {han: 200.0}, **air)
        self.assertEqual(self._line(order, han).boss_supplier_id, wfs)
        self.assertEqual(file.handler_id, wfs)
        self.assertEqual(self._need(file, han).partner_id, wfs)

        # Two handlers known: nothing is chosen for the user; the quotation line has no supplier restriction, so the
        # only tariff that fits (handler A) prices it. The file offers both handlers; choosing one moves the handling
        # needs not ordered yet to it.
        order2, file2 = self._accepted(han, {han: 200.0}, **dict(air, boss_carrier_id=lh.id))
        self.assertFalse(self._line(order2, han).boss_supplier_id)
        self.assertFalse(file2.handler_id)
        self.assertEqual(file2.handler_candidate_ids, wfs | iberia)
        self.assertEqual(self._need(file2, han).partner_id, wfs)
        file2.handler_id = iberia
        self.assertEqual(self._need(file2, han).partner_id, iberia)
        # Another airport without a known handler: no candidates, free choice.
        file2.port_id = bcn
        self.assertFalse(file2.handler_candidate_ids)
        # On the form, changing the airline replaces the handler of the previous one by the new single handler.
        self.env["boss.airline.handler"].create({"airline_id": lh.id, "airport_id": bcn.id, "handler_id": iberia.id})
        with Form(file) as form:
            form.carrier_id = lh
            self.assertEqual(form.handler_id, wfs)  # LH at MAD: two handlers, the previous one (WFS) is among them
            form.port_id = bcn
            self.assertEqual(form.handler_id, iberia)  # LH at BCN: only Iberia
