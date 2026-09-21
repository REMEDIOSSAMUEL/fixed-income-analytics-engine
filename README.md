# Fixed-income analytics engine

An offline Python 3.12+ library for three related tasks:

- fixed-rate bond pricing and yield analytics;
- Nelson-Siegel-Svensson (NSS) curve fitting; and
- deterministic interest-rate and curve-risk calculations.

The project uses invented example data and is intended for education and
research. It is not a production pricing or trading system. The accompanying
[dissertation](paper/fixed_income_analytics_dissertation.pdf) contains the
derivations, numerical results, and fuller discussion of the modelling choices.

## Setup

From the repository root in Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -c "import fixed_income; print(fixed_income.__file__)"
```

Use a later installed Python version if appropriate. Dependencies are declared
but not locked, so results are reproducible within a given numerical environment
rather than bit-for-bit across every NumPy and SciPy release.

## Examples

The CLI exposes fixed, deterministic examples rather than a general command-line
interface:

```powershell
.\.venv\Scripts\python.exe -m fixed_income.cli --help
.\.venv\Scripts\python.exe -m fixed_income.cli bond
.\.venv\Scripts\python.exe -m fixed_income.cli curve
.\.venv\Scripts\python.exe -m fixed_income.cli risk
.\.venv\Scripts\python.exe -m fixed_income.cli demo
```

`curve`, `risk`, and `demo` read `examples/illustrative_curve.csv` relative to
the current working directory, so run them from the repository root. `curve`
and `demo` write `outputs/yield_curve.png`; the `outputs` directory is ignored
by Git. The CSV contains invented decimal rates and carries no implied
compounding or zero-rate convention.

## Conventions

Rates are decimal values in the Python API: `0.05` means 5%, and `0.0001` means
one basis point. Currency results use the bond's face value, which defaults to
100. Bond YTM pricing and explicit zero-curve discounting are separate
calculations with different compounding and time conventions.

### Fixed-rate bonds

`FixedRateBond` represents an option-free bond with regular annual or
semiannual coupons. It is an immutable dataclass with these fields:

- `settlement_date` and `maturity_date`: `datetime.date` values;
- `coupon_rate`: nonnegative annual decimal rate;
- `face_value`: positive currency amount, default `100.0`; and
- `frequency`: `1` for annual or `2` for semiannual payments.

Coupon dates are generated backwards from maturity in 12- or 6-month steps.
Nonexistent dates clip to month end, but there is no separate end-of-month,
holiday, business-day, irregular-coupon, or ex-coupon convention. A payment on
the settlement date is excluded and accrued interest is zero at that boundary.
Between coupon dates, accrual is the actual elapsed days divided by the actual
days in that coupon period.

YTM is a nominal annual decimal yield compounded at coupon frequency. If
`alpha` is the accrued fraction, the first future payment is `1 - alpha` coupon
periods away. For periodic coupon `C`, frequency `m`, annual YTM `y`, and future
cash flows `CF_i`:

```text
q_i = 1 - alpha + i - 1
PV_i = CF_i * (1 + y/m)^(-q_i)
dirty price = sum(PV_i)
clean price = dirty price - accrued interest
```

The supported analytics are dirty and clean price, Macaulay and modified
duration, convexity, and DV01. Durations are in years. Convexity is the
dirty-price-normalised second derivative with respect to annual decimal YTM,
conventionally expressed in years squared. DV01 is a currency amount calculated
by full central repricing:

```text
DV01 = [P(y - 0.0001) - P(y + 0.0001)] / 2
```

```python
from datetime import date

from fixed_income import FixedRateBond

bond = FixedRateBond(
    settlement_date=date(2025, 4, 15),
    maturity_date=date(2030, 1, 15),
    coupon_rate=0.04,
)
analytics = bond.analytics(ytm=0.045)
print(analytics.clean_price)
print(analytics.dv01)
```

Zero coupons and negative yields are supported while
`1 + ytm / frequency > 0`. Inputs and computed prices must remain finite. There
is no yield solver or explicit zero-curve discounting in the bond methods.

### NSS curves

`NSSCurve` stores four beta coefficients as decimal rates and two positive tau
parameters in years. It evaluates

```text
L1(x) = (1 - exp(-x)) / x
L2(x) = L1(x) - exp(-x)
y(t) = beta0 + beta1*L1(t/tau1)
                 + beta2*L2(t/tau1)
                 + beta3*L2(t/tau2)
