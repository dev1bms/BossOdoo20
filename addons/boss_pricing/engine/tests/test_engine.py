"""Engine tests without Odoo. FICTITIOUS amounts only (supplier references: test_references.py).

Run: python -m unittest discover -s addons/boss_pricing/engine/tests -t addons/boss_pricing
"""
import unittest
from datetime import date
from decimal import Decimal

from engine import Rule, Status, price

D = date(2026, 11, 2)
CARRIER_A, CARRIER_B, CUSTOMER = 11, 12, 21
SHIP = {"direction": "import", "carrier_id": CARRIER_A, "customer_id": CUSTOMER, "line_qty": 1}
BY_CARRIER = {"direction": {"import"}, "carrier_id": {CARRIER_A}}


def rule(id_, method="per_unit", lineage=1, version=1, approved=True, **kw):
    params = kw.pop("params", {})
    return Rule(id=id_, product_id=1, uom_id=40, method=method, currency="EUR", lineage_id=lineage,
                version=version, approved=approved, params=params,
                valid_from=kw.pop("valid_from", date(2026, 1, 1)), **kw)


def amount(r, **inputs):
    res = price([r], {**SHIP, **inputs}, D)
    return res.amount if res.status is Status.OK else res.status


class TestSelection(unittest.TestCase):
    def test_missing_carrier_is_reported_not_guessed(self):
        rules = [rule(1, params={"unit_price": 240}, conditions=BY_CARRIER),
                 rule(2, lineage=2, params={"unit_price": 250},
                      conditions={"direction": {"import"}, "carrier_id": {CARRIER_B}})]
        res = price(rules, {"direction": "import", "line_qty": 1}, D)
        self.assertEqual((res.status, res.missing), (Status.MISSING_INPUT, ["carrier_id"]))

    def test_same_scope_in_two_tariffs_is_a_conflict_until_priority_decides(self):
        rules = [rule(1, params={"unit_price": 240}, conditions=BY_CARRIER),
                 rule(2, lineage=2, params={"unit_price": 250}, conditions=BY_CARRIER)]
        self.assertEqual(price(rules, SHIP, D).status, Status.CONFLICT)
        rules[1] = rule(2, lineage=2, params={"unit_price": 250}, conditions=BY_CARRIER, priority=5)
        self.assertEqual(price(rules, SHIP, D).amount, Decimal("250.00"))

    def test_customer_price_wins_and_newest_version_by_date(self):
        rules = [rule(1, params={"unit_price": 240}, conditions=BY_CARRIER),
                 rule(2, lineage=2, params={"unit_price": 200},
                      conditions={**BY_CARRIER, "customer_id": {CUSTOMER}})]
        self.assertEqual(price(rules, SHIP, D).rule.id, 2)
        versions = [rule(1, params={"unit_price": 240}),
                    rule(2, version=2, params={"unit_price": 260}, valid_from=date(2026, 9, 1))]
        self.assertEqual(price(versions, SHIP, D).rule.id, 2)
        self.assertEqual(price(versions, SHIP, date(2026, 8, 31)).rule.id, 1)

    def test_unapproved_on_request_missing_date_and_quantity(self):
        self.assertEqual(price([rule(1, approved=False, params={"unit_price": 1})], SHIP, D).status,
                         Status.PENDING_APPROVAL)
        res = price([rule(1, on_request=True, params={"unit_price": 0})], SHIP, D)
        self.assertEqual((res.status, res.amount), (Status.ON_REQUEST, None))
        self.assertEqual(price([rule(1, params={"unit_price": 1})], SHIP, None).missing, ["tariff_date"])
        self.assertEqual(price([rule(1, params={"unit_price": 1})], {**SHIP, "line_qty": 0}, D).missing,
                         ["quantity"])


