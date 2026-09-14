# Bibliographic verification and source-use record

Checked on 14 September 2026. There are 15 references in `references.bib`.
This is an editorial research record, not dissertation prose.

Bibliographic fields were checked against original institutional records,
publisher pages, official scientific-project citation records and Crossref DOI
metadata. Search snippets were used to locate sources; uncertain details were
omitted. Publication year is distinguished from later online posting or page
update dates. Source titles retain published spelling; the dissertation uses
British English. No text passages or source figures have been reproduced.

Metadata verification is not a claim of complete reading. The claim boundaries
below distinguish available source evidence from the fuller reading needed
before detailed dissertation prose or pinpoint citations. The internal
verification report is project evidence, not an external academic publication.

| Key | Verified record and fields | Intended role and reading boundary |
| --- | --- | --- |
| `nelson1987` | [JSTOR publisher issue contents](https://www.jstor.org/stable/i340505) confirms authors, title, 1987, The Journal of Business 60(4), 473–489. [Crossref](https://api.crossref.org/works/10.1086/296409) confirms DOI 10.1086/296409 and journal metadata. [Primary-paper scan hosted by Bocconi](https://didattica.unibocconi.it/mypage/upload/NELSON_SIEGEL20081008161957.PDF) located. | Chapter 4: original parsimonious model. Verify notation mapping against the original equations when drafting; do not import its empirical findings into this study. |
| `svensson1994` | [NBER original record](https://www.nber.org/papers/w4871) confirms Lars E. O. Svensson, full title, September 1994, Working Paper 4871 and DOI 10.3386/w4871. [IMF archive](https://archivescatalog.imf.org/Details/ArchiveExecutive/125115208) confirms the equivalent WP/94/114 record and author. | Chapter 4: Svensson extension. Cite the NBER version consistently; do not combine its DOI with the IMF series number or count duplicate versions as separate sources. |
| `bis2005` | [BIS publication record](https://www.bis.org/publ/bppdf/bispap25.htm) confirms corporate authorship, title, BIS Papers 25 and October 2005; the overview explains NS/NSS and estimation conventions. | Chapters 1, 2, 4 and 9: institutional curve-estimation framework and rate interpretation. No data download or claim that the engine replicates central-bank estimation. |
| `macaulay1938` | [NBER chapter record](https://www.nber.org/books-and-chapters/some-theoretical-problems-suggested-movements-interest-rates-bond-yields-and-stock-prices-united/introduction) and [NBER front matter](https://www.nber.org/system/files/chapters/c6339/c6339.pdf) identify Frederick R. Macaulay, full book title, publisher NBER and 1938. The volume URL is given in NBER's front matter. | Chapters 2–3: historical duration foundation. Inspect the relevant original duration discussion before adding historical detail or pinpoint pages; contemporary conventions also use Tuckman–Serrat. No uncertain page range, edition or DOI is supplied. |
| `tuckman2011` | [Wiley third-edition record](https://uat.store.wiley.com/en-us/fixed-income-securities-tools-for-today%27s-markets-3rd-edition-p-9781118133965) confirms Bruce Tuckman, Angel Serrat, title, third edition and October 2011; [Wiley companion](https://bcs.wiley.com/he-bcs/Books?action=index&bcsId=6676&itemId=0470904038) corroborates authors/edition. | Chapters 2–3: bond cash flows, price/yield, discount factors, spot versus YTM, duration, convexity and DV01. Publisher description supports the reading allocation; consult the actual relevant chapters before attaching detailed page citations. No claim of full-text access. |
| `ho1992` | [Crossref DOI record](https://api.crossref.org/works/10.3905/jfi.1992.408049) confirms Thomas S. Y. Ho, title plus subtitle, 1992, The Journal of Fixed Income 2(2), 29–44 and DOI. Publisher/DOI page was access-restricted. | Chapter 5: key-rate sensitivity concept. Metadata verified; inspect full paper before attributing particular basis functions or finite-bump conventions. The dissertation's exact basis and reconciliation proof come from the implementation and independent record. |
| `gilli2010` | [Institution-hosted original working paper](https://www.uni-giessen.de/static_files/pcms/jlu/comisef/files/wps031.pdf), title page and opening sections: Manfred Gilli, Stefan Große, Enrico Schumann; 30 March 2010; COMISEF WPS-031. | Chapters 4 and 9: multiple local optima, collinearity/conditioning and unstable parameter estimates. The paper's differential-evolution experiments are not the implemented optimiser and are not proposed development. Cite this verified working version; do not invent journal metadata or borrow another version's DOI. |
| `gurkaynak2007` | [Crossref](https://api.crossref.org/works/10.1016/j.jmoneco.2007.06.029) confirms authors, title, 2007, Journal of Monetary Economics 54(8), 2291–2304 and DOI. [Federal Reserve paper record](https://www.federalreserve.gov/econres/feds/the-us-treasury-yield-curve-1961-to-the-present.htm) corroborates authors/title and explains the discount-function context. | Chapters 2, 4 and 9: instrument-based term-structure estimation versus generic curve fitting. The bibliography cites the journal article, not the later-updated FEDS page as a 2011 paper. No Treasury observations are imported. |
| `anderson2001` | [Bank of England](https://www.bankofengland.co.uk/working-paper/2001/new-estimates-of-the-uk-real-and-nominal-yield-curves) confirms Nicola Anderson, John Sleath, title, Working Paper 126 and 28 March 2001. | Chapters 2 and 9: estimation choices, smoothness and interpretation. This is a spline-based institutional comparator, not an assertion that the engine implements splines. |
| `nocedal2006` | [Springer](https://link.springer.com/book/10.1007/978-0-387-40065-5) confirms Jorge Nocedal, Stephen J. Wright, Numerical Optimization, second edition, 2006, publisher and DOI. | Chapters 4, 6 and 9: nonlinear least squares, local minima, scaling and stopping. Consult relevant chapters for detailed derivations; no full-text reading claim. |
| `branch1999` | [SIAM journal record](https://epubs.siam.org/doi/abs/10.1137/S1064827595289108) confirms Mary Ann Branch, Thomas F. Coleman, Yuying Li; title; 21(1), 1–23; 1999; DOI. Later online posting is not the publication year. | Chapter 6: methodological basis for bound-constrained trust-region methods, linked by SciPy documentation. The engine uses SciPy's dense six-parameter default implementation, not every algorithmic option in this paper. |
| `higham2002` | [SIAM book](https://epubs.siam.org/doi/10.1137/1.9780898718027) and [front matter](https://epubs.siam.org/doi/abs/10.1137/1.9780898718027.fm) confirm Nicholas J. Higham, title, second edition, 2002, publisher and DOI. | Chapters 4, 6 and 7: finite-precision arithmetic, cancellation, conditioning and numerical stability. Exact project error calculations remain grounded in the independent report. |
| `harris2020` | [Official NumPy citation](https://numpy.org/citing-numpy/) supplies the full author list, Nature 585(7825), 357–362, 2020 and DOI 10.1038/s41586-020-2649-2. | Chapter 6: array programming and the actual NumPy computations. Full author list retained; no unnecessary software bibliography. |
| `virtanen2020` | [Official SciPy citation](https://scipy.org/citing-scipy/) supplies full authors and collective contributor credit, Nature Methods 17(3), 261–272, 2020 and DOI 10.1038/s41592-019-0686-2. | Chapter 6: SciPy's scientific-computing role; algorithm-specific discussion also cites Branch and the manual. |
| `scipyLeastSquares` | [Official least_squares manual](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html), accessed 14 September 2026: title, project author, algorithm, objective, defaults and references. No publication year invented. Online heading: 1.18.0. | Chapter 6: trust-region reflective default, two-point Jacobian, scaling, linear loss, stopping criteria and evaluation-count meaning. Locally inspected SciPy 1.18.1 signature agrees; record the version distinction rather than equating them. |

Before expanding the prose, inspect the specific source passages needed for
new claims; add pinpoint citations only after verifying the relevant pages.
The original-model, institutional-estimation, textbook, numerical-analysis
and implementation sources have distinct roles. A fitted curve's residual
does not justify the economic interpretation of its input rates.

The completed dissertation cites all 15 bibliography entries selectively;
no wildcard citation is used. No university,
degree, supervisor, candidate number or submission date has been invented.

## Completed dissertation source-use check

The original metadata audit above is retained as the planning-phase record.
During authoring, the relevant Svensson estimation discussion was checked in
the [author-hosted IMF version, section III](https://larseosvensson.se/files/papers/estimating-and-interpreting-forward-rates-sweden-1992-1994-IMFwp94-114.pdf).
It distinguishes spot discounting from coupon-bond yields and introduces the
additional curvature term. The bibliography consistently retains the verified
NBER version. Gilli, Grosse and Schumann's opening modelling/calibration
sections corroborate the loading form and the local-optimum/conditioning
limitations. The BIS overview and the official SciPy algorithm discussion
were rechecked. No external empirical results or alternative optimisation
algorithms have been attributed to this engine.

Detailed project equations and numerical claims are grounded in direct source
inspection, the preserved independent verification report, and fresh public-API
execution. Textbook and historical citations supply context, without invented
pinpoint citations or a claim of complete full-text reading. The final citation
audit confirms that every key resolves and all 15 entries are cited.
