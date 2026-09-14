# Independent examiner assessment

Review date: 14 September 2026. Submitted dissertation: `5a3f2ea`.
This assessment is independent of the dissertation's authorship. The existing
verification report was treated as evidence to check, not as authority.
The judgement concerns the stated educational scope, not institutional acceptance
or a numerical grade.

## Overall judgement

The mathematics and reproduced results support a sound undergraduate computational
verification study. The strongest work is the derivation of fractional-period
sensitivities and the all-maturity key-rate reconciliation argument. The weakest
part is the limited critical literature discussion and research breadth. A small
set of invented inputs, established formulas, and one curve family does not by
itself constitute a strong master's research contribution. More pages would not
resolve that limitation.

Targeted corrections improve the literature framing and financial exposition.
There is no Critical or Major mathematical finding and no engine defect found
within the reviewed conventions. The work is defensible as a conditional
verification study; empirical, global-optimisation and parameter-identification
claims would exceed the evidence.

## Findings and disposition

| Severity | Finding in submitted paper | Disposition |
| --- | --- | --- |
| Critical | None identified. | No engine correction or stop required. |
| Major (academic exposition) | Literature citations establish attribution but give too little comparison to justify the methodological position; discussion largely lists limitations. | Added a short comparison of compact parametric representation, instrument-based estimation and the calibration difficulty, plus interpretation of fit error and long-key exposure. No new models or experiments are claimed. Master's-level research breadth remains a limitation explicitly reported above. |
| Minor (mathematical terminology) | Chapter 3 says central DV01 retains finite-bump "curvature", although its second-order convexity term cancels. | Replaced by the correct odd-order nonlinear correction statement. The displayed equation and appendix proof were already correct. |
| Minor (financial exposition) | Par yield lacks an explicit no-accrual price basis; the discount-bond explanation relies on coupon versus YTM at between-coupon settlement. | Specified the conventional coupon-date par definition and based the numerical discount classification on the reported clean price. Specified dirty-price normalisation for the duration percentage. |
| Minor (NSS interpretation) | Loading roles are compressed enough to suggest separate curve turning points; equal-decay non-identification is omitted from the main text. | Defined factor loading at use, separated loading locations from turning points of the total curve, rejected structural economic interpretation, and explained the shared-loading degeneracy. |
| Minor (methodological claim) | Module separation is said to prevent rate-convention conflation. The API cannot infer a caller's economic interpretation. | Replaced the guarantee with an explicit caller responsibility. Abstract now describes missing inference from instrument prices rather than implying bootstrap is the only valid inference method. |
| Minor (presentation) | The standalone key-rate figure clips the end of its vertical axis label. | Regenerated that figure from the same public API values with a two-line label and a bounding box including the label. Numerical values and the correct NSS figure are retained. |
| Minor (reproducibility) | Git for Windows selects a PDF text driver; the regenerated PDF triggered false whitespace failures in compressed binary content. | Added paper-scoped `.gitattributes` marking PDFs binary; publication bytes are preserved and text-diff whitespace checks no longer interpret PDF streams. |
| Editorial | Displayed scenario prices and P&L can differ by one final digit when subtracted. The appendix contains a historical word count that would become stale after corrections. | Added a rounding note and removed the obsolete word-count claim. Updated the execution reference and documented the corrected figure recipe. |

## Scope and evidence read

Read all of `paper/main.tex`, `paper/references.bib`, ten chapter files, both
appendices, all three frontmatter files, `paper/verification_report.tex`,
`paper/bibliography_verification.md`, `README.md`, `AGENTS.md`,
`pyproject.toml`, all five `src/fixed_income/*.py` files, all three test files,
the illustrative CSV and ignore rules. Reviewed the original 46-page PDF as
rendered page contact sheets and both vector figures individually. Figures use
illustrative data, correctly labelled percentage rates and currency sensitivities.

Git comparison confirms that financial source, tests and example data at the
submitted revision equal the earlier audited revision `7eee019`. The existing
report is a historical record: its timing and source-line references were not
rewritten to impersonate a new original report.

