"""Offline fixed-income analytics with explicit decimal-rate conventions.

FixedRateBond uses nominal annual YTM compounded at coupon frequency.
NSS and explicit zero-curve risk analytics are not yet implemented.
"""

from fixed_income.bonds import BondAnalytics, FixedRateBond

__all__ = ["FixedRateBond", "BondAnalytics"]
