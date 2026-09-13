"""Offline fixed-income analytics with explicit decimal-rate conventions.

FixedRateBond uses nominal annual YTM compounded at coupon frequency.
NSS accepts generic rates without a bootstrap or compounding conversion.
Explicit zero-curve risk analytics are not yet implemented.
"""

from fixed_income.bonds import BondAnalytics, FixedRateBond
from fixed_income.curves import NSSCurve, NSSFitResult, fit_nss, plot_nss

__all__ = [
    "FixedRateBond", "BondAnalytics", "NSSCurve", "NSSFitResult", "fit_nss", "plot_nss",
]