## Equation audit

Every substantive display in the main text and Appendix A was checked, including
unnumbered intermediate lines. All have correct signs, powers, factors of coupon
frequency and rate conversion under the stated fixed-cash-flow assumptions.
The following register identifies the numbered equations by their LaTeX labels.

| Equation label(s) | Independent check |
| --- | --- |
| `eq:discount` | Inverting continuous accumulation gives exp(-r(T)T); rate times years is dimensionless. |
| `eq:accrual` | C=Fc/m and 0<=alpha<1; linear elapsed-period accrual is an explicit convention, not a theorem of discounting. |
| `eq:ytm-price` | Payment i is i-alpha coupon periods away; reciprocal fractional accumulation gives CF_i B^(-q_i). Clean is dirty minus yield-independent accrual. |
| `eq:price-first` | Differentiating each term produces -q_i/m and exponent -q_i-1; Macaulay is the PV-weighted q_i/m. |
| `eq:duration` | Factoring 1/B out of the first derivative gives -P'/P=D_Mac/B. Dirty-price normalisation matters. |
| `eq:convexity` | Second differentiation produces q_i(q_i+1)/m^2 and exponent -q_i-2; no factor 1/2 belongs in convexity. |
| `eq:taylor-price` | Taylor's second-order relative change uses -D_Mod delta_y plus convexity times delta_y^2/2, with cubic remainder locally. |
| `eq:ytm-dv01` | Down-minus-up divided by 2 equals -hP' plus cubic correction; 1 bp is 10^-4 decimal. Dividing by 2h would give a derivative. |
| `eq:loadings`, `eq:nss` | beta1 multiplies L1(tau1), beta2 L2(tau1), beta3 L2(tau2). Loading arguments are dimensionless. |
| `eq:nss-limits` | L1 tends to 1 at zero and 0 at infinity; L2 tends to 0 at both ends. Limits are beta0+beta1 and beta0 with fixed positive taus. |
| `eq:residuals`, `eq:rmse` | Observed-minus-fitted residuals; unweighted SSE; RMSE uses n, not an estimated residual degrees-of-freedom denominator. Decimal RMSE converts to bp by 10,000. |
| `eq:zero-price` | Actual days/365 and continuous zeros discount each cash flow separately; this does not substitute for nominal YTM discounting. |
| `eq:parallel-sign` | Derivative is -sum t_i V_i exp(-delta_r t_i), strictly negative because redemption is positive and future. |
| `eq:partition` | Nonnegative linear weights sum to one with constant endpoint tails. This is a real-arithmetic identity. |
| `eq:key-dv01`, `eq:parallel-dv01` | Same down-minus-up sign and fixed 1 bp magnitude; basis weights are dimensionless and shocks are decimal zeros. |
| `eq:app-par-sum`, `eq:app-premium` | Telescoping geometric sum proves par on coupon dates, including B=1 separately. Premium/discount sign identity at that boundary is correct. |
| `eq:app-duration`, `eq:app-convexity` | Chain rule and normalised weighted product reproduce both factors 1/(mB). |
| `eq:app-dv01` | Even Taylor terms cancel; leading correction is -h^3 P^(3)/6, positive for the stated bond. |
| `eq:central-first`, `eq:central-second` | Normalised central differences have h^2 terms -P^(3)/(6P) and P^(4)/(12P), respectively, with O(h^4) remainder. |
| `eq:series-one`, `eq:series-two` | Fifth-degree coefficients checked by expanding exp(-x); remainders are O(x^6). Separate L2 expansion prevents cancellation. |
| `eq:app-long` | Long-maturity 1/T coefficient is (beta1+beta2)tau1+beta3 tau2; remaining terms decay exponentially. |
| `eq:first-basis`, `eq:last-basis`, `eq:interior-basis`, `eq:app-partition` | Checked below first key, at every key, between adjacent keys, above last key, and the one-key convention. All cases agree with the implementation. |
| `eq:app-linear-risk` | Summing first derivatives uses sum b_j=1 and exactly recovers the parallel derivative. |
| `eq:app-key-sinh`, `eq:app-parallel-sinh` | Direct exponential subtraction yields sum V_i sinh(h t_i b_j) and sum V_i sinh(h t_i). |
| `eq:reconciliation` | Linear terms cancel; cubic coefficient is sum V_i t_i^3(sum b_j^3-1)/6. With h>0, nonnegative weights and PVs, residual is nonpositive, strictly negative for a split positive payment. |
| `eq:app-remainder` | The omitted fifth-and-higher odd terms are bounded by sum V_i (h t_i)^5 cosh(h t_i)/120. Numerical repricing rounding is additional. |