```

at finite positive maturities in years. Scalars return a Python `float`; NumPy
inputs retain their shape. Stable short-maturity expansions avoid cancellation
in the factor loadings.

`fit_nss` performs deterministic, unweighted least squares. It requires 1D
inputs with equal lengths and at least six distinct positive maturities. Six
fixed tau starting pairs seed linear beta estimates before joint nonlinear
fits. Betas are unbounded and taus are constrained to `[0.01, 100]` years. The
lowest-error successful candidate is returned with fitted rates, residuals,
decimal-rate RMSE, basis-point RMSE, and optimizer metadata. Result arrays are
independent, read-only copies in the original observation order.

```python
from pathlib import Path

import numpy as np

from fixed_income import NSSCurve, fit_nss, plot_nss

maturities = np.array([0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])
known = NSSCurve(0.04, -0.025, 0.03, -0.012, 1.4, 6.5)
observed_rates = known.yield_rate(maturities)

fit = fit_nss(maturities, observed_rates)
print(fit.rmse_bps)
plot_nss(maturities, observed_rates, fit.curve, Path("outputs/synthetic.png"))
```

The NSS API preserves the caller's rate convention. It does not bootstrap,
convert compounding, or turn par/CMT-style yields into zero rates. Calibration
can have local minima and weakly identified parameters; deterministic
multi-start fitting does not guarantee a unique or global optimum.

### Zero-curve valuation and risk

The risk API expects a curve whose `yield_rate(t)` method returns a finite,
continuously compounded annual zero rate in decimal units at positive maturity
`t`. `NSSCurve` satisfies the interface mechanically, but it is appropriate only
when the caller has explicitly assigned that interpretation to its rates.

`curve_price` discounts each future bond cash flow separately:

```text
t_i = (payment_date_i - settlement_date).days / 365.0
P = sum(CF_i * exp(-r(t_i) * t_i))
```

The result is a dirty currency price. This simplified Actual/365 convention is
distinct from the coupon-period timing and nominal compounding used by the YTM
bond methods.

Shock factories accept basis points and return callables that produce decimal
rate changes. `parallel_shock` is constant. `piecewise_linear_shock` interpolates
between positive, strictly increasing tenor anchors and holds the endpoint
shifts constant outside them. The supplied steepener and flattener use
`(-10, 0, +10)` bp and `(+10, 0, -10)` bp at 2, 10, and 30 years; these are
illustrative definitions, not market standards.

```python
from datetime import date

from fixed_income import (
    FixedRateBond,
    NSSCurve,
    curve_price,
    evaluate_scenario,
    key_rate_dv01,
    parallel_dv01,
    parallel_shock,
)

bond = FixedRateBond(date(2025, 4, 15), date(2055, 1, 15), 0.04)
zero_curve = NSSCurve(0.04, -0.015, 0.02, -0.006, 1.5, 7.0)

print(curve_price(bond, zero_curve))
print(evaluate_scenario(bond, zero_curve, parallel_shock(25), "+25 bp").pnl)
print(key_rate_dv01(bond, zero_curve))
print(parallel_dv01(bond, zero_curve))
```

Scenarios reprice the same cash flows at the same settlement date. They do not
include carry, elapsed time, transaction costs, or curve recalibration.

The default key tenors are 2, 5, 10, and 30 years. Their piecewise-linear basis
weights form a partition of unity. Key-rate and parallel DV01 both use central
full repricing with a one-basis-point bump:

```text
KRDV01_i = [P(r - 0.0001*basis_i) - P(r + 0.0001*basis_i)] / 2
parallel DV01 = [P(r - 0.0001) - P(r + 0.0001)] / 2
```

The sum of key-rate DV01s agrees with parallel DV01 to first order. Independent
finite bumps leave a small cubic-order difference, so exact equality is not
expected.

The risk model does not infer zero rates, enforce arbitrage restrictions, model
credit or optionality, or attach probabilities to scenarios. Results depend on
the supplied curve interpretation, interpolation, and key tenors.

## Tests

Run the deterministic suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

The tests cover financial identities and independent numerical references as
well as validation, boundary cases, plotting, and the CLI. The Python project
does not configure separate formatter, linter, or type-checker commands.

## Scope

The repository deliberately stops at fixed-rate bonds, NSS curve modelling, and
deterministic curve risk. It does not include market-data downloads, trading
signals, backtesting, stochastic risk measures, portfolio optimisation,
execution, services, or user interfaces.
