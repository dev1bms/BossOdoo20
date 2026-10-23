"""Engine tests without Odoo. FICTITIOUS amounts only (supplier references: test_references.py).

Run: python -m unittest discover -s addons/boss_pricing/engine/tests -t addons/boss_pricing
"""
import unittest
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

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


    def test_time_weekday_rules_on_an_estimate(self):
        # An estimate (days only) never assumes an exception that depends on the exit day; a rule tied only to
        # the start day (any Friday +1 day) applies.
        cont = [{"size": "40", "type_id": 1, "quantity": 1}]
        base = {"free_hours": 48, "free_mode": "threshold", "basis": "containers",
                "brackets": [{"up_to": 0, "unit_price": 10}]}
        exit_day = rule(1, method="time", params={**base, "saturday_until_monday": True, "friday_monday_free": 72})
        self.assertEqual(amount(exit_day, containers=cont, storage_days=3, start_weekday=5), Decimal("30.00"))
        self.assertEqual(amount(exit_day, containers=cont, storage_days=3, start_weekday=4), Decimal("30.00"))
        self.assertEqual(amount(exit_day, containers=cont, storage_days=2, start_weekday=5), Decimal("0.00"))
        friday = rule(1, method="time", params={**base, "friday_extra_day": True})
        self.assertEqual(amount(friday, containers=cont, storage_days=3, start_weekday=4), Decimal("0.00"))
        self.assertEqual(amount(friday, containers=cont, storage_days=4, start_weekday=4), Decimal("40.00"))
        # 36 free hours: an estimate of 2 days may be 25 to 48 hours, so only 1 day is surely free
        cold = rule(1, method="time", params={**base, "free_hours": 36})
        self.assertEqual(amount(cold, containers=cont, storage_days=1), Decimal("0.00"))
        self.assertEqual(amount(cold, containers=cont, storage_days=2), Decimal("20.00"))


MAD = ZoneInfo("Europe/Madrid")


def at(day, hour, minute=0):
    """Warehouse local time (Madrid). October 2026: Monday 12, Friday 16, Saturday 17; DST ends Sunday 25."""
    return datetime(2026, 10, day, hour, minute, tzinfo=MAD)


