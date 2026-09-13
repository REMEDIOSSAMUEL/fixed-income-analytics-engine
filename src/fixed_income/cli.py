"""Offline illustrative bond and NSS curve command line interface."""

import argparse
from datetime import date
from pathlib import Path

import numpy as np

from fixed_income.bonds import FixedRateBond
from fixed_income.curves import fit_nss, plot_nss


def _curve_example() -> None:
    """Fit the invented repository CSV (decimal rates, maturities in years)."""
    source = Path("examples") / "illustrative_curve.csv"
    data = np.genfromtxt(source, delimiter=",", names=True)
    result = fit_nss(data["maturity_years"], data["rate"])
    print("Illustrative NSS curve example (invented; no market data)")
    print("Generic decimal rates; no implied compounding convention.")
    print("This is not a bootstrapped zero curve.")
    for name in ("beta0", "beta1", "beta2", "beta3"):
        print(f"{name}: {getattr(result.curve, name):.10f} decimal rate")
    for name in ("tau1", "tau2"):
        print(f"{name}: {getattr(result.curve, name):.10f} years")
    print(f"Optimizer success: {result.success}")
    print(f"Optimizer status: {result.status} ({result.message})")
    print(f"Function evaluations (selected start): {result.nfev}")
    print(f"Successful starts: {result.starts_succeeded}/{result.starts_attempted}")
    print(f"RMSE (decimal rate): {result.rmse:.10f}")
    print(f"RMSE (basis points): {result.rmse_bps:.6f}")
    destination = Path("outputs") / "yield_curve.png"
    plot_nss(result.maturities, result.observed_rates, result.curve, destination)
    print(f"Plot: {destination}")


def main() -> None:
    """Print help or deterministic illustrative bond/curve analytics."""
    parser = argparse.ArgumentParser(
        description="Educational fixed-income analytics with decimal-rate inputs."
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("bond", help="Show an illustrative fixed-rate bond example")
    commands.add_parser("curve", help="Fit NSS to the invented offline curve CSV")
    args = parser.parse_args()
    if args.command == "curve":
        _curve_example()
        return
    if args.command != "bond":
        parser.print_help()
        return

    bond = FixedRateBond(date(2025, 4, 15), date(2030, 1, 15), coupon_rate=0.04)
    ytm = 0.045
    result = bond.analytics(ytm)
    print("Illustrative fixed-rate bond example (invented; no market data)")
    print("YTM convention: nominal annual, compounded at coupon frequency")
    print("Currency amounts are for the displayed face value.")
    print(f"Settlement: {bond.settlement_date.isoformat()}")
    print(f"Maturity: {bond.maturity_date.isoformat()}")
    print(f"Face value: {bond.face_value:.2f} currency units")
    print(f"Coupon rate: {bond.coupon_rate:.2%} annual ({bond.coupon_rate:.6f} decimal)")
    print(f"YTM: {ytm:.2%} annual ({ytm:.6f} decimal)")
    print(f"Frequency: {bond.frequency} payments/year (semiannual)")
    print(f"Accrued interest: {result.accrued_interest:.6f} currency units")
    print(f"Dirty price: {result.dirty_price:.6f} currency units")
    print(f"Clean price: {result.clean_price:.6f} currency units")
    print(f"Macaulay duration: {result.macaulay_duration:.6f} years")
    print(f"Modified duration: {result.modified_duration:.6f} years")
    print(f"Convexity: {result.convexity:.6f} years squared (P''(y)/P; decimal YTM)")
    print(f"DV01: {result.dv01:.6f} currency units for 1 bp (0.0001 decimal YTM)")
    print("DV01 convention: [dirty P(y - 1 bp) - dirty P(y + 1 bp)] / 2")


if __name__ == "__main__":
    main()
