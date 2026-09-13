"""Nelson-Siegel-Svensson fitting of generic decimal rates at positive years.

No compounding conversion or bootstrap is performed. The caller supplies the
rate convention; fitting par/CMT-style yields does not produce a zero curve.
"""

from dataclasses import dataclass
from math import isfinite
from numbers import Real
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares


def _real_array(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """Reject non-real/nonfinite data instead of silently discarding components."""
    array = np.asarray(values)
    if array.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain finite real numbers")
    array = np.asarray(array, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain finite real numbers")
    return array


def _loadings(x: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """L1=(1-exp(-x))/x; L2=L1-exp(-x), stable near zero."""
    small = x < 1e-3
    l1 = np.empty_like(x)
    l2 = np.empty_like(x)
    z = x[small]
    # Taylor series through x**5; omitted terms are O(x**6).
    # This also handles t/tau underflow to zero for positive input maturities.
    l1[small] = 1 + z * (-1/2 + z * (1/6 + z * (-1/24 + z * (1/120 - z/720))))
    l2[small] = z * (1/2 + z * (-1/3 + z * (1/8 + z * (-1/30 + z/144))))
    z = x[~small]
    l1[~small] = -np.expm1(-z) / z
    l2[~small] = l1[~small] - np.exp(-z)
    return l1, l2


def _design(maturities: NDArray[np.float64], tau1: float, tau2: float) -> NDArray[np.float64]:
    # An overflowing positive ratio has the correct limiting loadings (0, 0).
    with np.errstate(over="ignore", under="ignore"):
        l1, l2 = _loadings(maturities / tau1)
        _, l3 = _loadings(maturities / tau2)
    return np.stack((np.ones_like(maturities), l1, l2, l3), axis=-1)


@dataclass(frozen=True)
class NSSCurve:
    """Six-parameter NSS curve; betas are decimal rates, taus are years.

    yield_rate(t) retains the supplied rate/compounding convention; it neither
    bootstraps nor converts rates. All parameters must be finite real numbers,
    taus strictly positive. Evaluation requires finite t > 0 in years.
    """

    beta0: float
    beta1: float
    beta2: float
    beta3: float
    tau1: float
    tau2: float

    def __post_init__(self) -> None:
        for name in ("beta0", "beta1", "beta2", "beta3", "tau1", "tau2"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
                raise ValueError(f"{name} must be a finite real number")
        if self.tau1 <= 0 or self.tau2 <= 0:
            raise ValueError("tau1 and tau2 must be strictly positive years")

    def yield_rate(self, maturity_years: ArrayLike) -> float | NDArray[np.float64]:
        """Return decimal rates at positive years, preserving NumPy input shape.

        A scalar (including a zero-dimensional array) returns a Python float.
        t=0 is deliberately unsupported. No compounding convention is imposed.
        """
        maturities = _real_array(maturity_years, "maturities")
        if np.any(maturities <= 0):
            raise ValueError("maturities must be strictly positive years")
        with np.errstate(over="ignore", invalid="ignore"):
            rates = _design(maturities, self.tau1, self.tau2) @ np.array(
                [self.beta0, self.beta1, self.beta2, self.beta3]
            )
        if not np.all(np.isfinite(rates)):
            raise ValueError("NSS rates exceed finite floating-point range")
        return float(rates) if maturities.ndim == 0 else rates


@dataclass(frozen=True)
class NSSFitResult:
    """Selected fit and observation context in original input order.

    maturities are years; observed_rates, fitted_rates, residuals and rmse are
    decimal rates in the caller's convention. residuals = observed - fitted.
    Arrays returned by fit_nss are independent, read-only copies.
    success, status, message and nfev describe the selected optimizer run;
    nfev is not the total across starts. Start counts describe the whole fit.
    """

    curve: NSSCurve
    maturities: NDArray[np.float64]
    observed_rates: NDArray[np.float64]
    fitted_rates: NDArray[np.float64]
    residuals: NDArray[np.float64]
    rmse: float
    success: bool
    status: int
    message: str
    nfev: int
    starts_attempted: int
    starts_succeeded: int

    @property
    def rmse_bps(self) -> float:
        """RMSE in basis points: decimal-rate RMSE multiplied by 10,000."""
        return self.rmse * 10_000


def _observations(
    maturity_years: ArrayLike, observed_rates: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    maturities = _real_array(maturity_years, "maturities")
    rates = _real_array(observed_rates, "observed rates")
    if maturities.ndim != 1 or rates.ndim != 1:
        raise ValueError("maturities and observed rates must be 1D arrays")
    if maturities.size != rates.size:
        raise ValueError("maturities and observed rates must have identical lengths")
    if maturities.size == 0 or np.any(maturities <= 0):
        raise ValueError("maturities must be nonempty and strictly positive years")
    return maturities, rates


def fit_nss(maturity_years: ArrayLike, observed_rates: ArrayLike) -> NSSFitResult:
    """Fit generic decimal rates at years by deterministic unweighted least squares.

    Require at least six distinct positive maturities. Input order is preserved;
    repeated tenors are allowed beyond this minimum and receive equal weight.
    Six fixed tau pairs seed linear least-squares beta estimates, followed by
    joint six-parameter scipy least_squares fits. Betas are unbounded; both taus
    are bounded to [0.01, 100] years. Residuals are scaled to bp for optimization
    only. Select the finite successful candidate with lowest decimal-rate SSE.
    Raise RuntimeError if all starts fail. Neither a global minimum nor unique
    parameters are guaranteed. No bootstrap or compounding conversion is done.
    """
    maturities, rates = _observations(maturity_years, observed_rates)
    if np.unique(maturities).size < 6:
        raise ValueError("NSS fitting requires at least six distinct maturities")
    starts = ((0.5, 2.0), (1.0, 5.0), (2.0, 10.0),
              (5.0, 1.0), (10.0, 3.0), (3.0, 15.0))
    lower = np.array([-np.inf] * 4 + [0.01, 0.01])
    upper = np.array([np.inf] * 4 + [100.0, 100.0])
    best = None
    best_sse = np.inf
    successes = 0
    failures = []

    def objective(parameters: NDArray[np.float64]) -> NDArray[np.float64]:
        fitted = _design(maturities, parameters[4], parameters[5]) @ parameters[:4]
        return (rates - fitted) * 10_000

    for tau1, tau2 in starts:
        try:
            betas = np.linalg.lstsq(_design(maturities, tau1, tau2), rates, rcond=None)[0]
            candidate = least_squares(
                objective, np.r_[betas, tau1, tau2], bounds=(lower, upper),
                x_scale="jac", ftol=1e-10, xtol=1e-10, gtol=1e-10,
                max_nfev=3000,
            )
            if not candidate.success:
                failures.append(str(candidate.message))
                continue
            parameters = candidate.x
            if (not np.all(np.isfinite(parameters))
                    or np.any(parameters < lower) or np.any(parameters > upper)):
                failures.append("optimizer returned invalid parameters")
                continue
            curve = NSSCurve(*parameters)
            fitted_rates = np.asarray(curve.yield_rate(maturities))
            residuals = rates - fitted_rates
            with np.errstate(over="ignore", invalid="ignore"):
                sse = float(residuals @ residuals)
            if not np.isfinite(sse):
                failures.append("optimizer returned nonfinite residual sum of squares")
                continue
            successes += 1
            if sse < best_sse:
                best_sse = sse
                best = (curve, fitted_rates, residuals, candidate)
        except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
            failures.append(str(exc))

    if best is None:
        raise RuntimeError(
            f"NSS calibration failed: no successful valid fit from {len(starts)} starts. "
            + "; ".join(failures)
        )
    curve, fitted_rates, residuals, candidate = best
    arrays = [array.copy() for array in (maturities, rates, fitted_rates, residuals)]
    for array in arrays:
        array.setflags(write=False)
    return NSSFitResult(
        curve=curve, maturities=arrays[0], observed_rates=arrays[1],
        fitted_rates=arrays[2], residuals=arrays[3],
        rmse=float(np.sqrt(best_sse / rates.size)),
        success=bool(candidate.success), status=int(candidate.status),
        message=str(candidate.message), nfev=int(candidate.nfev),
        starts_attempted=len(starts), starts_succeeded=successes,
    )


def plot_nss(
    maturity_years: ArrayLike,
    observed_rates: ArrayLike,
    curve: NSSCurve,
    output_path: Path | None = None,
) -> Figure:
    """Plot decimal-rate observations and NSS fit; display the rate axis in %.

    Maturities are positive years. The caller's rate/compounding convention is
    retained. Return a Figure without opening a GUI; optionally save it, creating
    parent directories with pathlib. The smooth fit spans the observed tenors.
    """
    maturities, rates = _observations(maturity_years, observed_rates)
    grid = np.linspace(float(maturities.min()), float(maturities.max()), 500)
    figure = Figure(figsize=(8, 5), layout="constrained")
    axes = figure.subplots()
    axes.scatter(maturities, rates * 100, label="Observed rates")
    axes.plot(grid, np.asarray(curve.yield_rate(grid)) * 100, label="NSS fit")
    axes.set_xlabel("Maturity (years)")
    axes.set_ylabel("Yield / rate (%)")
    axes.set_title("Nelson-Siegel-Svensson fit")
    axes.legend()
    axes.grid(True, alpha=0.3)
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, dpi=150)
    return figure
