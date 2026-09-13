"""Independent continuous discounting and deterministic curve-risk invariants."""

from dataclasses import asdict, dataclass, replace
from datetime import date, timedelta
from math import cosh, exp, fsum, isfinite, sinh
from pathlib import Path

import numpy as np
import pytest

from fixed_income import (
    FixedRateBond, NSSCurve, KeyRateDV01, ScenarioResult, ShockedCurve,
    curve_price, evaluate_scenario, flattener_shock, key_rate_basis,
    key_rate_dv01, parallel_dv01, parallel_shock, piecewise_linear_shock,
    steepener_shock,
)
from fixed_income.cli import main


@dataclass(frozen=True)
class FlatZero:
    rate: float = 0.04

    def yield_rate(self, maturity_years: float) -> float:
        return self.rate


@pytest.fixture
def bond() -> FixedRateBond:
    return FixedRateBond(date(2025, 4, 15), date(2055, 1, 15), 0.04)


@pytest.fixture
def curve() -> NSSCurve:
    # Caller explicitly interprets these illustrative rates as continuous zeros.
    return NSSCurve(0.04, -0.015, 0.02, -0.006, 1.5, 7)


@pytest.mark.parametrize("frequency", [1, 2])
@pytest.mark.parametrize("rate", [-0.01, 0.0, 0.045])
def test_flat_zero_price_independent(frequency: int, rate: float) -> None:
    bond = FixedRateBond(date(2024, 4, 1), date(2025, 7, 1), 0.06, frequency=frequency)
    # Explicit calendar dates: includes leap-year settlement and partial period.
    dates = [date(2024, 7, 1), date(2025, 7, 1)]
    if frequency == 2:
        dates.insert(1, date(2025, 1, 1))
    cash_flows = [100 * 0.06 / frequency] * len(dates)
    cash_flows[-1] += 100
    expected = fsum(
        cf * exp(-rate * (payment - date(2024, 4, 1)).days / 365.0)
        for payment, cf in zip(dates, cash_flows, strict=True)
    )
    actual = curve_price(bond, FlatZero(rate))
    assert isfinite(actual) and actual > 0
    assert actual == pytest.approx(expected, rel=2e-15)


def test_settlement_coupon_excluded_and_ytm_not_used(monkeypatch: pytest.MonkeyPatch) -> None:
    bond = FixedRateBond(date(2024, 7, 1), date(2025, 7, 1), 0.06)
    def forbidden(*args: object) -> float:
        raise AssertionError("Zero pricing must not invoke YTM discounting")
    monkeypatch.setattr(FixedRateBond, "_present_values", forbidden)
    expected = 3 * exp(-0.04 * 184 / 365) + 103 * exp(-0.04)
    assert curve_price(bond, FlatZero()) == pytest.approx(expected, rel=2e-15)


def test_zero_coupon_actual365_leap_year() -> None:
    bond = FixedRateBond(date(2024, 1, 1), date(2025, 1, 1), 0)
    assert curve_price(bond, FlatZero()) == pytest.approx(100 * exp(-0.04 * 366 / 365))
    assert curve_price(bond, FlatZero()) != pytest.approx(100 * exp(-0.04), rel=1e-6)


def test_nss_explicit_zero_price(bond: FixedRateBond, curve: NSSCurve) -> None:
    assert isfinite(curve_price(bond, curve))
    assert curve_price(bond, curve) > 0


@pytest.mark.parametrize("shift", [-25.0, 0.0, 25.0])
def test_parallel_scenario_sign_units_and_pnl(bond: FixedRateBond, shift: float) -> None:
    base = FlatZero()
    shock = parallel_shock(shift)
    result = evaluate_scenario(bond, base, shock, f"{shift:+g} bp")
    assert isinstance(result, ScenarioResult)
    assert result.name == f"{shift:+g} bp"
    assert shock(3.0) == shift * 0.0001
    assert result.base_price == curve_price(bond, base)
    expected = curve_price(bond, FlatZero(0.04 + shift * 0.0001))
    assert result.shocked_price == pytest.approx(expected, rel=2e-15)
    assert result.pnl == result.shocked_price - result.base_price
    if shift > 0:
        assert result.pnl < 0
    elif shift < 0:
        assert result.pnl > 0
    else:
        assert result.pnl == pytest.approx(0, abs=1e-13)


def test_piecewise_anchors_midpoints_and_tails() -> None:
    shock = piecewise_linear_shock([2, 10, 30], [-10, 0, 20])
    for t, bp in [(0.01, -10), (2, -10), (6, -5), (10, 0), (20, 10), (30, 20), (60, 20)]:
        assert shock(t) == bp * 0.0001


def test_shock_copies_inputs() -> None:
    anchors = np.array([2.0, 10.0, 30.0])
    shifts = np.array([-10.0, 0.0, 10.0])
    shock = piecewise_linear_shock(anchors, shifts)
    anchors[:] = 1
    shifts[:] = 99
    assert shock(2) == -0.001
    assert shock(30) == 0.001