Unnumbered displays also pass: par telescoping; chain-rule steps; Taylor expansion
through fourth order; strictly negative third price derivative; exponential
series; NSS short-maturity derivative; shock-amplitude price; synthetic parameter
vector; and the explicitly dated flat-zero price. The standalone verification
report's additional displayed equations were checked, including its generic
piecewise shock, one-sided Jacobian approximation, rate-coordinate conversions,
face scaling and looser cubic reconciliation bound. No displayed equation
required mathematical correction.

## Symbols, terminology and conventions

The main document consistently uses y_YTM for nominal annual coupon-compounded
yield, r_NSS for generic fitted rates and r(T) for explicitly interpreted
continuous zeros. Coupon-based T_i and Actual/365 t_i remain distinct. Generic T,
decay tau, coupon frequency m, positive decimal bump h, accrual fraction alpha,
NSS betas, dirty price P, zero price functional and the two duration symbols have
defined meanings and notation-table entries. Observation index ell is distinct
from cash-flow i; the separately named NSS prime is explicitly a maturity
derivative. x's reuse as a generic exponential argument is declared.

All requested central terms have readable glossary definitions. Chapter text
now directly defines factor loading and sharpens par yield. No unresolved
non-obvious symbol was found in the dissertation. The historical standalone
report uses some local notation differently (for example i for observations);
its local definitions do not alter the dissertation's separate notation.

No inappropriate claim that the CSV is market or Treasury evidence was found.
Institutional literature references describe the cited studies, not the
provenance of the invented CSV. Fitting generic or par rates does not establish
zero-rate meaning; YTM, par and spot rates are not generally interchangeable.

## Numerical methodology and results

Executed the three published verification scripts after inspecting their code;
all printed results reproduced their historical record. Their finite-sum bond
price is independent of engine pricing, their synthetic observations use
90-digit exponentials, and their basis reference does not use numpy.interp.

Separately constructed a new 70-digit Decimal check using exact 90/181 accrual,
nine coupons of 2 and final payment 102. Dirty price is
98.871313082032782697442784495465...; modified duration is
4.231517692026541446412785...; convexity is
21.110444849612588960483503....
Engine absolute differences are approximately 3.05e-14 currency, 2.91e-16 years
and 1.36e-15 years squared. These are consistent with binary64 rounding.

At h=10^-4, high-precision convexity truncation alone is 5.91126738e-7 years
squared, whereas the historical binary64 total discrepancy is 3.87152067e-7.
Rounding partly cancels truncation at this step. The paper correctly reports
the computed total error, not a pure truncation error. Its seven-step table
shows initial second-order convergence and deterioration at small steps.
Existing relative test tolerances of 2e-8 for duration and 1e-6 for convexity
are reasonable regression thresholds, not achieved-accuracy claims. The
independent errors are much smaller. The long-zero-coupon test also distinguishes
central DV01 from its duration approximation.

The new high-precision risk check explicitly constructs all 60 dates, assigns
piecewise basis weights without interpolation calls, and uses the public fitted
curve only as its rate input. Residuals for decimal bumps 0.0002, 0.0001 and
0.00005 are -2.34747669562e-7, -2.93434242739e-8 and -3.66792695857e-9 currency.
Successive ratios are 8.00000938 and 8.00000235. At 1 bp the fifth-and-higher
remainder is about -1.14738e-14, inside the stated 7.08692e-14 bound.
Individual key and parallel values agree with full repricing within 3e-14.
Thus exact addition of independently repriced finite bumps would be an
incorrect requirement; the paper does not impose it.

