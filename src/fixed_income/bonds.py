"""Regular fixed-rate bonds priced from nominal annual decimal YTM.

YTM is compounded at coupon frequency (1 or 2). Prices, accrued interest,
and DV01 are currency amounts for the supplied face value, not percentages.
Durations are years; convexity is (d² dirty_price / dy²) / dirty_price,
where y is annual decimal YTM (conventionally expressed in years squared).
This module does not discount from an explicit zero curve.
"""

from dataclasses import dataclass
from datetime import date
from math import fsum, isfinite
from numbers import Real

from dateutil.relativedelta import relativedelta


def _finite_real(name: str, value: float) -> float:
    """Validate and promote real scalars before cash-flow or yield arithmetic."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not isfinite(result):
        raise ValueError(f"{name} must be a finite real number")
    return result


@dataclass(frozen=True)
class BondAnalytics:
    """YTM analytics for the bond's face value.

    ytm is a nominal annual decimal rate compounded at coupon frequency.
    Accrued interest, prices and DV01 are currency amounts. Durations are
    years. Convexity is the normalized second derivative with respect to
    annual decimal YTM, conventionally in years squared. DV01 uses full
    central dirty-price repricing at +/-0.0001 annual YTM.
    """

    ytm: float
    accrued_interest: float
    dirty_price: float
    clean_price: float
    macaulay_duration: float
    modified_duration: float
    convexity: float
    dv01: float


@dataclass(frozen=True)
class FixedRateBond:
    """An option-free bond with regular maturity-anchored coupons.

    coupon_rate is an annual decimal rate; face_value is a currency amount.
    frequency is 1 (annual) or 2 (semiannual). Each date is maturity minus
    an integer multiple of 12/frequency calendar months using relativedelta;
    nonexistent days clip to month end without shifting the maturity anchor.
    No separate end-of-month, holiday, business-day, irregular-coupon or
    ex-coupon rules apply.

    Settlement on a coupon date excludes that day's payment and starts a
    new accrual period with zero accrued interest. Otherwise accrual is
    actual elapsed days / actual days in the complete coupon period.
    YTM belongs to each analytics call, not to the security. Accepted real
    scalars are converted to Python floats before cash-flow and yield arithmetic.
    """

    settlement_date: date
    maturity_date: date
    coupon_rate: float
    face_value: float = 100.0
    frequency: int = 2

    def __post_init__(self) -> None:
        if type(self.settlement_date) is not date or type(self.maturity_date) is not date:
            raise ValueError("settlement_date and maturity_date must be datetime.date values")
        if self.maturity_date <= self.settlement_date:
            raise ValueError("maturity_date must be after settlement_date")
        object.__setattr__(self, "face_value", _finite_real("face_value", self.face_value))
        object.__setattr__(self, "coupon_rate", _finite_real("coupon_rate", self.coupon_rate))
        if self.face_value <= 0:
            raise ValueError("face_value must be positive")
        if self.coupon_rate < 0:
            raise ValueError("coupon_rate must be nonnegative")
        if type(self.frequency) is not int or self.frequency not in (1, 2):
            raise ValueError("frequency must be 1 (annual) or 2 (semiannual)")
        if not isfinite(self.face_value + self.face_value * self.coupon_rate / self.frequency):
            raise ValueError("coupon and principal cash flows must be finite")
        # Validate that the preceding coupon fits Python's calendar range.
        self._coupon_dates()

    def _coupon_dates(self) -> tuple[date, ...]:
        """Return the preceding/on-settlement coupon followed by future coupons."""
        dates = [self.maturity_date]
        periods = 1
        while dates[-1] > self.settlement_date:
            try:
                dates.append(
                    self.maturity_date
                    - relativedelta(months=periods * (12 // self.frequency))
                )
            except (ValueError, OverflowError) as exc:
                raise ValueError("coupon schedule exceeds datetime.date range") from exc
            periods += 1
        return tuple(reversed(dates))

    @property
    def previous_coupon_date(self) -> date:
        """Coupon on or immediately before settlement."""
        return self._coupon_dates()[0]

    @property
    def next_coupon_date(self) -> date:
        """First coupon strictly after settlement."""
        return self._coupon_dates()[1]

    def coupon_schedule(self) -> tuple[date, ...]:
        """Future payment dates, strictly after settlement, including maturity."""
        return self._coupon_dates()[1:]

    def _accrual_fraction(self) -> float:
        previous, following = self._coupon_dates()[:2]
        return (self.settlement_date - previous).days / (following - previous).days

    def accrued_interest(self) -> float:
        """Currency accrued: periodic coupon times actual/actual period fraction."""
        coupon = self.face_value * self.coupon_rate / self.frequency
        return coupon * self._accrual_fraction()

    def _discount_base(self, ytm: float) -> float:
        ytm = _finite_real("ytm", ytm)
        base = 1.0 + ytm / self.frequency
        if base <= 0:
            raise ValueError("ytm must satisfy 1 + ytm / frequency > 0")
        return base

    def _present_values(self, ytm: float) -> tuple[tuple[float, float], ...]:
        """Pairs of fractional coupon-period exponent q and discounted cash flow."""
        base = self._discount_base(ytm)
        dates = self._coupon_dates()
        alpha = (self.settlement_date - dates[0]).days / (dates[1] - dates[0]).days
        w = 1.0 - alpha
        coupon = self.face_value * self.coupon_rate / self.frequency
        terms = []
        try:
            for index in range(len(dates) - 1):
                q = w + index
                cash_flow = coupon
                if index == len(dates) - 2:
                    cash_flow += self.face_value
                terms.append((q, cash_flow * base ** (-q)))
            price = fsum(pv for _, pv in terms)
        except OverflowError as exc:
            raise ValueError("ytm produces a price outside floating-point range") from exc
        if not isfinite(price) or price <= 0:
            raise ValueError("ytm must produce a finite positive dirty price")
        return tuple(terms)

    def dirty_price(self, ytm: float) -> float:
        """Currency price: sum CF_i * (1 + ytm/m)^(-q_i), q_i = 1-alpha+i-1.

        ytm is nominal annual decimal YTM compounded m=frequency times/year.
        """
        return fsum(pv for _, pv in self._present_values(ytm))

    def clean_price(self, ytm: float) -> float:
        """Dirty price minus accrued interest, in currency for this face value.

        ytm is nominal annual decimal YTM compounded at coupon frequency.
        """
        return self.dirty_price(ytm) - self.accrued_interest()

    def macaulay_duration(self, ytm: float) -> float:
        """PV-weighted time in years, with t_i=q_i/frequency.

        ytm is nominal annual decimal YTM compounded at coupon frequency.
        """
        terms = self._present_values(ytm)
        price = fsum(pv for _, pv in terms)
        return fsum((q / self.frequency) * (pv / price) for q, pv in terms)

    def modified_duration(self, ytm: float) -> float:
        """Macaulay duration / (1 + ytm/frequency), in years.

        Equals -(d dirty_price / dy) / dirty_price for annual decimal YTM y,
        nominally compounded at coupon frequency.
        """
        return self.macaulay_duration(ytm) / self._discount_base(ytm)

    def convexity(self, ytm: float) -> float:
        """Normalized second derivative wrt annual decimal YTM (years squared).

        For m=frequency, q_i=1-alpha+i-1 and nominal annual decimal YTM y:
        d²P/dy² = sum CF_i*q_i*(q_i+1)/m² * (1+y/m)^(-q_i-2).
        Return (d²P/dy²)/P using dirty P, with no factor of 1/2.
        """
        terms = self._present_values(ytm)
        price = fsum(pv for _, pv in terms)
        base = self._discount_base(ytm)
        return fsum(
            (pv / price) * (q / self.frequency / base)
            * ((q + 1) / self.frequency / base)
            for q, pv in terms
        )

    def dv01(self, ytm: float) -> float:
        """Currency sensitivity: [P(y-0.0001)-P(y+0.0001)]/2, using dirty P.

        y is nominal annual decimal YTM compounded at coupon frequency.
        One basis point is exactly 0.0001. Both shifted yields must be valid.
        A conventional positive-duration bond has positive DV01.
        """
        ytm = _finite_real("ytm", ytm)
        self._discount_base(ytm)
        return (self.dirty_price(ytm - 0.0001) - self.dirty_price(ytm + 0.0001)) / 2

    def analytics(self, ytm: float) -> BondAnalytics:
        """All measures at nominal annual decimal YTM and coupon compounding.

        Currency measures use this face value; durations are years and
        convexity is years squared. Requires valid yields at ytm +/-1 bp.
        """
        ytm = _finite_real("ytm", ytm)
        dirty = self.dirty_price(ytm)
        accrued = self.accrued_interest()
        return BondAnalytics(
            ytm=ytm,
            accrued_interest=accrued,
            dirty_price=dirty,
            clean_price=dirty - accrued,
            macaulay_duration=self.macaulay_duration(ytm),
            modified_duration=self.modified_duration(ytm),
            convexity=self.convexity(ytm),
            dv01=self.dv01(ytm),
        )