@pytest.mark.parametrize(
    ("factory", "expected"),
    [(steepener_shock, [-0.001, 0, 0.001]), (flattener_shock, [0.001, 0, -0.001])],
)
def test_default_and_custom_shapes(factory: object, expected: list[float]) -> None:
    shock = factory()
    assert [shock(t) for t in (2, 10, 30)] == expected
    custom = factory([1, 5, 20], [-5, 3, 12])
    assert [custom(t) for t in (1, 5, 20)] == [v * 0.0001 for v in (-5, 3, 12)]


def test_key_basis_identity_midpoints_and_tails() -> None:
    keys = np.array([2, 5, 10, 30])
    np.testing.assert_array_equal(key_rate_basis(keys), np.eye(4))
    np.testing.assert_array_equal(key_rate_basis(0.01), [1, 0, 0, 0])
    np.testing.assert_array_equal(key_rate_basis(60), [0, 0, 0, 1])
    for i, midpoint in enumerate((3.5, 7.5, 20)):
        expected = np.zeros(4)
        expected[i:i+2] = 0.5
        np.testing.assert_array_equal(key_rate_basis(midpoint), expected)


def test_partition_of_unity_every_region() -> None:
    maturities = np.array([
        1e-10, 0.2, 1, 2, 2.3, 3.5, 4.9, 5, 5.1, 7.5, 9.7,
        10, 10.2, 15, 20, 25, 29.9, 30, 31, 60, 1000,
    ])
    weights = key_rate_basis(maturities)
    assert weights.shape == (maturities.size, 4)
    assert np.all(weights >= 0) and np.all(weights <= 1)
    np.testing.assert_allclose(weights.sum(axis=-1), 1, rtol=0, atol=2e-16)
    shaped = key_rate_basis(np.array([[1, 3], [20, 50]]))
    assert shaped.shape == (2, 2, 4)


@pytest.mark.parametrize("keys", [(1, 3, 7, 15, 40), (5,), (0.5, 2)])
def test_custom_keys_and_single_anchor(bond: FixedRateBond, keys: tuple[float, ...]) -> None:
    np.testing.assert_array_equal(key_rate_basis(keys, keys), np.eye(len(keys)))
    weights = key_rate_basis([0.01, 1, 2.5, 6, 20, 100], keys)
    np.testing.assert_allclose(weights.sum(axis=-1), 1, rtol=0, atol=2e-16)
    result = key_rate_dv01(bond, FlatZero(), keys)
    assert tuple(item.tenor_years for item in result) == keys
    assert all(item.dv01 >= 0 for item in result)
    if len(keys) == 1:
        assert result[0].dv01 == parallel_dv01(bond, FlatZero())
        assert piecewise_linear_shock(keys, [25])(100) == 0.0025


def test_individual_dv01_against_single_cash_flow() -> None:
    settlement = date(2025, 1, 1)
    bond = FixedRateBond(settlement, settlement + timedelta(days=365 * 20), 0)
    base = 100 * exp(-0.04 * 20)
    result = key_rate_dv01(bond, FlatZero())
    # 20 years is halfway between 10Y and 30Y: only those two bases have weight.
    expected = base * sinh(0.0001 * 20 * 0.5)
    assert [item.dv01 for item in result[:2]] == [0, 0]
    for item in result[2:]:
        assert isinstance(item, KeyRateDV01)
        assert item.dv01 == pytest.approx(expected, rel=2e-12, abs=1e-13)
    assert parallel_dv01(bond, FlatZero()) == pytest.approx(
        base * sinh(0.0001 * 20), rel=2e-12, abs=1e-13
    )


@pytest.mark.parametrize("keys", [(2, 5, 10, 30), (1, 3, 7, 15, 40)])
def test_dv01_reconciliation_with_derived_bound(
    bond: FixedRateBond, curve: NSSCurve, keys: tuple[float, ...],
) -> None:
    sensitivities = key_rate_dv01(bond, curve, keys)
    parallel = parallel_dv01(bond, curve)
    total = fsum(item.dv01 for item in sensitivities)
    assert all(item.dv01 >= -1e-13 for item in sensitivities)
    assert parallel > 0
    # Each central difference is sum PV*sinh(h*t*w).
    # Partition of unity cancels linear terms. With 0<=w<=1, the remaining
    # difference is nonnegative and <= sum PV*(h*t)^3*cosh(h*t)/6.
    # Compare also to the leading cubic term, bounding O((h*t)^5) explicitly.
    upper_bound = 0.0
    cubic = 0.0
    fifth_bound = 0.0
    for payment in bond.coupon_schedule():
        t = (payment - bond.settlement_date).days / 365.0
        cf = bond.face_value * bond.coupon_rate / bond.frequency
        if payment == bond.maturity_date:
            cf += bond.face_value
        pv = cf * exp(-curve.yield_rate(t) * t)
        z = 0.0001 * t
        w = key_rate_basis(t, keys)
        upper_bound += pv * z**3 * cosh(z) / 6
        cubic += pv * z**3 * (1 - np.sum(w**3)) / 6
        fifth_bound += pv * z**5 * cosh(z) / 120
    rounding = 64 * np.finfo(float).eps * curve_price(bond, curve) * len(keys)
    difference = parallel - total
    assert -rounding <= difference <= upper_bound + rounding
    assert abs(difference - cubic) <= fifth_bound + rounding
    assert total == pytest.approx(parallel, rel=0, abs=upper_bound + rounding)


