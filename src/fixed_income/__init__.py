"""Offline fixed-income analytics with explicit decimal-rate conventions.

FixedRateBond uses nominal annual YTM compounded at coupon frequency.
NSS accepts generic rates without a bootstrap or compounding conversion.
Risk uses explicitly interpreted continuous annual zero rates and Actual/365 times.
"""

from fixed_income.bonds import BondAnalytics, FixedRateBond
from fixed_income.curves import NSSCurve, NSSFitResult, fit_nss, plot_nss

from fixed_income.risk import (
    KeyRateDV01, ScenarioResult, ShockedCurve, ZeroCurve, curve_price,
    evaluate_scenario, flattener_shock, key_rate_basis, key_rate_dv01,
    parallel_dv01, parallel_shock, piecewise_linear_shock, steepener_shock,
)

__all__ = [
    "FixedRateBond", "BondAnalytics", "NSSCurve", "NSSFitResult", "fit_nss", "plot_nss",
    "ZeroCurve", "ShockedCurve", "ScenarioResult", "KeyRateDV01", "curve_price",
    "evaluate_scenario", "parallel_shock", "piecewise_linear_shock",
    "steepener_shock", "flattener_shock", "key_rate_basis",
    "key_rate_dv01", "parallel_dv01",
]
