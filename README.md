# Fixed-income analytics engine

A small Python 3.12+ educational/research project focused on mathematical
transparency, explicit financial conventions, and deterministic offline execution.
**All three intended capabilities are implemented:** fixed-rate bond analytics,
Nelson-Siegel-Svensson (NSS) yield-curve modelling, and interest-rate/curve-risk
analytics. This is an educational library, not a production pricing platform.

## Exactly three capabilities

1. **Implemented - fixed-rate bond analytics:** regular coupon schedules, accrued
   interest, dirty and clean prices from YTM, Macaulay and modified duration,
   analytical convexity, and full-repricing DV01.
2. **Implemented - Nelson-Siegel-Svensson curves:** standard
   six-parameter NSS (beta0, beta1, beta2, beta3, tau1, tau2), stable factor
   loadings, scalar/vector evaluation, deterministic nonlinear and multi-start
   calibration using scipy.optimize.least_squares, residuals, RMSE in decimal
   rates and basis points, and observation/fit plots.
3. **Implemented - interest-rate and curve risk:** bond valuation
   from continuously compounded zero rates, parallel and generic piecewise-linear
   shocks, steepeners, flatteners, and key-rate DV01.

## Windows PowerShell setup

Use native PowerShell from the repository root (the directory containing
`pyproject.toml`, `src`, and `examples`). Python 3.12 or later is required.

If `.venv` does not exist, create it once. This example selects an installed
Python 3.12 using the Windows `py` launcher; select a later installed version
instead if appropriate:

```powershell
py -3.12 -m venv .venv
```

Install the package in editable mode with the test dependency, then check the
interpreter version and package import. These commands use the virtual
environment directly; activation is unnecessary:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import fixed_income; print(fixed_income.__file__)"
```

Dependency installation may require network access; application execution does
not. Dependencies are declared in `pyproject.toml`, but versions are not locked,
so identical environments across installations are not guaranteed.

## CLI examples

Run these commands from the repository root after installation:

```powershell
.\.venv\Scripts\python.exe -m fixed_income.cli --help
.\.venv\Scripts\python.exe -m fixed_income.cli bond
.\.venv\Scripts\python.exe -m fixed_income.cli curve
.\.venv\Scripts\python.exe -m fixed_income.cli risk
.\.venv\Scripts\python.exe -m fixed_income.cli demo
```

Each subcommand runs a fixed illustrative example; there are no CLI options for
custom bond parameters or input/output paths. Use the Python API for custom
inputs. Running without a subcommand shows help.

| Subcommand | Result |
| --- | --- |
| `bond` | Prints the invented bond's dates, face value, coupon, YTM, frequency, accrued interest, dirty/clean price, durations, convexity, and full-repricing DV01. |
| `curve` | Fits NSS to the invented CSV; prints all six parameters, optimizer status, and RMSE in decimal rates and bp; saves `outputs/yield_curve.png`. |
| `risk` | Fits the same CSV and explicitly interprets its rates as continuous zeros; prints base price, parallel +/-25 bp and shape scenarios, KRDV01s, parallel DV01, and reconciliation. |
| `demo` | Runs the bond, curve, and risk examples in order, reusing the fitted curve. |

The `curve`, `risk`, and `demo` commands resolve
`examples/illustrative_curve.csv` from the **current working directory**. They
require the repository's example data; installing the package does not make
these paths independent of the working directory. The CSV contains invented
rates, never current/live market data, and fitting it does not bootstrap a zero
curve. The risk example uses settlement 2025-04-15 and maturity 2055-01-15,
approximately 30 years apart.

The `curve` and `demo` commands create the gitignored `outputs` directory and
write the same `outputs/yield_curve.png` path. Rerunning either command replaces
that plot. The bond output labels rates in both percentages and decimals and
labels currency amounts, years, and years squared; curve and risk output state
their rate interpretation and units.

## Bond API and conventions

Rates are decimals internally: 0.05 = 5%; 0.0001 = 1 basis point (bp).
Coupon rate is annual. YTM is a **nominal annual decimal yield compounded at
coupon frequency**, supplied to each pricing/analytics call rather than stored
on the bond. Supported frequencies are 1 (annual) and 2 (semiannual).

FixedRateBond is an immutable dataclass with settlement_date, maturity_date,
coupon_rate, face_value=100.0, and frequency=2. Dates must be datetime.date values,
maturity must follow settlement, face value must be positive, and coupon rate
must be nonnegative. Numerical inputs must be finite. Accepted real scalars
(including NumPy scalars) are converted to Python floats before arithmetic,
so lower-precision input dtypes do not reduce cash-flow or 1 bp bump precision.
This preserves the supplied values; it cannot restore precision already lost
when those values were created. Zero coupons and negative YTM are supported,
provided `1 + YTM/frequency > 0`. DV01 and the combined analytics also require
valid yields at both +/-1 bp shifts. Yields that produce a nonfinite or
nonpositive dirty price, or overflow during discounting, raise `ValueError`.
Clean price is calculated by subtracting accrued interest; it has no separate
positivity check.

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
For example, semiannual August 31 anchors produce February 28/29 and August 31
coupons.

coupon_schedule() returns an ascending tuple of payment dates strictly after
settlement, including maturity. The previous coupon is on or before settlement;
the next coupon is strictly after settlement. **Settlement on a coupon date
excludes that day's payment and starts a new period with zero accrued interest.**

For periodic coupon `C = face_value * coupon_rate / m`, with `m = frequency`:

```text
alpha = elapsed calendar days from previous coupon to settlement
        / calendar days from previous coupon to next coupon