def test_no_base_mutation_and_face_scaling(bond: FixedRateBond, curve: NSSCurve) -> None:
    before = asdict(curve)
    points = np.array([0.2, 2, 7, 20, 40])
    values = curve.yield_rate(points).copy()
    for shock in (parallel_shock(25), parallel_shock(-25), steepener_shock(), flattener_shock()):
        evaluate_scenario(bond, curve, shock, "test")
    sensitivities = key_rate_dv01(bond, curve)
    parallel = parallel_dv01(bond, curve)
    assert asdict(curve) == before
    np.testing.assert_array_equal(curve.yield_rate(points), values)
    larger = replace(bond, face_value=1000)
    assert curve_price(larger, curve) == pytest.approx(10 * curve_price(bond, curve))
    assert parallel_dv01(larger, curve) == pytest.approx(10 * parallel, rel=1e-11)
    np.testing.assert_allclose(
        [item.dv01 for item in key_rate_dv01(larger, curve)],
        [10 * item.dv01 for item in sensitivities], rtol=1e-10, atol=1e-12,
    )


@pytest.mark.parametrize("keys", [[], [2, 2], [5, 2], [0, 5], [-1, 5], [1, np.nan], [1, np.inf], [[2, 5]], [True], ["2"]])
def test_invalid_keys_and_anchors(bond: FixedRateBond, keys: object) -> None:
    with pytest.raises(ValueError, match="tenors"):
        key_rate_basis(3, keys)
    with pytest.raises(ValueError, match="tenors"):
        key_rate_dv01(bond, FlatZero(), keys)
    with pytest.raises(ValueError, match="tenors"):
        piecewise_linear_shock(keys, [1, 2])


@pytest.mark.parametrize("shifts", [[], [1], [[1, 2]], [1, np.nan], [1, np.inf], [1j, 2], ["1", "2"]])
def test_invalid_anchor_shifts(shifts: object) -> None:
    with pytest.raises(ValueError, match="shifts_bps"):
        piecewise_linear_shock([2, 5], shifts)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf, True, "25", 1j])
def test_invalid_parallel_shifts(value: object) -> None:
    with pytest.raises(ValueError, match="shift_bps"):
        parallel_shock(value)


@pytest.mark.parametrize("value", [0, -1, np.nan, np.inf, True])
def test_invalid_evaluation_maturities(value: object) -> None:
    for shock in (parallel_shock(25), steepener_shock(), flattener_shock()):
        with pytest.raises(ValueError, match="maturity"):
            shock(value)
    with pytest.raises(ValueError, match="maturities"):
        key_rate_basis(value)
    with pytest.raises(ValueError, match="maturity"):
        ShockedCurve(FlatZero(), parallel_shock(25)).yield_rate(value)


@pytest.mark.parametrize("rate", [np.nan, np.inf, -np.inf, True, [0.04], 10000, -10000])
def test_invalid_curve_outputs_or_price_range(bond: FixedRateBond, rate: object) -> None:
    with pytest.raises(ValueError, match="zero|price"):
        curve_price(bond, FlatZero(rate))


def test_invalid_decimal_shock(bond: FixedRateBond) -> None:
    with pytest.raises(ValueError, match="decimal shock"):
        curve_price(bond, ShockedCurve(FlatZero(), lambda t: np.nan))


@pytest.mark.parametrize("command", ["risk", "demo"])
def test_risk_and_demo_cli(
    command: str, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], tmp_path: Path,
) -> None:
    source = Path(__file__).resolve().parents[1] / "examples" / "illustrative_curve.csv"
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / source.name).write_bytes(source.read_bytes())
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["fixed-income", command])
    main()
    output = capsys.readouterr().out
    for label in (
        "Illustrative curve-risk example", "invented", "continuously compounded zero rates",
        "educational", "Actual/365", "Base zero-curve price:", "+25 bp", "-25 bp",
        "Steepener", "Flattener", "2Y KRDV01:", "5Y KRDV01:", "10Y KRDV01:",
        "30Y KRDV01:", "Parallel DV01:", "Sum of KRDV01:", "Reconciliation difference",
    ):
        assert label in output
    if command == "demo":
        assert output.index("Illustrative fixed-rate bond") < output.index("Illustrative NSS")
        assert output.index("Illustrative NSS") < output.index("Illustrative curve-risk")
        assert (tmp_path / "outputs" / "yield_curve.png").is_file()
