"""ADR-002 spike: what standard Odoo 20 does for BOSS pricing cases.

Characterisation tests: each test pins the OBSERVED standard behaviour and logs a
"FINDING" line. Fictitious amounts only (no real supplier prices).
"""
import logging

from odoo import Command
from odoo.tests import TransactionCase, tagged

_logger = logging.getLogger(__name__)


def finding(text, *args):
    _logger.info("FINDING " + text, *args)


@tagged("post_install", "-at_install", "boss_spike")
class TestSpike(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_uom = cls.env.ref("uom.group_uom")
        cls.env.ref("base.group_user").write({"implied_ids": [Command.link(group_uom.id)]})
        cls.env.ref("base.user_root").write({"group_ids": [Command.link(group_uom.id)]})
        Uom = cls.env["uom.uom"]
        # Three independent bases (no relative unit => no conversion intended).
        cls.u20 = Uom.create({"name": "Cont 20'"})
        cls.u40 = Uom.create({"name": "Cont 40'"})
        cls.uwm = Uom.create({"name": "W/M"})
        cls.thc = cls.env["product.product"].create({
            "name": "THC - Terminal handling",
            "default_code": "THC",
            "type": "service",
            "uom_id": cls.u20.id,
            "uom_ids": [Command.set([cls.u40.id, cls.uwm.id])],
            "list_price": 999.0,  # sentinel: shows any fallback to the product sales price
        })
        cls.customer = cls.env["res.partner"].create({"name": "CLIENTE SPIKE"})
        cls.carrier = cls.env["res.partner"].create({"name": "NAVIERA SPIKE"})
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True

    def pricelist(self, *items):
        return self.env["product.pricelist"].create({
            "name": "PL spike",
            "currency_id": self.eur.id,
            "item_ids": [Command.create({"product_tmpl_id": self.thc.product_tmpl_id.id, **vals})
                         for vals in items],
        })

    def order(self, pricelist, *lines):
        return self.env["sale.order"].create({
            "partner_id": self.customer.id,
            "pricelist_id": pricelist.id,
            "order_line": [Command.create({"product_id": self.thc.id, **vals}) for vals in lines],
        })

    # 1. Same service, three charge bases: right price, unit and quantity -----------
    def test_1_fixed_sale_price_per_charge_base(self):
        pl = self.pricelist(
            {"uom_id": self.u20.id, "compute_price": "fixed", "fixed_price": 180.0},
            {"uom_id": self.u40.id, "compute_price": "fixed", "fixed_price": 240.0},
            {"uom_id": self.uwm.id, "compute_price": "fixed", "fixed_price": 12.0},
        )
        so = self.order(
            pl,
            {"product_uom_id": self.u20.id, "product_uom_qty": 2},
            {"product_uom_id": self.u40.id, "product_uom_qty": 1},
            {"product_uom_id": self.uwm.id, "product_uom_qty": 12.5},
        )
        got = [(l.product_uom_id.name, l.product_uom_qty, l.price_unit, l.price_subtotal)
               for l in so.order_line]
        finding("T1 lines (unit, qty, price_unit, subtotal) = %s", got)
        self.assertEqual(got, [("Cont 20'", 2, 180.0, 360.0), ("Cont 40'", 1, 240.0, 240.0),
                               ("W/M", 12.5, 12.0, 150.0)])
        self.assertEqual(so.order_line.pricelist_item_id.mapped("uom_id"), self.u20 | self.u40 | self.uwm)

    # 2. Missing price for one base: what does standard do? -------------------------
    def test_2_missing_rule_and_generic_rule_fallback(self):
        only20 = self.pricelist({"uom_id": self.u20.id, "compute_price": "fixed", "fixed_price": 180.0})
        line = self.order(only20, {"product_uom_id": self.u40.id, "product_uom_qty": 1}).order_line
        finding("T2a no 40' rule -> rule=%s price_unit=%s (list_price sentinel 999)",
                line.pricelist_item_id.id, line.price_unit)
        generic = self.pricelist({"compute_price": "fixed", "fixed_price": 180.0})
        line = self.order(generic, {"product_uom_id": self.uwm.id, "product_uom_qty": 12.5}).order_line
        finding("T2b rule without unit (180/cont) applied to W/M -> price_unit=%s", line.price_unit)

    # 3. Two prices for the same service/base/date ----------------------------------
    def test_3_conflicting_rules(self):
        pl = self.pricelist(
            {"uom_id": self.u40.id, "compute_price": "fixed", "fixed_price": 240.0},
            {"uom_id": self.u40.id, "compute_price": "fixed", "fixed_price": 250.0},
        )
        line = self.order(pl, {"product_uom_id": self.u40.id, "product_uom_qty": 1}).order_line
        finding("T3 two 40' rules (240, 250) -> picked %s, no error raised", line.price_unit)

    # 4. Relative units: hidden conversion ------------------------------------------
    def test_4_relative_units_convert_silently(self):
        teu = self.env["uom.uom"].create({"name": "TEU"})
        c40 = self.env["uom.uom"].create({"name": "Cont 40' (2 TEU)", "relative_uom_id": teu.id,
                                          "relative_factor": 2.0})
        self.thc.write({"uom_id": teu.id, "uom_ids": [Command.set([c40.id])]})
        pl = self.pricelist({"uom_id": c40.id, "compute_price": "fixed", "fixed_price": 240.0})
        line = self.order(pl, {"product_uom_id": c40.id, "product_uom_qty": 1}).order_line
        finding("T4 fixed 240 on a 40' rule, 40' defined as 2 TEU -> price_unit=%s", line.price_unit)
        qty = self.u20._compute_quantity(1, self.uwm)
        finding("T4b 1 Cont 20' converted to W/M (unrelated bases) = %s (no error)", qty)

    # 5. Supplier price (product.supplierinfo) selection ----------------------------
    def test_5_supplierinfo_selection(self):
        Info = self.env["product.supplierinfo"]
        for uom, price in ((self.u20, 150.0), (self.u40, 200.0), (self.uwm, 10.0)):
            Info.create({"partner_id": self.carrier.id, "product_tmpl_id": self.thc.product_tmpl_id.id,
                         "uom_id": uom.id, "min_qty": 0.0, "price": price,
                         "currency_id": self.eur.id})
        seller = self.thc._select_seller(partner_id=self.carrier, quantity=1, uom_id=self.u40)
        finding("T5a _select_seller(40') -> %s", seller)
        forced = self.thc._select_seller(partner_id=self.carrier, quantity=1, uom_id=self.u40,
                                         params={"force_uom": True})
        finding("T5b _select_seller(40', force_uom) -> %s", forced)

    # 6. Shipment cost + % : markup vs margin, minimum per unit vs line vs file -----
    def test_6_cost_plus_percentage(self):
        pl = self.pricelist({"uom_id": self.u40.id, "base": "boss_shipment_cost",
                             "compute_price": "markup", "price_markup": 25.0})
        line = self.order(pl, {"product_uom_id": self.u40.id, "product_uom_qty": 2,
                               "boss_cost_unit": 100.0}).order_line
        finding("T6a cost 100, surcharge 25%% -> price_unit=%s (margin 25%% would be 133.33)",
                line.price_unit)
        self.assertEqual(line.price_unit, 125.0)
        pl.item_ids.write({"price_min_margin": 30.0, "price_max_margin": 100000.0})
        line.order_id._recompute_prices()
        finding("T6b + price_min_margin 30 -> price_unit=%s subtotal=%s (minimum applies per unit)",
                line.price_unit, line.price_subtotal)
        self.assertEqual(self.thc.standard_price, 0.0, "product cost must stay untouched")

    # 7. Two offers, different costs; tariff update vs accepted offer ---------------
    def test_7_offers_isolated_and_accepted_offer_frozen(self):
        pl = self.pricelist({"uom_id": self.u40.id, "base": "boss_shipment_cost",
                             "compute_price": "markup", "price_markup": 25.0})
        a = self.order(pl, {"product_uom_id": self.u40.id, "product_uom_qty": 1, "boss_cost_unit": 100.0})
        b = self.order(pl, {"product_uom_id": self.u40.id, "product_uom_qty": 1, "boss_cost_unit": 200.0})
        b.order_line.boss_cost_unit = 220.0
        self.assertEqual((a.order_line.price_unit, b.order_line.price_unit), (125.0, 275.0))
        a.action_confirm()
        pl.item_ids.price_markup = 40.0
        finding("T7a after markup 25->40: accepted A=%s, draft B=%s (no action)",
                a.order_line.price_unit, b.order_line.price_unit)
        b._recompute_prices()
        finding("T7b draft B after 'update prices' = %s", b.order_line.price_unit)
        a.order_line.product_uom_qty = 2
        finding("T7c accepted A after changing quantity to 2 -> price_unit=%s", a.order_line.price_unit)
        a.order_line.boss_cost_unit = 150.0
        finding("T7d accepted A after changing its cost to 150 -> price_unit=%s", a.order_line.price_unit)
        self.assertEqual(self.thc.standard_price, 0.0)
