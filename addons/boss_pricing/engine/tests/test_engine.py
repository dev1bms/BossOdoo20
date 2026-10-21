"""Engine tests without Odoo. FICTITIOUS amounts only (no real supplier prices).

Run: python -m unittest discover -s addons/boss_pricing/engine/tests -t addons/boss_pricing
"""
import unittest
from datetime import date
from decimal import Decimal

from engine import Rule, Status, price

D = date(2026, 11, 2)
CARRIER_A, CARRIER_B, CUSTOMER = 11, 12, 21


def rule(id_, unit_price, lineage=1, version=1, approved=True, **kw):
    params = {"unit_price": unit_price, **kw.pop("params", {})}
    return Rule(id=id_, product_id=1, uom_id=40, method="per_unit", currency="EUR",
                lineage_id=lineage, version=version, approved=approved, params=params,
                valid_from=kw.pop("valid_from", date(2026, 1, 1)), **kw)


SHIP = {"direction": "import", "carrier_id": CARRIER_A, "customer_id": CUSTOMER}
BY_CARRIER = {"direction": {"import"}, "carrier_id": {CARRIER_A}}


class TestComputation(unittest.TestCase):
    def test_per_unit_quantity_in_charge_basis(self):
        res = price([rule(1, 240, conditions=BY_CARRIER)], SHIP, D, 2)
        self.assertEqual((res.status, res.amount, res.currency), (Status.OK, Decimal("480.00"), "EUR"))

    def test_minimum_applies_to_the_line_total(self):
        res = price([rule(1, "12.5", params={"min_amount": 60})], SHIP, D, 3)
        self.assertEqual(res.amount, Decimal("60.00"))
        self.assertEqual([s[0] for s in res.steps], ["per_unit", "minimum"])

    def test_on_request_has_no_amount(self):
        res = price([rule(1, 0, on_request=True)], SHIP, D, 1)
        self.assertEqual((res.status, res.amount), (Status.ON_REQUEST, None))


class TestSelection(unittest.TestCase):
    def test_missing_carrier_is_reported_not_guessed(self):
        rules = [rule(1, 240, conditions=BY_CARRIER), rule(2, 250, lineage=2, conditions={
            "direction": {"import"}, "carrier_id": {CARRIER_B}})]
        res = price(rules, {"direction": "import"}, D, 1)
        self.assertEqual((res.status, res.missing), (Status.MISSING_INPUT, ["carrier_id"]))

    def test_same_scope_in_two_tariffs_is_a_conflict_until_priority_decides(self):
        rules = [rule(1, 240, conditions=BY_CARRIER), rule(2, 250, lineage=2, conditions=BY_CARRIER)]
        self.assertEqual(price(rules, SHIP, D, 1).status, Status.CONFLICT)
        rules[1] = rule(2, 250, lineage=2, conditions=BY_CARRIER, priority=5)
        self.assertEqual(price(rules, SHIP, D, 1).amount, Decimal("250.00"))

    def test_customer_price_wins_over_general_price(self):
        rules = [rule(1, 240, conditions=BY_CARRIER),
                 rule(2, 200, lineage=2, conditions={**BY_CARRIER, "customer_id": {CUSTOMER}})]
        self.assertEqual(price(rules, SHIP, D, 1).rule.id, 2)

    def test_newest_version_by_date_and_older_dates_keep_their_version(self):
        rules = [rule(1, 240), rule(2, 260, version=2, valid_from=date(2026, 9, 1))]
        self.assertEqual(price(rules, SHIP, D, 1).rule.id, 2)
        self.assertEqual(price(rules, SHIP, date(2026, 8, 31), 1).rule.id, 1)

    def test_unapproved_price_is_not_used(self):
        res = price([rule(1, 240, approved=False)], SHIP, D, 1)
        self.assertEqual((res.status, res.amount), (Status.PENDING_APPROVAL, None))

    def test_missing_date_or_quantity(self):
        self.assertEqual(price([rule(1, 240)], SHIP, None, 1).missing, ["tariff_date"])
        self.assertEqual(price([rule(1, 240)], SHIP, D, 0).missing, ["quantity"])


if __name__ == "__main__":
    unittest.main()