class TestStorageActualPeriod(unittest.TestCase):
    """Airport storage with the actual period. Fictitious tariff shaped like an airport handler's: per 100 kg and
    24 hours, 48 h free as a threshold, Friday with a Monday exit 72 h, Saturday free until Monday included,
    10 € up to 7 periods / 20 € more, minimum 50 per stay. 500 kg = 5 units. Expected values computed by hand."""

    PARAMS = {"basis": "awb_kg", "unit_size": 100, "period_unit": "24h", "free_hours": 48, "free_mode": "threshold",
              "friday_monday_free": 72, "saturday_until_monday": True, "min_amount": 50,
              "brackets": [{"up_to": 7, "unit_price": 10}, {"up_to": 0, "unit_price": 20}]}

    def stay(self, start, end, kg=500, **params):
        r = rule(1, method="time", params={**self.PARAMS, **params})
        return amount(r, awb_kg=kg, storage_start=start, storage_end=end)

    def test_48_hours_exactly_is_free_one_minute_more_is_charged_from_the_start(self):
        self.assertEqual(self.stay(at(12, 10), at(14, 10)), Decimal("0.00"))  # 48 h 00 min
        self.assertEqual(self.stay(at(12, 10), at(14, 10, 1)), Decimal("150.00"))  # 3 periods x 5 x 10

    def test_24_hour_periods_versus_calendar_days(self):
        # 120 h over six calendar dates (Mon 10:00 -> Sat 10:00): 5 periods of 24 h, 6 calendar days
        self.assertEqual(self.stay(at(12, 10), at(17, 10), saturday_until_monday=False), Decimal("250.00"))
        self.assertEqual(self.stay(at(12, 10), at(17, 10), saturday_until_monday=False, period_unit="calendar",
                                   free_hours=0, free_days=2), Decimal("300.00"))

    def test_daylight_saving_change_counts_real_hours(self):
        # Sat 24/10 10:00 CEST -> Mon 26/10 10:00 CET is 49 real hours (clocks go back on Sunday 25/10)
        self.assertEqual(self.stay(at(24, 10), at(26, 10), saturday_until_monday=False), Decimal("150.00"))

    def test_friday_arrival(self):
        self.assertEqual(self.stay(at(16, 9), at(19, 8)), Decimal("0.00"))  # Fri -> Mon, 71 h <= 72
        self.assertEqual(self.stay(at(16, 9), at(19, 10)), Decimal("200.00"))  # Fri -> Mon, 73 h: 4 periods
        self.assertEqual(self.stay(at(16, 9), at(20, 8)), Decimal("200.00"))  # Fri -> Tue, 95 h: 4 periods
        self.assertEqual(self.stay(at(16, 9), at(18, 11)), Decimal("150.00"))  # Fri -> Sun, 50 h > 48 h

    def test_saturday_arrival_is_free_until_monday_included_not_72_hours(self):
        self.assertEqual(self.stay(at(17, 9), at(19, 23, 59)), Decimal("0.00"))  # Sat -> Mon 23:59 (62 h 59 min)
        self.assertEqual(self.stay(at(17, 9), at(20, 8)), Decimal("150.00"))  # Sat -> Tue 08:00: 71 h, 3 periods
        self.assertEqual(self.stay(at(17, 23), at(20, 0, 30)), Decimal("150.00"))  # Sat 23:00 -> Tue 00:30

    def test_day_tiers_undecided_reading_is_not_priced_when_the_readings_differ(self):
        # 10 days of 24 h: day by day 7 x 5 x 10 + 3 x 5 x 20 = 650; whole stay at the higher rate 10 x 5 x 20 = 1000
        res = price([rule(1, method="time", params={**self.PARAMS, "tier_mode": "undecided"})],
                    {**SHIP, "awb_kg": 500, "storage_start": at(12, 10), "storage_end": at(22, 10)}, D)
        self.assertEqual(res.status, Status.NOT_READY)
        readings = dict(res.steps)["readings_undecided"]
        self.assertEqual({r["tier_mode"]: r["amount"] for r in readings["readings"]},
                         {"positional": Decimal("650"), "whole_stay": Decimal("1000")})
        self.assertEqual((readings["low"], readings["high"]), (Decimal("650"), Decimal("1000")))
        self.assertEqual(self.stay(at(12, 10), at(22, 10), tier_mode="positional"), Decimal("650.00"))
        self.assertEqual(self.stay(at(12, 10), at(22, 10), tier_mode="whole_stay"), Decimal("1000.00"))
        # 7 periods: both readings 350 -> priced; 8 periods: 450 or 800 -> not priced
        self.assertEqual(self.stay(at(12, 10), at(19, 10), tier_mode="undecided"), Decimal("350.00"))
        self.assertEqual(self.stay(at(12, 10), at(20, 10), tier_mode="undecided"), Status.NOT_READY)
        self.assertEqual(self.stay(at(12, 10), at(20, 10), tier_mode="positional"), Decimal("450.00"))
        # an estimate of 10 days: the same two readings
        self.assertEqual(amount(rule(1, method="time", params={**self.PARAMS, "tier_mode": "undecided"}), awb_kg=500,
                                storage_days=10), Status.NOT_READY)

    def test_day_count_and_rounding_undecided(self):
        undecided = {"period_unit": "undecided"}
        # Mon 10:00 -> Wed 10:01: 3 periods of 24 h and 3 calendar days -> the readings agree: 150
        self.assertEqual(self.stay(at(12, 10), at(14, 10, 1), **undecided), Decimal("150.00"))
        # Mon 10:00 -> Sat 10:00 (120 h): 5 periods (250) or 6 calendar days (300) -> not priced
        res = price([rule(1, method="time", params={**self.PARAMS, **undecided, "saturday_until_monday": False})],
                    {**SHIP, "awb_kg": 500, "storage_start": at(12, 10), "storage_end": at(17, 10)}, D)
        self.assertEqual(res.status, Status.NOT_READY)
        self.assertEqual({r["period_unit"]: r["amount"] for r in dict(res.steps)["readings_undecided"]["readings"]},
                         {"24h": Decimal("250"), "calendar": Decimal("300")})
        # «por 100 kg» without «o fracción»: 450 kg = 4.5 or 5 units (135 or 150); 500 kg = 5 units either way
        three = (at(12, 10), at(15, 9))
        self.assertEqual(self.stay(*three, kg=450, round_undecided=True), Status.NOT_READY)
        self.assertEqual(self.stay(*three, kg=500, round_undecided=True), Decimal("150.00"))
        self.assertEqual(self.stay(*three, kg=80, round_undecided=True), Decimal("50.00"))  # 24 or 30 -> minimum 50

    def test_minimum_per_stay_per_day_and_never_on_a_free_stay(self):
        self.assertEqual(self.stay(at(12, 10), at(15, 9), kg=80), Decimal("50.00"))  # 3 x 0.8 x 10 = 24 -> 50
        self.assertEqual(self.stay(at(12, 10), at(14, 10), kg=80), Decimal("0.00"))  # free stays free
        per_day = {"min_per_day": True, "min_amount": 15, "round_up": True}
        self.assertEqual(self.stay(at(12, 10), at(15, 9), kg=80, **per_day), Decimal("45.00"))  # 3 x max(10, 15)

    def test_per_100_kg_or_fraction_chooses_the_weight_then_rounds_up(self):
        three = (at(12, 10), at(15, 9))  # 71 h: 3 periods
        self.assertEqual(self.stay(*three, kg=100, round_up=True), Decimal("50.00"))  # 1 unit: 30 -> minimum 50
        self.assertEqual(self.stay(*three, kg=100.01, round_up=True), Decimal("60.00"))  # 2 units
        self.assertEqual(self.stay(*three, kg=400, round_up=True), Decimal("120.00"))  # 4 units
        self.assertEqual(self.stay(*three, kg=401, round_up=True), Decimal("150.00"))  # 5 units
        self.assertEqual(self.stay(*three, kg=401), Decimal("120.30"))  # pro rata 4.01 units
        # chargeable weight with the document's factor: max(300 kg, 1.5 m3 x 333 = 499.5) -> 5 units
        r = rule(1, method="time", params={**self.PARAMS, "basis": "chargeable_kg", "volumetric_factor": 333,
                                           "round_up": True})
        self.assertEqual(amount(r, gross_kg=300, volume_m3=1.5, storage_start=three[0], storage_end=three[1]),
                         Decimal("150.00"))

    def test_missing_and_inconsistent_data_is_never_a_zero(self):
        r = rule(1, method="time", params=self.PARAMS)
        self.assertEqual(price([r], {**SHIP, "storage_start": at(12, 10), "storage_end": at(14, 11)}, D).missing,
                         ["awb_kg"])
        self.assertEqual(price([r], {**SHIP, "awb_kg": 500, "storage_start": at(14, 10), "storage_end": at(12, 10)},
                               D).missing, ["storage_end"])
        self.assertEqual(price([r], {**SHIP, "awb_kg": 500, "storage_start": at(12, 10)}, D).missing,
                         ["storage_days"])  # period not ended and no estimate
        self.assertEqual(amount(r, awb_kg=500, storage_start=at(12, 10), storage_days=4), Decimal("200.00"))

    def test_calendar_days_franchise_counts_entry_and_exit_days(self):
        # Warehouse-like: per 100 kg or fraction and calendar day, 3 calendar days free as a threshold, 1 €
        cal = {"basis": "awb_kg", "unit_size": 100, "round_up": True, "period_unit": "calendar", "free_days": 3,
               "free_mode": "threshold", "brackets": [{"up_to": 0, "unit_price": 1}]}
        r = rule(1, method="time", params=cal)
        self.assertEqual(amount(r, awb_kg=1000, storage_start=at(12, 8), storage_end=at(14, 22)), Decimal("0.00"))
        self.assertEqual(amount(r, awb_kg=1000, storage_start=at(12, 8), storage_end=at(16, 17)), Decimal("50.00"))


if __name__ == "__main__":
    unittest.main()
