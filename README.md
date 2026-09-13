# Fixed-income analytics engine

A small Python 3.12+ educational/research project focused on mathematical
transparency, explicit financial conventions, and deterministic offline execution.
**Financial functionality is not yet implemented.** This phase provides packaging,
a help-only CLI, illustrative data, and module/test placeholders.

## Exactly three planned capabilities

1. **Fixed-rate bond analytics:** coupon schedules, accrued interest, dirty and
   clean prices from YTM, Macaulay and modified duration, convexity, and DV01.
2. **Nelson-Siegel-Svensson curves:** standard six-parameter NSS
   (beta0, beta1, beta2, beta3, tau1, tau2), stable factor loadings, scalar/vector
   evaluation, deterministic nonlinear and multi-start calibration using
   scipy.optimize.least_squares, residuals, RMSE (decimal rates and basis points),
   and observation/fit plots.
3. **Interest-rate and curve risk:** bond valuation from continuously compounded
   zero rates, parallel and generic piecewise-linear shocks, steepeners,
   flatteners, and key-rate DV01.

## Conventions and limitations

Rates are decimals internally: 0.05 = 5%; 0.0001 = 1 basis point. Decimal rates,
percentages, percentage points, and basis points must never be mixed silently.
Public APIs will specify units and reject invalid values clearly. The usual
default face value will be 100; prices and price sensitivities must identify their
face-value basis.

Planned conventional bond pricing uses nominal annual YTM compounded at coupon
frequency. Version 1 covers option-free fixed-rate bonds with regular annual or
semiannual coupon periods. Accrued interest uses actual calendar days elapsed in
the current coupon period divided by actual calendar days in that complete
period. Irregular first/final coupons, ex-coupon handling, holiday calendars,
and business-day adjustments are excluded.

YTM-based pricing and discounting individual cash flows from an explicit zero
curve are distinct calculations. Planned curve valuation uses
DF(t) = exp(-r(t) * t), where t is time in years and r(t) is a continuously
compounded annual zero rate. The fitting API will accept generic maturity/rate
observations: Treasury CMT/par-style yields are **not automatically zero-coupon
spot rates** and cannot simply be treated as such for discounting.

Default key-rate tenors will be 2Y, 5Y, 10Y, and 30Y. For sorted keys, each basis
will equal one at its own key and zero at the others, with linear interpolation
between keys. The first basis stays one before the first key; the last stays one
after the last key, with other bases zero in those respective tails. Thus the
bases sum to one at every relevant positive maturity.

## Non-goals

No PCA, relative-value or rich/cheap analysis, z-scores, butterfly strategies,
trading signals, backtesting, VaR, expected shortfall, portfolio optimisation,
machine learning, forecasting, trade execution, brokers, databases, REST APIs,
web applications, dashboards, notebooks, or live market-data downloads.
This is not a production pricing or trading platform.

## Windows PowerShell setup

Run from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Activation is optional. Invoke the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -c "import fixed_income; print(fixed_income.__file__)"
.\.venv\Scripts\python.exe -m fixed_income.cli --help
.\.venv\Scripts\python.exe -m pytest -q
```

Dependency installation may require network access; application execution will
not. Dependencies are declared in pyproject.toml, but versions are not locked,
so this scaffold does not guarantee identical environments across installations.

## CLI and tests

The installed fixed-income command (or python -m fixed_income.cli) currently
shows help only. Future CLI work is limited to bond analytics, NSS fitting and
plotting from local CSV data, and curve-risk scenarios. No financial subcommands
exist yet.

The three test modules contain explicitly skipped placeholders. A successful
pytest run currently confirms collection only, not financial correctness.
Numerical implementation will require deterministic tests.

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
