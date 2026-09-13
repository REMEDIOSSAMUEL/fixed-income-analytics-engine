"""Deterministic NSS formula, calibration, failure and integration checks."""

from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from fixed_income import NSSCurve, NSSFitResult, fit_nss, plot_nss
from fixed_income.cli import main


@pytest.fixture
def curve() -> NSSCurve:
    return NSSCurve(0.04, -0.025, 0.03, -0.012, 1.4, 6.5)


@pytest.fixture
def observations(curve: NSSCurve) -> tuple[np.ndarray, np.ndarray]:
    maturities = np.geomspace(0.05, 40.0, 40)
    return maturities, curve.yield_rate(maturities)


@pytest.fixture(scope="module")
def synthetic_fit() -> NSSFitResult:
    maturities = np.geomspace(0.05, 40.0, 40)
    known = NSSCurve(0.04, -0.025, 0.03, -0.012, 1.4, 6.5)
    return fit_nss(maturities, known.yield_rate(maturities))


def _reference(curve: NSSCurve, maturity: float) -> float:
    # Independent 70-digit Decimal evaluation, including extremely short tenors.
    with localcontext() as context:
        context.prec = 70
        t = Decimal(str(maturity))
        x1, x2 = t / Decimal(str(curve.tau1)), t / Decimal(str(curve.tau2))
        e1, e2 = (-x1).exp(), (-x2).exp()
        l1, l3 = (1 - e1) / x1, (1 - e2) / x2 - e2
        betas = [Decimal(str(getattr(curve, f"beta{i}"))) for i in range(4)]
        return float(betas[0] + betas[1] * l1 + betas[2] * (l1 - e1) + betas[3] * l3)


def test_scalar_evaluation(curve: NSSCurve) -> None:
    actual = curve.yield_rate(4.0)
    assert isinstance(actual, float)
    assert actual == pytest.approx(_reference(curve, 4.0), rel=1e-14)
    assert curve.yield_rate(np.array(4.0)) == actual


@pytest.mark.parametrize("shape", [(6,), (2, 3), (1, 2, 3)])
def test_vector_evaluation_and_shape(curve: NSSCurve, shape: tuple[int, ...]) -> None:
    maturities = np.array([0.1, 0.5, 1, 3, 10, 30]).reshape(shape)
    actual = curve.yield_rate(maturities)
    assert isinstance(actual, np.ndarray)
    assert actual.shape == shape
    expected = np.array([_reference(curve, t) for t in maturities.flat]).reshape(shape)
    np.testing.assert_allclose(actual, expected, rtol=1e-14, atol=1e-16)


@pytest.mark.parametrize("maturity", [1e-18, 1e-12, 1e-8, 0.000999, 0.001, 0.001001])
@pytest.mark.parametrize("factor", ["beta1", "beta2", "beta3"])
def test_short_maturity_loadings(maturity: float, factor: str) -> None:
    # Isolating factors catches cancellation in L2 hidden by a nonzero beta0.
    curve = replace(NSSCurve(0, 0, 0, 0, 1, 2), **{factor: 1.0})
    assert curve.yield_rate(maturity) == pytest.approx(
        _reference(curve, maturity), rel=2e-12, abs=0.0
    )


def test_extreme_positive_ratios() -> None:
    curve = NSSCurve(0.04, -0.02, 0.01, 0.03, 1e-300, 1e-300)
    assert curve.yield_rate(1e300) == 0.04
    curve = replace(curve, tau1=1e300, tau2=1e300)
    assert curve.yield_rate(1e-300) == 0.02


@pytest.mark.parametrize("field", ["tau1", "tau2"])
@pytest.mark.parametrize("value", [0, -1, np.nan, np.inf, -np.inf, True, "1"])
def test_invalid_taus(curve: NSSCurve, field: str, value: object) -> None:
    with pytest.raises(ValueError, match="tau"):
        replace(curve, **{field: value})


@pytest.mark.parametrize("field", ["beta0", "beta1", "beta2", "beta3"])
@pytest.mark.parametrize("value", [np.nan, np.inf, True, "0.03"])
def test_invalid_betas(curve: NSSCurve, field: str, value: object) -> None:
    with pytest.raises(ValueError, match=field):
        replace(curve, **{field: value})