accrued_interest = C * alpha
```

This is an actual-days fraction of the regular coupon period, not a complete
market day-count implementation.

### Prices and durations

For `i = 1` at the next coupon, define `w = 1 - alpha` and `q_i = w + i - 1`.
`CF_i` is `C`, with principal added at maturity. For annual decimal YTM `y`:

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
`-(dP/dy)/P` for dirty price `P` and annual decimal YTM `y`. Payment times use fractional
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
`-modified_duration * delta_y + 0.5 * convexity * delta_y^2`.

Public DV01 uses full central repricing of dirty price, with **1 bp = 0.0001**:

```text
DV01 = [P(y - 0.0001) - P(y + 0.0001)] / 2
DV01_approx = modified_duration * dirty_price * 0.0001
```

DV01 is a currency amount for a one-basis-point move on the supplied face value
and is positive for a conventional positive-duration bond. The approximation is
documented for comparison; the public method uses the full repricing formula.

### Bond limitations

Only option-free bonds with regular maturity-based annual or semiannual coupons
are supported. There is no issue date, irregular first/final coupon, holiday
adjustment, business-day convention, special end-of-month rule, or ex-coupon
handling. Calculations use floating-point arithmetic and deterministic
illustrative inputs. There is no yield solver. Explicit zero-curve valuation is
provided separately by risk.curve_price and does not change the YTM bond API.

## NSS API and calibration

NSSCurve is an immutable dataclass with beta0, beta1, beta2, beta3 (decimal
rates) and tau1, tau2 (strictly positive years). All parameters must be finite.
yield_rate(maturity_years) accepts a scalar or NumPy array of finite positive
maturities in years and returns decimal rates, preserving array shape. A scalar
or zero-dimensional array returns a Python float. **t=0 is not supported.**
The model retains the caller's rate convention and does no compounding conversion.

For `x1 = t/tau1` and `x2 = t/tau2`:

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
`max_nfev=3000` per start. SciPy's evaluation count excludes the additional
residual calls used to approximate the numerical Jacobian, so 3,000 is not a
limit on all residual calls. These choices are deterministic; there is no random
initialization.

Only successful candidates with finite parameters, valid bounds and finite
residual sum of squares are eligible. The lowest unweighted residual sum of
squares wins; ties retain the earlier start. If none succeeds, fit_nss raises
RuntimeError with failure details. Invalid inputs raise ValueError.

`NSSFitResult` contains `curve`, `maturities`, `observed_rates`, `fitted_rates`,
`residuals`, `rmse`, `success`, `status`, `message`, `nfev`, `starts_attempted`, and
`starts_succeeded`; `rmse_bps` is a computed property. Arrays returned by `fit_nss`
are independent read-only copies in original observation order. Optimizer
metadata and `nfev` describe the selected run, not total work across starts;
`nfev` also excludes the numerical-Jacobian residual calls described above.

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

## Curve conventions and zero-rate interpretation

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
zero curve are distinct calculations. The curve-risk module requires
the caller to interpret supplied rates explicitly as **continuously compounded
annual zero rates** in decimal units, with DF(t) = exp(-r(t) * t) for t in years.
NSS fitting alone does not establish that interpretation.

## Zero-curve valuation and risk API

ZeroCurve is a minimal protocol with yield_rate(maturity_years), evaluated at
scalar positive years and returning a finite scalar continuous annual decimal
zero rate (a zero-dimensional NumPy array is also accepted). NSSCurve can be
passed directly when the caller explicitly chooses that rate interpretation.
The library cannot infer the economic meaning of supplied observations.

curve_price(bond, curve) reuses FixedRateBond.coupon_schedule(), excludes
settlement-date payments, and adds principal to the last coupon. It returns a
**dirty currency price for the supplied face value**, without subtracting accrued
interest. The existing bond schedule limitations still apply.

```text
t_i = (cash_flow_date_i - settlement_date).days / 365.0
CF_i = face_value * coupon_rate / frequency  (+ face_value at maturity)
DF(t_i) = exp(-r(t_i) * t_i)
P = sum_i CF_i * DF(t_i)
```

This **simplified Actual/365** convention counts actual calendar days, including
leap days, but always divides by 365.0. It is a project convention, not a universal
market convention. It differs from the fractional coupon-period times used by
bonds.py for nominal annual YTM compounded at coupon frequency. Curve pricing
never routes through that YTM formula. Negative zero rates are allowed.
Nonfinite curve outputs and prices outside positive floating-point range fail
with ValueError.

### Shocks and scenarios

parallel_shock(shift_bps) returns a callable decimal shift for any finite bp
input, including +/-25 bp. piecewise_linear_shock(anchor_years, shifts_bps)
accepts nonempty 1D arrays of equal length: finite, positive, strictly increasing
anchor years and finite bp shocks. Duplicate or unsorted anchors fail. Shocks
interpolate linearly between anchors and stay flat at the first/last shock in
the respective tails. A single anchor defines a constant shock.

**1 bp = 0.0001 decimal rate.** Factories convert bp to decimal changes exactly
once at construction. Returned shock(t) callables accept positive years and
return decimals. `ShockedCurve(base_curve, shock)` adds that decimal change to
the base rate without modifying the base curve. Its `shock` argument is a
callable: `shock(t)` takes a positive maturity in years and returns a decimal
rate change. Use the factories above to construct that callable from bp inputs.

The illustrative defaults are:

| Definition | 2Y | 10Y | 30Y |
| --- | ---: | ---: | ---: |
| steepener_shock() | -10 bp | 0 bp | +10 bp |
| flattener_shock() | +10 bp | 0 bp | -10 bp |

Both functions accept custom anchor_years and shifts_bps and use the same
interpolation/tails as piecewise_linear_shock. These are illustrative definitions;
there is no single universally correct steepener or flattener.

evaluate_scenario(bond, curve, shock, name) fully reprices and returns
ScenarioResult(name, base_price, shocked_price), with pnl as a property:

```text
shocked_rate(t) = base_rate(t) + shock(t)   # decimal zero rates
P&L = shocked_price - base_price           # currency for the bond's face value
```

Scenarios are instantaneous: settlement and cash flows remain fixed. There is
no passage of time, carry, transaction costs, or curve recalibration under shocks.
Caller-provided curves and shock callables must be deterministic and should not
mutate their own state.

```python
from datetime import date
from fixed_income import (
    FixedRateBond, NSSCurve, curve_price, evaluate_scenario,
    parallel_shock, key_rate_dv01, parallel_dv01,
)

