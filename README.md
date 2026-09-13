# Fixed-income analytics engine

A small Python 3.12+ educational/research project focused on mathematical
transparency, explicit financial conventions, and deterministic offline execution.
**Phases 1 and 2 implement fixed-rate bond analytics and Nelson-Siegel-Svensson
(NSS) yield-curve modelling.** Interest-rate/curve-risk analytics remain an
unimplemented placeholder.

## Exactly three capabilities

1. **Implemented - fixed-rate bond analytics:** regular coupon schedules, accrued
   interest, dirty and clean prices from YTM, Macaulay and modified duration,
   analytical convexity, and full-repricing DV01.
2. **Implemented - Nelson-Siegel-Svensson curves:** standard
   six-parameter NSS (beta0, beta1, beta2, beta3, tau1, tau2), stable factor
   loadings, scalar/vector evaluation, deterministic nonlinear and multi-start
   calibration using scipy.optimize.least_squares, residuals, RMSE in decimal
   rates and basis points, and observation/fit plots.
3. **Not yet implemented - interest-rate and curve risk:** planned bond valuation
   from continuously compounded zero rates, parallel and generic piecewise-linear
   shocks, steepeners, flatteners, and key-rate DV01.

## Implemented bond API and conventions

Rates are decimals internally: 0.05 = 5%; 0.0001 = 1 basis point (bp).
Coupon rate is annual. YTM is a **nominal annual decimal yield compounded at
coupon frequency**, supplied to each pricing/analytics call rather than stored
on the bond. Supported frequencies are 1 (annual) and 2 (semiannual).

FixedRateBond is an immutable dataclass with settlement_date, maturity_date,
coupon_rate, face_value=100.0, and frequency=2. Dates must be datetime.date values,
maturity must follow settlement, face value must be positive, and coupon rate
must be nonnegative. Numerical inputs must be finite. Zero coupons and negative
YTM are supported, provided 1 + YTM/frequency > 0. DV01 and the combined analytics
also require valid yields at both +/-1 bp shifts. Prices outside finite positive
floating-point range raise ValueError.

```python
from datetime import date
from fixed_income import FixedRateBond, BondAnalytics

bond = FixedRateBond(
    settlement_date=date(2025, 4, 15),
    maturity_date=date(2030, 1, 15),
    coupon_rate=0.04,
    face_value=100.0,
    frequency=2,
)
result: BondAnalytics = bond.analytics(ytm=0.045)
print(result.clean_price)
print(result.dv01)
```

The public bond methods are coupon_schedule(), accrued_interest(),
dirty_price(ytm), clean_price(ytm), macaulay_duration(ytm),
modified_duration(ytm), convexity(ytm), dv01(ytm), and analytics(ytm).
previous_coupon_date and next_coupon_date are date properties.
BondAnalytics holds ytm, accrued_interest, dirty_price, clean_price,
macaulay_duration, modified_duration, convexity, and dv01.

### Schedule and accrued interest

Dates are generated backward from maturity using dateutil.relativedelta at
integer multiples of 12 months (annual) or 6 months (semiannual). Every date is
anchored to maturity, avoiding cumulative day-of-month drift. A nonexistent day
clips to the last day of that month; there is no additional end-of-month rule.
For example, August 31 anchors produce February 28/29 and August 31 coupons.

coupon_schedule() returns an ascending tuple of payment dates strictly after
settlement, including maturity. The previous coupon is on or before settlement;
the next coupon is strictly after settlement. **Settlement on a coupon date
excludes that day's payment and starts a new period with zero accrued interest.**

For periodic coupon C = face_value * coupon_rate / m, with m = frequency:

```text
alpha = elapsed calendar days from previous coupon to settlement
        / calendar days from previous coupon to next coupon
accrued_interest = C * alpha
```

This is an actual-days fraction of the regular coupon period, not a complete
market day-count implementation.

### Prices and durations

For i = 1 at the next coupon, define w = 1 - alpha and q_i = w + i - 1.
CF_i is C, with principal added at maturity. For annual decimal YTM y:

```text
PV_i = CF_i * (1 + y/m)^(-q_i)
dirty_price = sum(PV_i)
clean_price = dirty_price - accrued_interest
t_i = q_i / m
Macaulay duration = sum(t_i * PV_i) / dirty_price
modified duration = Macaulay duration / (1 + y/m)
```

Prices and accrued interest are currency amounts for the supplied face value;
they are not automatically normalized to 100. Both durations are in years.
Macaulay duration is the PV-weighted payment time. Modified duration equals
-(dP/dy)/P for dirty price P and annual decimal YTM y. Payment times use fractional
coupon periods divided by frequency, not actual days divided by 365.

### Convexity and DV01

Analytical convexity is the dirty-price-normalized second derivative with respect
to **annual decimal YTM**, conventionally expressed in years squared:

```text
d2P/dy2 = sum(CF_i * q_i * (q_i + 1) / m^2 * (1 + y/m)^(-q_i - 2))
convexity = (d2P/dy2) / dirty_price
```

Convexity itself has no factor of 1/2. That factor enters the second-order
approximation: delta_P / P is approximately
-modified_duration * delta_y + 0.5 * convexity * delta_y^2.

Public DV01 uses full central repricing of dirty price, with **1 bp = 0.0001**:

```text
DV01 = [P(y - 0.0001) - P(y + 0.0001)] / 2
DV01_approx = modified_duration * dirty_price * 0.0001
```

DV01 is a currency amount for a one-basis-point move on the supplied face value
and is positive for a conventional positive-duration bond. The approximation is
documented for comparison; the public method uses the full repricing formula.

### Version 1 limitations

Only option-free bonds with regular maturity-based annual or semiannual coupons
are supported. There is no issue date, irregular first/final coupon, holiday
adjustment, business-day convention, special end-of-month rule, or ex-coupon
handling. Calculations use floating-point arithmetic and deterministic
illustrative inputs. There is no yield solver or explicit zero-curve valuation.

## Implemented NSS API and calibration

NSSCurve is an immutable dataclass with beta0, beta1, beta2, beta3 (decimal
rates) and tau1, tau2 (strictly positive years). All parameters must be finite.
yield_rate(maturity_years) accepts a scalar or NumPy array of finite positive
maturities in years and returns decimal rates, preserving array shape. A scalar
or zero-dimensional array returns a Python float. **t=0 is not supported.**
The model retains the caller's rate convention and does no compounding conversion.

For x1 = t/tau1 and x2 = t/tau2:

```text
L1(x) = (1 - exp(-x)) / x
L2(x) = L1(x) - exp(-x)
y(t) = beta0 + beta1*L1(x1) + beta2*L2(x1) + beta3*L2(x2)
```

The loadings use numpy.expm1 and, below x=0.001, Taylor expansions through
x^5 with O(x^6) remainder. Expanding L2 separately avoids cancellation between
L1 and exp(-x) at extremely short positive maturities.

```python
import numpy as np
from pathlib import Path
from fixed_income import NSSCurve, NSSFitResult, fit_nss, plot_nss

maturities = np.array([0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])
known = NSSCurve(0.04, -0.025, 0.03, -0.012, 1.4, 6.5)
observed_rates = known.yield_rate(maturities)  # invented decimal-rate observations
fit: NSSFitResult = fit_nss(maturities, observed_rates)
print(fit.curve.yield_rate(4.0))
print(fit.rmse_bps)
figure = plot_nss(maturities, observed_rates, fit.curve, Path("outputs/synthetic.png"))
```

fit_nss requires 1D arrays of equal length, finite rates, positive maturities,
and at least six distinct maturities. Input order is retained; repeated tenors
beyond this minimum are allowed and each observation has equal weight.
Negative rates are permitted.

Calibration uses scipy.optimize.least_squares to jointly fit all six parameters
from six fixed (tau1, tau2) starting pairs in years:
(0.5, 2), (1, 5), (2, 10), (5, 1), (10, 3), and (3, 15).
Each start initializes the four betas with linear least squares at those taus.
Betas are unbounded, allowing varied curve shapes; taus are bounded to
[0.01, 100] years. Optimization residuals are scaled to basis points for numerical
conditioning, with Jacobian-based parameter scaling, tolerances of 1e-10 and
at most 3,000 function evaluations per start. These choices are deterministic;
there is no random initialization.

Only successful candidates with finite parameters, valid bounds and finite
residual sum of squares are eligible. The lowest unweighted residual sum of
squares wins; ties retain the earlier start. If none succeeds, fit_nss raises
RuntimeError with failure details. Invalid inputs raise ValueError.

NSSFitResult contains curve, maturities, observed_rates, fitted_rates, residuals,
rmse, rmse_bps, success, status, message, nfev, starts_attempted and
starts_succeeded. Arrays are independent read-only copies in original observation
order. Optimizer metadata and nfev describe the selected run, not total work.

```text
residual = observed_rate - fitted_rate        # decimal rate
RMSE = sqrt(mean(residual^2))                # decimal rate
RMSE_bps = RMSE * 10_000                     # basis points
```

plot_nss accepts the observations, an NSSCurve and an optional pathlib.Path.
It returns a matplotlib Figure and optionally saves it, creating parent
directories. Observed points and a smooth fit over the observed maturity range
are shown against maturity in years, with rates converted to percentages for
the labelled plot axis. It does not open an interactive window.

### Calibration limitations