class TestMethods(unittest.TestCase):
    CONTAINERS = [{"size": "20", "type_id": 1, "quantity": 2}, {"size": "40", "type_id": 1, "quantity": 1},
                  {"size": "40", "type_id": 3, "quantity": 1}]

    def test_per_unit_quantities(self):
        self.assertEqual(amount(rule(1, params={"unit_price": 240}), line_qty=2), Decimal("480.00"))
        by_size = rule(1, params={"unit_price": 100, "basis": "containers"})
        self.assertEqual(amount(by_size, containers=self.CONTAINERS, container_size="40"), Decimal("200.00"))
        teu = rule(1, params={"unit_price": 10, "basis": "teu"})
        self.assertEqual(amount(teu, containers=self.CONTAINERS), Decimal("60.00"))  # 2x1 + 2x2 TEU
        # per 100 kg or fraction of chargeable kg (factor from the document), minimum on the total
        fraction = rule(1, params={"unit_price": 3, "basis": "chargeable_kg", "volumetric_factor": 167,
                                   "unit_size": 100, "round_up": True, "min_amount": 10})
        # max(300, 1 x 167) = 300 kg -> 3 units x 3 = 9 -> minimum 10
        self.assertEqual(amount(fraction, gross_kg=300, volume_m3=1), Decimal("10.00"))
        self.assertEqual(amount(fraction, gross_kg=301, volume_m3=1), Decimal("12.00"))  # 3.01 -> 4 units
        self.assertEqual(amount(fraction, gross_kg=100, volume_m3=2), Decimal("12.00"))  # 2 x 167 = 334 kg -> 4
        self.assertEqual(price([fraction], {**SHIP, "gross_kg": 100}, D).missing, ["volume_m3"])

    def test_max_of_bases(self):
        r = rule(1, method="max_of_bases", params={"basis": "gross_ton", "unit_price": 20, "basis_2": "volume_m3",
                                                   "unit_price_2": 10, "min_amount": 30})
        self.assertEqual(amount(r, gross_kg=2500, volume_m3=4), Decimal("50.00"))  # 2.5 t x 20 vs 4 m3 x 10
        self.assertEqual(amount(r, gross_kg=1000, volume_m3=6), Decimal("60.00"))
        self.assertEqual(amount(r, gross_kg=500, volume_m3=1), Decimal("30.00"))  # minimum

    def test_brackets_bounds_open_bracket_and_floor(self):
        table = [{"up_to": 100, "fixed_amount": 50}, {"up_to": 500, "unit_price": 0.4},
                 {"up_to": 1000, "unit_price": 0.3}]
        r = rule(1, method="brackets", params={"basis": "gross_kg", "brackets": table})
        self.assertEqual(amount(r, gross_kg=100), Decimal("50.00"))  # inclusive upper bound
        self.assertEqual(amount(r, gross_kg=101), Decimal("40.40"))  # whole quantity x unit price
        self.assertEqual(amount(r, gross_kg=1001), Status.NO_TARIFF)  # above the document
        floor = rule(1, method="brackets", params={"basis": "gross_kg", "brackets": table, "floor_previous": True})
        self.assertEqual(amount(floor, gross_kg=501), Decimal("200.00"))  # 150.30 < 500 x 0.4
        open_table = table + [{"up_to": 0, "unit_price": 0.25}]
        self.assertEqual(amount(rule(1, method="brackets", params={"basis": "gross_kg", "brackets": open_table}),
                                gross_kg=2000), Decimal("500.00"))

    def test_percent_of_goods_and_of_same_supplier_services(self):
        r = rule(1, method="percent", params={"percent_base": "goods_value", "rate": 0.3, "min_amount": 35})
        self.assertEqual(amount(r, goods_value=20000), Decimal("60.00"))
        self.assertEqual(amount(r, goods_value=1000), Decimal("35.00"))
        fuel = rule(1, method="percent", params={"percent_base": "services", "rate": 10, "base_product_ids": [7],
                                                 "supplier_id": 5, "currency": "EUR"})
        related = [{"product_id": 7, "supplier_id": 5, "amount": 300, "currency": "EUR"},
                   {"product_id": 7, "supplier_id": 6, "amount": 999, "currency": "EUR"}]
        self.assertEqual(amount(fuel, related_costs=related), Decimal("30.00"))
        self.assertEqual(price([fuel], SHIP, D).missing, ["base_services"])

    def test_time_deduct_threshold_tiers_and_estimate_zero(self):
        tiers = [{"up_to": 7, "unit_price": 10}, {"up_to": 0, "unit_price": 20}]
        deduct = rule(1, method="time", params={"free_days": 4, "free_mode": "deduct", "brackets": tiers,
                                                "basis": "containers"})
        cont = [{"size": "40", "type_id": 1, "quantity": 2}]
        # days 5..9 charged: 5,6,7 at 10 and 8,9 at 20 -> 70 per container x 2
        self.assertEqual(amount(deduct, containers=cont, storage_days=9), Decimal("140.00"))
        self.assertEqual(amount(deduct, containers=cont, storage_days=4), Decimal("0.00"))  # justified zero
        threshold = rule(1, method="time", params={"free_hours": 48, "free_mode": "threshold", "brackets": tiers,
                                                   "basis": "chargeable_kg", "volumetric_factor": 167,
                                                   "unit_size": 100, "round_up": True, "min_amount": 50})
        self.assertEqual(amount(threshold, gross_kg=500, volume_m3=1, storage_days=2), Decimal("0.00"))
        self.assertEqual(amount(threshold, gross_kg=500, volume_m3=1, storage_days=3), Decimal("150.00"))
        relative = rule(1, method="time", params={"free_days": 7, "tier_mode": "relative", "basis": "containers",
                                                  "brackets": [{"up_to": 5, "unit_price": 10},
                                                               {"up_to": 0, "unit_price": 20}]})
        # days 8..12 are the first 5 charged days at 10, days 13..15 at 20: (50 + 60) x 2 containers
        self.assertEqual(amount(relative, containers=cont, storage_days=15), Decimal("220.00"))
        whole = rule(1, method="time", params={"free_days": 0, "brackets": tiers, "tier_mode": "whole_stay",
                                               "basis": "containers"})
        self.assertEqual(amount(whole, containers=cont, storage_days=8), Decimal("320.00"))
        self.assertEqual(price([deduct], {**SHIP, "containers": cont}, D).missing, ["storage_days"])
        self.assertEqual(amount(deduct, containers=cont, storage_days=0), Decimal("0.00"))  # estimate 0 days


if __name__ == "__main__":
    unittest.main()