bond = FixedRateBond(date(2025, 4, 15), date(2055, 1, 15), 0.04)
# Explicitly interpret these invented NSS rates as continuous annual zero rates.
zero_curve = NSSCurve(0.04, -0.015, 0.02, -0.006, 1.5, 7.0)
print(curve_price(bond, zero_curve))
print(evaluate_scenario(bond, zero_curve, parallel_shock(25), "+25 bp").pnl)
print(key_rate_dv01(bond, zero_curve))
print(parallel_dv01(bond, zero_curve))
```

### Key-rate basis, DV01 and reconciliation

key_rate_basis(maturity_years, key_tenors=(2, 5, 10, 30)) returns dimensionless
weights with shape (*maturity_shape, number_of_keys). Scalar maturity yields
a vector in key order. Keys must be positive, finite, nonempty and strictly
increasing. One key is supported and has weight one everywhere.

Each basis equals one at its own key and zero at every other key. Between
adjacent keys only the neighboring two bases are nonzero, linearly interpolating
with weights summing to one. Below the first key its basis is one; above the
last key its basis is one. Thus **sum_i basis_i(t) = 1** at every positive
maturity, including both tails.

key_rate_dv01(bond, curve, key_tenors=(2, 5, 10, 30)) returns an ordered tuple
of KeyRateDV01(tenor_years, dv01). parallel_dv01(bond, curve) returns a scalar.
Both use full repricing under continuous zero-rate shifts and Actual/365 times:

```text
KRDV01_i = [P(r - 0.0001*basis_i) - P(r + 0.0001*basis_i)] / 2
parallel_DV01 = [P(r - 0.0001) - P(r + 0.0001)] / 2
reconciliation_difference = sum_i KRDV01_i - parallel_DV01
```

These are currency amounts for one bp, not derivatives per unit decimal rate.
They have positive signs for conventional positive-cash-flow bonds; an
unexposed key can have zero sensitivity.

Partition of unity makes the linear sensitivities additive. Independent central
full repricing is nonlinear, so the sum of KRDV01s only approximately matches
parallel DV01. For positive PVs and h=0.0001, each cash-flow contribution is
`PV*sinh(h*t*weight)`; linear terms cancel in the reconciliation. The discrepancy
starts at order h^3. Tests bound parallel_DV01 - sum KRDV01 by
`sum PV*(h*t)^3*cosh(h*t)/6` plus floating-point rounding, and also check the leading
cubic term with a fifth-order remainder bound.

### Risk modelling limitations

The caller is responsible for supplying meaningful continuous zero rates.
There is no bootstrap, automatic rate-convention conversion, credit/default or
option modelling, arbitrage enforcement, or guarantee of sensible extrapolation.
Risk holds cash flows fixed, ignores elapsed time and liquidity, and depends on
the chosen anchors, basis and interpolation. Scenario P&L signs for steepeners
and flatteners depend on the bond's cash-flow exposures. Curve DV01 need not
equal the YTM DV01: their rate variables, compounding and time conventions differ.

## Non-goals

No PCA, relative-value or rich/cheap analysis, z-scores, butterfly strategies,
trading signals, backtesting, VaR, expected shortfall, portfolio optimisation,
machine learning, forecasting, trade execution, brokers, databases, REST APIs,
web applications, dashboards, notebooks, or live market-data downloads.
This is not a production pricing or trading platform.

## Tests

Run the complete deterministic suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

For a focused check, run the relevant module's tests. Check whitespace before
committing documentation or code changes:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_bonds.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_curves.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_risk.py -q
git diff --check
```

Deterministic bond tests check par/premium/discount pricing, price monotonicity,
accrual and coupon boundaries, leap-year/month-end schedules, single fractional
periods, zero coupons, annual/semiannual frequency, negative and zero yields,
face-value scaling, real-scalar precision, input validation, combined analytics,
and the CLI.
Independent numerical first/second derivatives check duration and convexity;
direct repricing checks DV01. Derivative steps and tolerances are documented
in the tests. Deterministic curve tests cover scalar/vector formulas and shapes,
short-maturity accuracy against high-precision reference calculations, input
validation, synthetic curve-fit quality, RMSE units, reproducibility, result
metadata, candidate selection and failure handling, plotting and the curve CLI.
Risk tests independently check flat continuous-zero discounting, Actual/365
and coupon boundaries, scenario units/signs/P&L, interpolation/tails, default
and custom shapes, key partition of unity, single-cash-flow sensitivities,
mathematically bounded DV01 reconciliation, input validation, base-curve
immutability and the risk/demo CLI. No placeholder tests remain.

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
