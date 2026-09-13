"""Explicit continuous-zero valuation and deterministic curve risk.

All rates are annual decimals. Curve times use actual settlement-to-payment
calendar days / 365.0, a simplified project convention. Shock factories accept
basis points once; returned functions produce decimal changes. No YTM pricing,
bootstrap, elapsed-time carry, or cash-flow changes enter these calculations.
"""

from collections.abc import Callable
from dataclasses import dataclass
from math import exp, fsum, isfinite
from numbers import Real
from typing import Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray

from fixed_income.bonds import FixedRateBond


class ZeroCurve(Protocol):
    """Return a continuous annual decimal zero rate at scalar positive years.

    A scalar float or zero-dimensional NumPy array is accepted. NSSCurve can be
    supplied directly only when the caller explicitly interprets its rates as
    continuous zero rates. This interface performs no bootstrap or conversion.
    """

    def yield_rate(self, maturity_years: float) -> float | NDArray[np.float64]:
        """Continuous annual decimal zero rate at positive maturity in years."""
        ...


def _scalar(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    return float(value)


def _maturity(value: float) -> float:
    maturity = _scalar(value, "maturity_years")
    if maturity <= 0:
        raise ValueError("maturity_years must be strictly positive")
    return maturity


def _array(values: ArrayLike, name: str) -> NDArray[np.float64]:
    array = np.asarray(values)
    if array.dtype.kind not in "iuf" or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain finite real numbers")
    return np.asarray(array, dtype=float)


def _tenors(values: ArrayLike) -> NDArray[np.float64]:
    tenors = _array(values, "tenors")
    if tenors.ndim != 1 or tenors.size == 0:
        raise ValueError("tenors must be a nonempty 1D array")
    if np.any(tenors <= 0) or np.any(tenors[1:] <= tenors[:-1]):
        raise ValueError("tenors must be positive and strictly increasing")
    return tenors.copy()


def _zero_rate(curve: ZeroCurve, maturity: float) -> float:
    value = _array(curve.yield_rate(maturity), "zero rate")
    if value.ndim != 0:
        raise ValueError("zero rate must be scalar for a scalar maturity")
    return float(value)


@dataclass(frozen=True)
class ShockedCurve:
    """Add a decimal shock callable to a continuous-zero base curve.

    shock(t) returns a finite decimal change at positive years, NOT basis points.
    The base curve is retained by reference and never mutated by this wrapper.
    Caller-provided curves and shock callables must themselves be deterministic.
    """

    base_curve: ZeroCurve
    shock: Callable[[float], float]

    def yield_rate(self, maturity_years: float) -> float:
        """Shocked continuous annual decimal zero rate at positive years."""
        t = _maturity(maturity_years)
        change = _scalar(self.shock(t), "decimal shock")
        return _scalar(_zero_rate(self.base_curve, t) + change, "shocked zero rate")


@dataclass(frozen=True)
class ScenarioResult:
    """Instantaneous dirty-price scenario; all amounts use the bond's face value.

    pnl = shocked_price - base_price, in currency units, with unchanged cash
    flows and settlement. No accrual carry, transaction costs or passage of time.
    """

    name: str
    base_price: float
    shocked_price: float

    @property
    def pnl(self) -> float:
        """Currency P&L: shocked price minus base price."""
        return self.shocked_price - self.base_price


@dataclass(frozen=True)
class KeyRateDV01:
    """Key tenor in years and positive currency DV01 for a 1 bp basis move."""

    tenor_years: float
    dv01: float


def curve_price(bond: FixedRateBond, curve: ZeroCurve) -> float:
    """Dirty currency price: sum CF * exp(-r(t)*t), continuous decimal zeros.

    Reuse the bond's future coupon schedule, excluding any settlement-date
    payment. Each coupon is face_value*coupon_rate/frequency, with principal
    added at maturity. t is actual calendar days after settlement / 365.0.
    This simplified Actual/365 convention is not a universal market convention.
    No YTM formula or accrued-interest subtraction is used. Negative zero rates
    are supported; nonfinite or unrepresentable positive prices raise ValueError.
    """
    coupon = bond.face_value * bond.coupon_rate / bond.frequency
    present_values = []
    try:
        for payment_date in bond.coupon_schedule():
            cash_flow = coupon
            if payment_date == bond.maturity_date:
                cash_flow += bond.face_value
            if cash_flow == 0:
                continue
            t = (payment_date - bond.settlement_date).days / 365.0
            rate = _zero_rate(curve, t)
            discount = exp(-rate * t)
            pv = cash_flow * discount
            if not isfinite(pv) or pv <= 0:
                raise ValueError("zero curve produces a price outside positive floating-point range")
            present_values.append(pv)
        price = fsum(present_values)
    except OverflowError as exc:
        raise ValueError("zero curve produces a price outside positive floating-point range") from exc
    if not isfinite(price) or price <= 0:
        raise ValueError("zero curve must produce a finite positive price")
    return price


def parallel_shock(shift_bps: float) -> Callable[[float], float]:
    """Return s(t) in decimals for a parallel shift supplied in bp (1 bp=0.0001)."""
    shift = _scalar(shift_bps, "shift_bps") * 0.0001

    def shock(maturity_years: float) -> float:
        _maturity(maturity_years)
        return shift

    return shock


def piecewise_linear_shock(
    anchor_years: ArrayLike, shifts_bps: ArrayLike,
) -> Callable[[float], float]:
    """Return a decimal shock s(t) from sorted positive years and bp anchors.

    Require nonempty 1D arrays of identical length and finite real values;
    anchor years must be strictly increasing. Interpolate linearly between
    anchors and hold the nearest endpoint shock flat in both tails. One anchor
    defines a constant shock. Inputs are copied; bp convert to decimals once.
    """
    anchors = _tenors(anchor_years)
    shifts = _array(shifts_bps, "shifts_bps")
    if shifts.ndim != 1 or shifts.size != anchors.size:
        raise ValueError("shifts_bps must be 1D with the same length as anchor years")
    decimal_shifts = shifts.copy() * 0.0001

    def shock(maturity_years: float) -> float:
        t = _maturity(maturity_years)
        return float(np.interp(t, anchors, decimal_shifts))

    return shock


def steepener_shock(
    anchor_years: ArrayLike = (2.0, 10.0, 30.0),
    shifts_bps: ArrayLike = (-10.0, 0.0, 10.0),
) -> Callable[[float], float]:
    """Illustrative steepener: -10/0/+10 bp at 2/10/30 years; accepts custom anchors.

    Returned shocks are decimals; interpolation and tails follow
    piecewise_linear_shock. This is not a universal steepener definition.
    """
    return piecewise_linear_shock(anchor_years, shifts_bps)


def flattener_shock(
    anchor_years: ArrayLike = (2.0, 10.0, 30.0),
    shifts_bps: ArrayLike = (10.0, 0.0, -10.0),
) -> Callable[[float], float]:
    """Illustrative flattener: +10/0/-10 bp at 2/10/30 years; accepts custom anchors.

    Returned shocks are decimals; interpolation and tails follow
    piecewise_linear_shock. This is not a universal flattener definition.
    """
    return piecewise_linear_shock(anchor_years, shifts_bps)


def evaluate_scenario(
    bond: FixedRateBond, curve: ZeroCurve, shock: Callable[[float], float], name: str,
) -> ScenarioResult:
    """Fully reprice a decimal shock to continuous zeros; currency P&L is new-old.

    Use the bp-accepting shock factories for convenient unit conversion.
    Cash flows and Actual/365 times are unchanged; the base curve is not mutated.
    """
    return ScenarioResult(name, curve_price(bond, curve), curve_price(bond, ShockedCurve(curve, shock)))


def key_rate_basis(
    maturity_years: ArrayLike, key_tenors: ArrayLike = (2.0, 5.0, 10.0, 30.0),
) -> NDArray[np.float64]:
    """Dimensionless linear key weights, shape (*maturity_shape, number_of_keys).

    Maturities are finite positive years. Keys are nonempty, positive, finite,
    strictly increasing years. At keys the weights are the identity matrix;
    between keys only the neighboring weights are nonzero. The first/last
    weight is one in the respective tail. Weights sum to one everywhere.
    A single key has weight one at every positive maturity.
    """
    keys = _tenors(key_tenors)
    maturities = _array(maturity_years, "maturities")
    if np.any(maturities <= 0):
        raise ValueError("maturities must be strictly positive")
    identity = np.eye(keys.size)
    return np.stack([np.interp(maturities, keys, row) for row in identity], axis=-1)


def key_rate_dv01(
    bond: FixedRateBond, curve: ZeroCurve,
    key_tenors: ArrayLike = (2.0, 5.0, 10.0, 30.0),
) -> tuple[KeyRateDV01, ...]:
    """Currency KRDV01 per key: [P(-1 bp*basis_i) - P(+1 bp*basis_i)]/2.

    Keys are sorted positive years; defaults are 2/5/10/30. Full continuous-zero
    repricing uses Actual/365 times. Results retain key order. The sum reconciles
    approximately to parallel_dv01; independent nonlinear repricing introduces
    cubic (in the decimal bump) differences despite partition of unity.
    """
    keys = _tenors(key_tenors)
    results = []
    for key, weights in zip(keys, np.eye(keys.size), strict=True):
        # Values at keys are +/-1 BP, converted only inside the shock factory.
        minus = ShockedCurve(curve, piecewise_linear_shock(keys, -weights))
        plus = ShockedCurve(curve, piecewise_linear_shock(keys, weights))
        dv01 = (curve_price(bond, minus) - curve_price(bond, plus)) / 2
        results.append(KeyRateDV01(float(key), dv01))
    return tuple(results)


def parallel_dv01(bond: FixedRateBond, curve: ZeroCurve) -> float:
    """Currency DV01: [P(curve-1 bp) - P(curve+1 bp)]/2, full zero repricing.

    Rates are continuous annual decimals, times Actual/365 years. The fixed
    1 bp bump converts to 0.0001 once inside parallel_shock.
    """
    minus = ShockedCurve(curve, parallel_shock(-1.0))
    plus = ShockedCurve(curve, parallel_shock(1.0))
    return (curve_price(bond, minus) - curve_price(bond, plus)) / 2