All main-document numerical tables and quoted values were compared with the
CLI, unrounded API values or rerun verification calculations. No stale financial
value, transcription error, factor-of-10,000 error or inconsistent sign was found.
The additional maximum absolute residual is 1.52038294681 bp and RMSE is
7.82762433805005e-5 decimal, agreeing with the rounded table. Reconciliation
uses unrounded values. Its displayed summed components need not reproduce
every last digit after rounding.

## Citation integrity

All 15 entries are real, relevant and cited; no deletion or metadata correction
was justified. Author names, year, title, series/journal, edition, supplied
pages, DOIs and URLs were checked where applicable. No speculative missing
DOI or page range was added. Metadata validation does not imply complete
reading of every textbook.

- Nelson and Siegel: [publisher's JSTOR issue](https://www.jstor.org/stable/i340505)
  confirms 1987, 60(4), 473-489 and names; Crossref confirms DOI
  [10.1086/296409](https://api.crossref.org/works/10.1086/296409).
  Crossref supplies only the starting page, so the full range comes from JSTOR.
- Svensson: [NBER record](https://www.nber.org/papers/w4871) confirms
  September 1994, WP 4871 and DOI 10.3386/w4871. The accessible
  [author-hosted IMF version](https://larseosvensson.se/files/papers/estimating-and-interpreting-forward-rates-sweden-1992-1994-IMFwp94-114.pdf),
  section III, corroborates the second curvature term. Series versions are
  not mixed in the bibliography.
- BIS: [institutional record](https://www.bis.org/publ/bppdf/bispap25.htm)
  confirms BIS Papers 25, 2005, title and institutional source; overview
  supports the distinction between rates and estimation conventions.
- Macaulay: [NBER chapter/volume record](https://www.nber.org/books-and-chapters/some-theoretical-problems-suggested-movements-interest-rates-bond-yields-and-stock-prices-united/some-theoretical-and-practical-difficulties-comparing-long-term-interest-rates-different-and)
  confirms author, full volume title, 1938 and NBER.
- Tuckman and Serrat: [Wiley third-edition record](https://uat.store.wiley.com/en-us/fixed-income-securities-tools-for-today%27s-markets-3rd-edition-p-9781118133965)
  confirms both authors, title, edition and 2011.
- Ho: [Crossref](https://api.crossref.org/works/10.3905/jfi.1992.408049)
  confirms title and subtitle, Thomas S. Y. Ho, 1992, 2(2), 29-44.
  No claim is made that Ho used this project's precise endpoint basis.
- Gilli, Große and Schumann: [original working paper](https://www.uni-giessen.de/static_files/pcms/jlu/comisef/files/wps031.pdf)
  title page confirms WPS-031, 30 March 2010 and names; opening sections
  and collinearity discussion support the stated calibration limitations.
- Gürkaynak, Sack and Wright: [journal record](https://www.sciencedirect.com/science/article/pii/S0304393207000840)
  and [Crossref](https://api.crossref.org/works/10.1016/j.jmoneco.2007.06.029)
  confirm 2007, 54(8), 2291-2304 and DOI.
- Anderson and Sleath: [Bank of England](https://www.bankofengland.co.uk/working-paper/2001/new-estimates-of-the-uk-real-and-nominal-yield-curves)
  confirms WP 126, 2001, names and the spline-based approach.
- Nocedal and Wright: [Springer](https://link.springer.com/book/10.1007/978-0-387-40065-5)
  confirms authors, title, second edition, 2006 and DOI.
- Branch, Coleman and Li: [SIAM journal record](https://epubs.siam.org/doi/abs/10.1137/S1064827595289108?journalCode=sjoce3)
  confirms 1999, 21(1), 1-23, names, title and DOI. Later online posting is not
  the publication year.
- Higham: [author's book record](https://nhigham.com/accuracy-and-stability-of-numerical-algorithms/)
  and [SIAM](https://epubs.siam.org/doi/10.1137/1.9780898718027)
  confirm second edition, 2002, title and DOI.
- Harris et al.: [NumPy's citation record](https://numpy.org/citing-numpy/)
  confirms the full author list, 2020, Nature 585(7825), 357-362 and DOI.
- Virtanen et al.: [SciPy's citation record](https://scipy.org/citing-scipy/)
  confirms the full author list and contributor credit, 2020, Nature Methods
  17(3), 261-272 and DOI.
- SciPy least_squares: [official manual](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)
  confirms objective, default algorithm, Jacobian, stopping and evaluation-count
  semantics. Online manual identifies version 1.18.0; installed 1.18.1 is
  separately recorded. No invented publication year is used.

Some direct web fetches were restricted. Authoritative indexed records,
author-hosted originals and read-only Crossref requests supplied the alternatives.
No financial observations were downloaded.

## Reproducibility and final presentation validation

Editable installation with the documented `pip install -e ".[dev]"` succeeded,
and package import resolved to this repository. An initial optional attempt with
build isolation disabled failed because setuptools was absent from the runtime
environment; the documented isolated build resolved it without project changes.
Python 3.12.10 and installed library versions match Appendix B.

The required pytest run passed: **234 passed in 11.52s**.
The bond, curve and risk CLI commands each exited successfully.
All three report scripts and the separate high-precision examiner check passed.

The required clean build (`latexmk -C -outdir=build main.tex`, then the
specified PDF command) completed successfully with pdfLaTeX and Biber.
The final LaTeX log contains no warnings, undefined references/citations,
duplicate-label messages, overfull or underfull boxes; Biber reports no warnings
or errors. All 15 bibliography keys resolve and are cited; the equation register
covers all 37 numbered labels. The rendered final PDF has **46 pages**. Both
figures and all rendered page layouts were inspected; the corrected key-rate
label is fully visible and tables/equations show no clipping or overlap.
The final publication PDF was copied only after the successful build.

The build tools printed environment-level Perl locale fallback and MiKTeX update
reminders. These did not prevent compilation and are distinct from document or
bibliography warnings. No toolchain upgrade was needed.

`git diff --check` passed. Financial source, tests, dependencies and inputs are
untouched. Only paper files are eligible for the authorised correction commit;
the staged diff is inspected separately before committing. The final commit,
push result and repository status are reported in the delivery message.

## Corrected key-rate figure reproduction

Run this Python block through the PowerShell stdin wrapper documented in the
standalone verification report, from the repository root. It only renders
existing public API results; it adds no financial functionality.

```python
from datetime import date
from pathlib import Path
import matplotlib as mpl
from matplotlib.figure import Figure
import numpy as np
from fixed_income import FixedRateBond, fit_nss, key_rate_dv01

data = np.genfromtxt(Path("examples/illustrative_curve.csv"),
                     delimiter=",", names=True)
curve = fit_nss(data["maturity_years"], data["rate"]).curve
bond = FixedRateBond(date(2025, 4, 15), date(2055, 1, 15), 0.04)
values = key_rate_dv01(bond, curve)
with mpl.rc_context({"font.family": "serif", "font.size": 11}):
    figure = Figure(figsize=(8, 4.5), layout="constrained")
    axes = figure.subplots()
    axes.bar([str(int(v.tenor_years)) for v in values],
             [v.dv01 for v in values], color="#244760", width=0.6)
    axes.set_xlabel("Key maturity (years)")
    axes.set_ylabel("Key-rate DV01\n(currency for a 1 bp bump; face 100)")
    axes.set_ylim(bottom=0)
    axes.set_axisbelow(True)
    axes.grid(axis="y", alpha=0.25)
    for edge in ("top", "right"):
        axes.spines[edge].set_visible(False)
    figure.savefig(Path("paper/figures/key_rate_dv01.pdf"),
                   bbox_inches="tight", pad_inches=0.08)
print("Key-rate figure regenerated from unchanged public APIs")
```
