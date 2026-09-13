"""Offline illustrative fixed-rate bond analytics command line interface."""

import argparse
from datetime import date

from fixed_income.bonds import FixedRateBond


def main() -> None:
    """Print help or deterministic illustrative bond analytics."""
    parser = argparse.ArgumentParser(
        description="Educational fixed-income analytics with decimal-rate inputs."
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("bond", help="Show an illustrative fixed-rate bond example")
    args = parser.parse_args()
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
