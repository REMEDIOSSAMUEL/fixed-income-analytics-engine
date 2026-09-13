# Fixed-income analytics engine

A small Python 3.12+ educational/research project focused on mathematical
transparency, explicit financial conventions, and deterministic offline execution.
**Phase 1 implements fixed-rate bond analytics.** Nelson-Siegel-Svensson (NSS)
modelling and interest-rate/curve-risk analytics remain unimplemented placeholders.

## Exactly three capabilities

1. **Implemented - fixed-rate bond analytics:** regular coupon schedules, accrued
   interest, dirty and clean prices from YTM, Macaulay and modified duration,
   analytical convexity, and full-repricing DV01.
2. **Not yet implemented - Nelson-Siegel-Svensson curves:** planned standard
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

## Future curve conventions (not implemented)

YTM-based pricing and discounting individual cash flows from an explicit zero
curve are distinct calculations. Planned curve valuation uses
DF(t) = exp(-r(t) * t), where t is time in years and r(t) is a continuously
compounded annual zero rate. The fitting API will accept generic maturity/rate
observations: Treasury CMT/par-style yields are **not automatically zero-coupon
spot rates** and cannot simply be treated as such for discounting.

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
shows help. NSS and curve-risk commands are not implemented.

Deterministic bond tests check par/premium/discount pricing, price monotonicity,
accrual and coupon boundaries, leap-year/month-end schedules, single fractional
periods, zero coupons, annual/semiannual frequency, negative and zero yields,
face-value scaling, input validation, combined analytics, and the CLI.
Independent numerical first/second derivatives check duration and convexity;
direct repricing checks DV01. Derivative steps and tolerances are documented
in the tests. Curve and risk test modules remain explicitly skipped placeholders;
those skips establish no numerical correctness.

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
