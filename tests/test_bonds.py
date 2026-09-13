"""Independent financial invariants and calendar cases for fixed-rate bonds."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from math import isfinite

import numpy as np
import pytest

from fixed_income import BondAnalytics, FixedRateBond
from fixed_income.cli import main


@pytest.fixture
def bond() -> FixedRateBond:
    return FixedRateBond(date(2025, 4, 15), date(2030, 1, 15), 0.04)


@pytest.mark.parametrize("frequency", [1, 2])
def test_par_on_coupon_date(frequency: int) -> None:
    bond = FixedRateBond(date(2025, 1, 15), date(2030, 1, 15), 0.04, frequency=frequency)
    assert bond.clean_price(0.04) == pytest.approx(100.0, abs=1e-11)
    assert bond.dirty_price(0.04) == pytest.approx(100.0, abs=1e-11)
    assert bond.accrued_interest() == 0.0


@pytest.mark.parametrize("frequency", [1, 2])
def test_premium_discount_and_monotonicity(frequency: int) -> None:
    bond = FixedRateBond(date(2025, 4, 15), date(2030, 1, 15), 0.04, frequency=frequency)
    assert bond.clean_price(0.03) > 100
    assert bond.clean_price(0.05) < 100
    assert bond.dirty_price(0.03) > bond.dirty_price(0.04) > bond.dirty_price(0.05)


def test_dirty_clean_accrual(bond: FixedRateBond) -> None:
    # Jan 15 to Apr 15 is 90 days; Jan 15 to Jul 15 is 181 days.
    assert bond.accrued_interest() == pytest.approx(2.0 * 90 / 181)
    assert bond.dirty_price(0.045) == pytest.approx(
        bond.clean_price(0.045) + bond.accrued_interest()
    )


def test_exact_half_period_accrual() -> None:
    # Jan 1 to Jul 1 in leap year 2024 is 182 days; Apr 1 is day 91.
    bond = FixedRateBond(date(2024, 4, 1), date(2026, 7, 1), 0.06)
    assert bond.accrued_interest() == pytest.approx(1.5)


@pytest.mark.parametrize(
    ("settlement", "previous", "following", "count"),
    [
        (date(2025, 7, 14), date(2025, 1, 15), date(2025, 7, 15), 4),
        (date(2025, 7, 15), date(2025, 7, 15), date(2026, 1, 15), 3),
        (date(2025, 7, 16), date(2025, 7, 15), date(2026, 1, 15), 3),
    ],
)
def test_schedule_at_coupon_boundary(
    settlement: date, previous: date, following: date, count: int
) -> None:
    bond = FixedRateBond(settlement, date(2027, 1, 15), 0.04)
    schedule = bond.coupon_schedule()
    assert bond.previous_coupon_date == previous
    assert bond.next_coupon_date == following
    assert schedule[0] == following
    assert schedule[-1] == bond.maturity_date
    assert len(schedule) == count
    assert all(payment > settlement for payment in schedule)
    assert tuple(sorted(set(schedule))) == schedule
    if settlement == previous:
        assert bond.accrued_interest() == 0.0


def test_maturity_anchor_prevents_month_end_drift() -> None:
    bond = FixedRateBond(date(2023, 9, 1), date(2025, 8, 31), 0.04)
    assert bond.previous_coupon_date == date(2023, 8, 31)
    assert bond.coupon_schedule() == (
        date(2024, 2, 29), date(2024, 8, 31),
        date(2025, 2, 28), date(2025, 8, 31),
    )


def test_annual_leap_day_schedule() -> None:
    bond = FixedRateBond(date(2024, 3, 1), date(2028, 2, 29), 0.04, frequency=1)
    assert bond.previous_coupon_date == date(2024, 2, 29)
    assert bond.coupon_schedule() == (
        date(2025, 2, 28), date(2026, 2, 28),
        date(2027, 2, 28), date(2028, 2, 29),
    )
    assert bond.accrued_interest() == pytest.approx(4 / 365)


def test_single_fractional_period_known_values() -> None:
    bond = FixedRateBond(date(2024, 4, 1), date(2024, 7, 1), 0.06)
    # Half a semiannual period remains: one CF of 103, discounted by sqrt(1.02).
    expected_price = 103 / (1.02 ** 0.5)
    assert bond.coupon_schedule() == (date(2024, 7, 1),)
    assert bond.dirty_price(0.04) == pytest.approx(expected_price)
    assert bond.clean_price(0.04) == pytest.approx(expected_price - 1.5)
    assert bond.macaulay_duration(0.04) == pytest.approx(0.25)
    assert bond.modified_duration(0.04) == pytest.approx(0.25 / 1.02)
    assert bond.convexity(0.04) == pytest.approx(0.5 * 1.5 / (4 * 1.02**2))


def test_day_before_maturity_has_one_fractional_payment() -> None:
    bond = FixedRateBond(date(2025, 7, 14), date(2025, 7, 15), 0.04)
    assert bond.dirty_price(0.04) == pytest.approx(102 / 1.02 ** (1 / 181))
    assert bond.accrued_interest() == pytest.approx(2 * 180 / 181)


@pytest.mark.parametrize("frequency", [1, 2])
@pytest.mark.parametrize("ytm", [-0.01, 0.0, 0.045])
def test_zero_coupon_known_price_and_duration(frequency: int, ytm: float) -> None:
    bond = FixedRateBond(date(2025, 1, 15), date(2030, 1, 15), 0, frequency=frequency)
    assert bond.dirty_price(ytm) == pytest.approx(100 / (1 + ytm / frequency) ** (5 * frequency))
    assert bond.macaulay_duration(ytm) == pytest.approx(5.0)
    assert bond.accrued_interest() == 0


@pytest.mark.parametrize("frequency", [1, 2])
@pytest.mark.parametrize("ytm", [-0.01, 0.0, 0.045])
def test_duration_matches_numerical_first_derivative(frequency: int, ytm: float) -> None:
    bond = FixedRateBond(date(2025, 4, 15), date(2030, 1, 15), 0.04, frequency=frequency)
    # 0.1 bp limits truncation error while retaining ample price precision.
    h = 1e-5
    price = bond.dirty_price(ytm)
    derivative = (bond.dirty_price(ytm + h) - bond.dirty_price(ytm - h)) / (2 * h)
    assert bond.modified_duration(ytm) == pytest.approx(-derivative / price, rel=2e-8)
    assert bond.macaulay_duration(ytm) == pytest.approx(
        bond.modified_duration(ytm) * (1 + ytm / frequency)
    )


@pytest.mark.parametrize("frequency", [1, 2])
@pytest.mark.parametrize("ytm", [-0.01, 0.0, 0.045])
def test_convexity_matches_numerical_second_derivative(frequency: int, ytm: float) -> None:
    bond = FixedRateBond(date(2025, 4, 15), date(2030, 1, 15), 0.04, frequency=frequency)
    # A larger 1 bp step avoids cancellation in the second price difference;
    # the central formula's O(h²) error fits comfortably within 1e-6 relative.
    h = 1e-4
    price = bond.dirty_price(ytm)
    derivative = (bond.dirty_price(ytm + h) - 2 * price + bond.dirty_price(ytm - h)) / h**2
    assert bond.convexity(ytm) == pytest.approx(derivative / price, rel=1e-6)
    assert bond.convexity(ytm) > 0


def test_dv01_is_full_repricing(bond: FixedRateBond) -> None:
    ytm = 0.045
    direct = (bond.dirty_price(0.0449) - bond.dirty_price(0.0451)) / 2
    assert bond.dv01(ytm) == pytest.approx(direct, abs=1e-12)
    assert bond.dv01(ytm) > 0
    approximation = bond.modified_duration(ytm) * bond.dirty_price(ytm) * 0.0001
    assert bond.dv01(ytm) == pytest.approx(approximation, rel=1e-6)


def test_dv01_differs_from_duration_approximation_for_long_bond() -> None:
    bond = FixedRateBond(date(2025, 1, 1), date(2125, 1, 1), 0, frequency=1)
    ytm = 0.01
    direct = (100 / 1.0099**100 - 100 / 1.0101**100) / 2
    approximation = bond.modified_duration(ytm) * bond.dirty_price(ytm) * 0.0001
    assert bond.dv01(ytm) == pytest.approx(direct, rel=1e-11)
    assert abs(bond.dv01(ytm) - approximation) > 1e-6


def test_face_value_scaling(bond: FixedRateBond) -> None:
    larger = replace(bond, face_value=1000)
    for name in ("dirty_price", "clean_price", "dv01"):
        assert getattr(larger, name)(0.045) == pytest.approx(10 * getattr(bond, name)(0.045))
    assert larger.accrued_interest() == pytest.approx(10 * bond.accrued_interest())
    for name in ("macaulay_duration", "modified_duration", "convexity"):
        assert getattr(larger, name)(0.045) == pytest.approx(getattr(bond, name)(0.045))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("maturity_date", date(2025, 4, 15), "maturity_date"),
        ("maturity_date", date(2025, 4, 14), "maturity_date"),
        ("settlement_date", "2025-04-15", "datetime.date"),
        ("settlement_date", datetime(2025, 4, 15), "datetime.date"),
        ("face_value", 0, "face_value"),
        ("face_value", -100, "face_value"),
        ("face_value", float("nan"), "face_value"),
        ("face_value", float("inf"), "face_value"),
        ("face_value", float("-inf"), "face_value"),
        ("coupon_rate", -0.01, "coupon_rate"),
        ("coupon_rate", float("nan"), "coupon_rate"),
        ("coupon_rate", float("inf"), "coupon_rate"),
        ("coupon_rate", float("-inf"), "coupon_rate"),
        ("coupon_rate", "0.04", "coupon_rate"),
        ("coupon_rate", True, "coupon_rate"),
        ("frequency", 0, "frequency"),
        ("frequency", 4, "frequency"),
        ("frequency", 2.0, "frequency"),
        ("frequency", True, "frequency"),
        ("frequency", float("nan"), "frequency"),
        ("frequency", float("inf"), "frequency"),
    ],
)
def test_invalid_construction(
    bond: FixedRateBond, field: str, value: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        replace(bond, **{field: value})


@pytest.mark.parametrize("frequency", [1, 2])
@pytest.mark.parametrize("ytm", [float("nan"), float("inf"), float("-inf"), -2.0, -3.0, "0.04", True])
def test_invalid_ytm_in_all_operations(frequency: int, ytm: object) -> None:
    bond = FixedRateBond(date(2025, 4, 15), date(2030, 1, 15), 0.04, frequency=frequency)
    for name in (
        "dirty_price", "clean_price", "macaulay_duration",
        "modified_duration", "convexity", "dv01", "analytics",
    ):
        with pytest.raises(ValueError, match="ytm"):
            getattr(bond, name)(ytm)


@pytest.mark.parametrize("frequency", [1, 2])
def test_yield_boundary_and_dv01_lower_shift(frequency: int) -> None:
    bond = FixedRateBond(date(2025, 1, 1), date(2026, 1, 1), 0.04, frequency=frequency)
    with pytest.raises(ValueError, match="ytm"):
        bond.dirty_price(-float(frequency))
    ytm = -frequency + 0.00005
    assert isfinite(bond.dirty_price(ytm))
    with pytest.raises(ValueError, match="ytm"):
        bond.dv01(ytm)
    with pytest.raises(ValueError, match="ytm"):
        bond.analytics(ytm)


def test_analytics_and_immutable_security(bond: FixedRateBond) -> None:
    result = bond.analytics(0.045)
    assert isinstance(result, BondAnalytics)
    assert result.ytm == 0.045
    assert result.accrued_interest == bond.accrued_interest()
    for name in (
        "dirty_price", "clean_price", "macaulay_duration",
        "modified_duration", "convexity", "dv01",
    ):
        assert getattr(result, name) == getattr(bond, name)(0.045)
    with pytest.raises(FrozenInstanceError):
        bond.coupon_rate = 0.05


def test_cli_example(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["fixed-income", "bond"])
    main()
    output = capsys.readouterr().out
    for label in (
        "Illustrative", "Settlement:", "Maturity:", "Face value:", "Coupon rate:",
        "YTM:", "Frequency:", "Accrued interest:", "Dirty price:", "Clean price:",
        "Macaulay duration:", "Modified duration:", "Convexity:", "DV01:",
        "4.50%", "0.045000 decimal", "1 bp (0.0001 decimal YTM)", "currency units",
    ):
        assert label in output


@pytest.mark.parametrize("dtype", [np.float16, np.float32, np.float64])
@pytest.mark.parametrize("frequency", [1, 2])
def test_real_scalar_inputs_preserve_financial_precision(
    dtype: type[np.floating], frequency: int,
) -> None:
    coupon_rate, face, ytm = dtype(0.06), dtype(100.1), dtype(0.04)
    bond = FixedRateBond(
        date(2024, 4, 1), date(2024, 7, 1), coupon_rate,
        face_value=face, frequency=frequency,
    )
    # One contractual payment, 91 days away. The full annual/semiannual
    # period has 366/182 days. Preserve the inputs' represented values;
    # additional arithmetic must not run in the input dtype's lower precision.
    q = 91 / (366 if frequency == 1 else 182)
    coupon = float(face) * float(coupon_rate) / frequency
    cash_flow = float(face) + coupon
    y = float(ytm)
    base = 1 + y / frequency
    price = cash_flow / base**q
    accrued = coupon * (1 - q)
    expected_dv01 = (
        cash_flow / (1 + (y - 0.0001) / frequency)**q
        - cash_flow / (1 + (y + 0.0001) / frequency)**q
    ) / 2
    expected = {
        "dirty_price": price,
        "clean_price": price - accrued,
        "macaulay_duration": q / frequency,
        "modified_duration": q / (frequency * base),
        "convexity": q * (q + 1) / (frequency * base)**2,
        "dv01": expected_dv01,
    }
    result = bond.analytics(ytm)
    assert bond.accrued_interest() == pytest.approx(accrued, rel=2e-14)
    assert result.accrued_interest == pytest.approx(accrued, rel=2e-14)
    for name, value in expected.items():
        # Absolute tolerance allows central-repricing rounding, while rejecting
        # a rounded/vanishing 1 bp shift or reduced-precision cash flows.
        assert getattr(bond, name)(ytm) == pytest.approx(value, rel=2e-13, abs=3e-14)
        assert getattr(result, name) == pytest.approx(value, rel=2e-13, abs=3e-14)
    assert expected_dv01 > 0


@pytest.mark.parametrize("field", ["face_value", "coupon_rate"])
def test_unrepresentable_real_input_is_clear(bond: FixedRateBond, field: str) -> None:
    with pytest.raises(ValueError, match=field):
        replace(bond, **{field: 10**400})


def test_unrepresentable_real_yield_is_clear(bond: FixedRateBond) -> None:
    with pytest.raises(ValueError, match="ytm"):
        bond.analytics(10**400)