@pytest.mark.parametrize("value", [0, -1, np.nan, np.inf, [1, 0], [1, np.nan], 1j, True])
def test_invalid_maturities(curve: NSSCurve, value: object) -> None:
    with pytest.raises(ValueError, match="maturities"):
        curve.yield_rate(value)


@pytest.mark.parametrize(
    ("maturities", "rates", "message"),
    [
        ([], [], "nonempty"),
        ([1, 2, 3], [0.03] * 3, "six distinct"),
        ([1] * 6, [0.03] * 6, "six distinct"),
        (list(range(1, 7)), [0.03] * 5, "identical lengths"),
        ([[1, 2, 3, 4, 5, 6]], [0.03] * 6, "1D"),
        (list(range(1, 7)), [[0.03] * 6], "1D"),
        (1, 0.03, "1D"),
        ([0, 1, 2, 3, 4, 5], [0.03] * 6, "positive"),
        ([-1, 1, 2, 3, 4, 5], [0.03] * 6, "positive"),
        ([np.nan, 1, 2, 3, 4, 5], [0.03] * 6, "finite"),
        ([np.inf, 1, 2, 3, 4, 5], [0.03] * 6, "finite"),
        (list(range(1, 7)), [0.03] * 5 + [np.nan], "finite"),
        (list(range(1, 7)), [0.03] * 5 + [np.inf], "finite"),
        (list(range(1, 7)), [0.03] * 5 + [1j], "real"),
    ],
)
def test_invalid_calibration_data(maturities: object, rates: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        fit_nss(maturities, rates)


def test_noiseless_curve_fit(synthetic_fit: NSSFitResult) -> None:
    # 1e-8 decimal = 0.0001 bp; compare curves, not non-identifiable parameters.
    assert synthetic_fit.rmse < 1e-8
    np.testing.assert_allclose(
        synthetic_fit.fitted_rates, synthetic_fit.observed_rates, rtol=0, atol=5e-8
    )


@pytest.mark.parametrize(
    "known",
    [
        NSSCurve(-0.005, -0.015, 0.02, 0.008, 0.8, 4.0),
        NSSCurve(0.025, 0.035, -0.02, 0.015, 5.5, 1.3),
        NSSCurve(0.035, 0, 0, 0, 1, 5),
    ],
)
def test_other_synthetic_shapes(known: NSSCurve) -> None:
    maturities = np.geomspace(0.1, 30, 30)
    result = fit_nss(maturities, known.yield_rate(maturities))
    assert result.rmse < 1e-8


def test_result_metadata_and_units(synthetic_fit: NSSFitResult) -> None:
    result = synthetic_fit
    assert isinstance(result, NSSFitResult)
    assert isinstance(result.curve, NSSCurve)
    np.testing.assert_array_equal(result.fitted_rates, result.curve.yield_rate(result.maturities))
    np.testing.assert_array_equal(result.residuals, result.observed_rates - result.fitted_rates)
    assert result.rmse == pytest.approx(np.sqrt(np.mean(result.residuals**2)), abs=1e-18)
    assert result.rmse_bps == result.rmse * 10_000
    assert result.success is True
    assert result.status in (1, 2, 3, 4)
    assert result.message
    assert result.nfev > 0
    assert 1 <= result.starts_succeeded <= result.starts_attempted == 6
    assert 0.01 <= result.curve.tau1 <= 100
    assert 0.01 <= result.curve.tau2 <= 100


def test_repeated_calibration_is_deterministic(
    observations: tuple[np.ndarray, np.ndarray], synthetic_fit: NSSFitResult,
) -> None:
    repeated = fit_nss(*observations)
    np.testing.assert_array_equal(repeated.fitted_rates, synthetic_fit.fitted_rates)
    assert repeated.curve == synthetic_fit.curve
    assert repeated.rmse == synthetic_fit.rmse
    assert repeated.nfev == synthetic_fit.nfev
    assert repeated.status == synthetic_fit.status


def test_noisy_fit_preserves_order_and_owns_data(observations: tuple[np.ndarray, np.ndarray]) -> None:
    maturities, rates = observations
    maturities = maturities[::-1].copy()
    rates = rates[::-1] + 0.0001 * np.cos(np.arange(rates.size))
    result = fit_nss(maturities, rates)
    np.testing.assert_array_equal(result.maturities, maturities)
    np.testing.assert_array_equal(result.observed_rates, rates)
    assert 0 < result.rmse < 0.0001
    assert result.rmse_bps == pytest.approx(np.sqrt(np.mean(result.residuals**2)) * 10_000)
    rates[:] = 0
    maturities[:] = 1
    assert np.all(result.observed_rates != 0)
    assert np.any(result.maturities != 1)
    for array in (result.maturities, result.observed_rates, result.fitted_rates, result.residuals):
        assert not array.flags.writeable


@pytest.mark.parametrize("failure", ["unsuccessful", "nonfinite", "bounds", "exception"])
def test_failed_calibration_is_clear(monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    calls = []

    def fail(*args: object, **kwargs: object) -> SimpleNamespace:
        calls.append(1)
        if failure == "exception":
            raise ValueError("simulated optimizer error")
        x = np.array([0.04, 0, 0, 0, 1, 5], dtype=float)
        if failure == "nonfinite":
            x[0] = np.nan
        if failure == "bounds":
            x[4] = 101
        return SimpleNamespace(success=failure != "unsuccessful", message="test failure", x=x)

    monkeypatch.setattr("fixed_income.curves.least_squares", fail)
    with pytest.raises(RuntimeError, match="no successful valid fit from 6 starts"):
        fit_nss(np.arange(1, 7), np.full(6, 0.04))
    assert len(calls) == 6


def test_selects_best_valid_success_and_known_rmse(monkeypatch: pytest.MonkeyPatch) -> None:
    # Unsuccessful exact fits must not beat successful candidates.
    levels = [0.03, 0.04, 0.039, np.nan, 0.035, 0.038]
    calls = []

    def candidate(*args: object, **kwargs: object) -> SimpleNamespace:
        index = len(calls)
        calls.append(1)
        return SimpleNamespace(
            x=np.array([levels[index], 0, 0, 0, 1, 5]),
            success=index != 1, status=2, message=f"start {index}", nfev=index + 10,
        )

    monkeypatch.setattr("fixed_income.curves.least_squares", candidate)
    result = fit_nss(np.arange(1, 7), np.full(6, 0.04))
    assert result.curve.beta0 == 0.039
    np.testing.assert_allclose(result.residuals, 0.001, rtol=0, atol=1e-17)
    assert result.rmse == pytest.approx(0.001)
    assert result.rmse_bps == pytest.approx(10.0)
    assert result.message == "start 2"
    assert result.nfev == 12
    assert result.starts_succeeded == 4


def test_plot(curve: NSSCurve, tmp_path: Path) -> None:
    maturities = np.array([5, 0.5, 2, 10])
    rates = curve.yield_rate(maturities)
    destination = tmp_path / "plots" / "curve.png"
    figure = plot_nss(maturities, rates, curve, destination)
    assert destination.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    axes = figure.axes[0]
    assert axes.get_xlabel() == "Maturity (years)"
    assert "%" in axes.get_ylabel()
    np.testing.assert_allclose(axes.collections[0].get_offsets()[:, 1], rates * 100)
    grid = axes.lines[0].get_xdata()
    assert np.all(np.diff(grid) > 0)
    assert grid[0] == 0.5 and grid[-1] == 10
    np.testing.assert_allclose(axes.lines[0].get_ydata(), curve.yield_rate(grid) * 100)


def test_curve_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path,
) -> None:
    # A temporary repository-shaped directory keeps generated files out of source.
    example = Path(__file__).resolve().parents[1] / "examples" / "illustrative_curve.csv"
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / example.name).write_bytes(example.read_bytes())
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["fixed-income", "curve"])
    main()
    output = capsys.readouterr().out
    for label in (
        "invented", "no market data", "beta0:", "beta1:", "beta2:", "beta3:",
        "tau1:", "tau2:", "Optimizer success: True", "Optimizer status:",
        "RMSE (decimal rate):", "RMSE (basis points):", "not a bootstrapped zero curve",
    ):
        assert label in output
    assert (tmp_path / "outputs" / "yield_curve.png").is_file()