NSS is nonlinear and can have local minima and weakly identified parameters.
A modest deterministic multi-start search does not guarantee a global optimum
or unique parameters. Six distinct observations are only a minimum input check,
not a guarantee of identification; broad tenor coverage and more observations
are preferable. Different parameter sets may describe almost identical curves.
Tau bounds can constrain unusual curves. There are no shape, positivity or
arbitrage constraints, no observation weights, and no extrapolation guarantees.
Reproducibility assumes the same numerical environment; dependencies are not locked.

## Curve conventions and future risk module

The fitting API accepts **generic maturity/rate observations** and does not
assign a financial interpretation or compounding convention to them.
**Par/CMT-style yields** describe coupon-bearing/par-style instruments;
**zero-coupon spot rates** describe discounting to a single maturity under
a specified compounding convention. These are distinct inputs.

**Fitting an NSS function to Treasury CMT/par-style yields does NOT
automatically convert them into a bootstrapped zero curve.**
Treating an NSS fit to par-style yields as though it were a zero curve is only
an educational approximation unless a proper bootstrap has been performed.
This project does not currently implement bootstrapping.

YTM-based bond pricing and discounting individual cash flows from an explicit
zero curve are distinct calculations. The later curve-risk module will require
the caller to interpret supplied rates explicitly as **continuously compounded
annual zero rates** in decimal units, with DF(t) = exp(-r(t) * t) for t in years.
NSS fitting alone does not establish that interpretation. Curve-risk calculations
are not implemented in this phase.

Planned default key-rate tenors are 2Y, 5Y, 10Y, and 30Y. For sorted keys, each
basis will equal one at its own key and zero at the others, with linear
interpolation between keys. The first basis stays one before the first key; the
last stays one after the last key, with other bases zero in those respective
tails. Thus the bases will sum to one at every relevant positive maturity.

## Non-goals

No PCA, relative-value or rich/cheap analysis, z-scores, butterfly strategies,
trading signals, backtesting, VaR, expected shortfall, portfolio optimisation,
machine learning, forecasting, trade execution, brokers, databases, REST APIs,
web applications, dashboards, notebooks, or live market-data downloads.
This is not a production pricing or trading platform.

## Windows PowerShell setup

Run from the repository root. Create the environment only if needed; all commands
invoke its Python directly and do not depend on activation:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -c "import fixed_income; print(fixed_income.__file__)"
.\.venv\Scripts\python.exe -m fixed_income.cli --help
.\.venv\Scripts\python.exe -m fixed_income.cli bond
.\.venv\Scripts\python.exe -m fixed_income.cli curve
.\.venv\Scripts\python.exe -m pytest tests\test_curves.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_bonds.py -q
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

Dependency installation may require network access; application execution does
not. Dependencies are declared in pyproject.toml, but versions are not locked,
so identical environments across installations are not guaranteed.

## CLI and tests

The bond subcommand prints a clearly labelled invented example with settlement,
maturity, face value, annual coupon rate, annual YTM, payment frequency, accrued
interest, dirty/clean price, both durations, convexity, and full-repricing DV01.
Rates display both percentages and decimal values; price amounts, years, years
squared, and basis points are explicitly labelled. Running without a subcommand
shows help. The curve subcommand reads examples/illustrative_curve.csv relative
to the repository root, fits NSS and prints all six parameters, optimizer status,
and RMSE in both decimal rate units and basis points. It saves
outputs/yield_curve.png, creating the gitignored outputs directory if needed.
The CSV is invented illustrative data, never current/live market data.
Curve-risk commands are not implemented.

Deterministic bond tests check par/premium/discount pricing, price monotonicity,
accrual and coupon boundaries, leap-year/month-end schedules, single fractional
periods, zero coupons, annual/semiannual frequency, negative and zero yields,
face-value scaling, input validation, combined analytics, and the CLI.
Independent numerical first/second derivatives check duration and convexity;
direct repricing checks DV01. Derivative steps and tolerances are documented
in the tests. Deterministic curve tests cover scalar/vector formulas and shapes,
short-maturity accuracy against high-precision reference calculations, input
validation, synthetic curve-fit quality, RMSE units, reproducibility, result
metadata, candidate selection and failure handling, plotting and the curve CLI.
Only the risk test module remains an explicitly skipped placeholder; that skip
establishes no numerical correctness.

## Repository layout

```text
.
|-- .gitignore
|-- AGENTS.md
|-- README.md
|-- pyproject.toml
|-- examples/
|   `-- illustrative_curve.csv
|-- src/
|   `-- fixed_income/
|       |-- __init__.py
|       |-- bonds.py
|       |-- curves.py
|       |-- risk.py
|       `-- cli.py
`-- tests/
    |-- test_bonds.py
    |-- test_curves.py
    `-- test_risk.py
```

examples/illustrative_curve.csv contains invented, illustrative offline example
data from 0.25 to 30 years. Its columns are maturity_years and rate, with rates
in decimal units. These are not observed market data and carry no implied
zero-rate or compounding convention.
