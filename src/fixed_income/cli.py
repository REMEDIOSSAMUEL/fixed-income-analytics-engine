"""Offline illustrative bond, NSS curve and continuous-zero risk CLI."""

import argparse
from datetime import date
from math import fsum
from pathlib import Path

import numpy as np

from fixed_income.bonds import FixedRateBond
from fixed_income.curves import NSSFitResult, fit_nss, plot_nss
from fixed_income.risk import (
    ZeroCurve, curve_price, evaluate_scenario, flattener_shock, key_rate_dv01,
    parallel_dv01, parallel_shock, steepener_shock,
)


def _load_curve() -> NSSFitResult:
    source = Path("examples") / "illustrative_curve.csv"
    data = np.genfromtxt(source, delimiter=",", names=True)
    return fit_nss(data["maturity_years"], data["rate"])


def _curve_example() -> NSSFitResult:
    result = _load_curve()
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
    return result


def _risk_example(curve: ZeroCurve | None = None) -> None:
    if curve is None:
        curve = _load_curve().curve
    bond = FixedRateBond(date(2025, 4, 15), date(2055, 1, 15), coupon_rate=0.04)
    print("Illustrative curve-risk example (invented; no market data)")
    print("Fitted rates are interpreted as continuously compounded zero rates")
    print("for this educational example; NSS fitting does not bootstrap par yields.")
    print("Time convention: Actual/365 = actual calendar days from settlement / 365.0")
    print(f"Settlement: {bond.settlement_date}; maturity: {bond.maturity_date}")
    print(f"Face value: {bond.face_value:.2f}; coupon: {bond.coupon_rate:.2%} annual; semiannual")
    print("All prices, P&L and DV01s are currency amounts for this face value.")
    print(f"Base zero-curve price: {curve_price(bond, curve):.8f} (dirty)")
    for name, shock in (
        ("Parallel +25 bp", parallel_shock(25)),
        ("Parallel -25 bp", parallel_shock(-25)),
        ("Steepener (2/10/30Y: -10/0/+10 bp)", steepener_shock()),
        ("Flattener (2/10/30Y: +10/0/-10 bp)", flattener_shock()),
    ):
        result = evaluate_scenario(bond, curve, shock, name)
        print(f"{result.name}: base={result.base_price:.8f}, "
              f"shocked={result.shocked_price:.8f}, P&L={result.pnl:+.8f}")
    sensitivities = key_rate_dv01(bond, curve)
    for item in sensitivities:
        print(f"{item.tenor_years:g}Y KRDV01: {item.dv01:.10f}")
    parallel = parallel_dv01(bond, curve)
    total = fsum(item.dv01 for item in sensitivities)
    print(f"Parallel DV01: {parallel:.10f}")
    print(f"Sum of KRDV01: {total:.10f}")
    print(f"Reconciliation difference (sum - parallel): {total - parallel:+.12e}")
    print("DV01 uses [P(-1 bp) - P(+1 bp)]/2; 1 bp = 0.0001 decimal zero rate.")


def _bond_example() -> None:
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


def main() -> None:
    """Print help or deterministic offline examples of the three capabilities."""
    parser = argparse.ArgumentParser(
        description="Educational fixed-income analytics with decimal-rate inputs."
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("bond", help="Show an illustrative fixed-rate bond example")
    commands.add_parser("curve", help="Fit NSS to the invented offline curve CSV")
    commands.add_parser("risk", help="Reprice an illustrative bond under zero-curve shocks")
    commands.add_parser("demo", help="Run bond, curve and risk examples in order")
    args = parser.parse_args()
    if args.command == "bond":
        _bond_example()
    elif args.command == "curve":
        _curve_example()
    elif args.command == "risk":
        _risk_example()
    elif args.command == "demo":
        _bond_example()
        print()
        fit = _curve_example()
        print()
        _risk_example(fit.curve)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
