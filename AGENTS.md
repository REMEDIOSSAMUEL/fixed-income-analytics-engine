# Agent contract

This educational/research project is intentionally restricted to exactly three
capabilities: fixed-rate bond analytics, Nelson-Siegel-Svensson yield-curve
modelling, and interest-rate/curve-risk analytics. Scope cannot expand without
explicit user instruction.

Do not implement or scaffold PCA, relative value, rich/cheap analysis, z-scores,
butterfly strategies, trading signals, backtesting, VaR, expected shortfall,
portfolio optimisation, machine learning, forecasting, execution, brokers,
databases, REST APIs, web applications, dashboards, notebooks, or live data
downloads. Do not add speculative abstractions. This is not a production pricing
or trading platform.

## Financial and implementation rules

- Rates are decimal values internally; 0.05 means 5%, and 0.0001 means 1 bp.
- Public APIs and documentation must state units and compounding conventions.
  Never silently mix decimals, percentages, percentage points, and basis points.
- Prefer transparent financial formulas over opaque abstractions.
- Keep conventional YTM pricing distinct from explicit zero-curve discounting.
- Default face value should generally be 100. Reject invalid values clearly.
- Numerical functionality requires deterministic tests. Substantive changes
  require tests; scaffold placeholders do not establish numerical correctness.
- Inspect existing interfaces before modifying them.
- README claims must match implementation.
- Require Python 3.12+, use type hints and clear financial docstrings, and use
  dataclasses where appropriate. Use pathlib for Python filesystem paths.
- Keep public APIs small and execution reproducible and offline.
- Use argparse for CLI work; do not use QuantLib or add unrelated tooling.

## Environment and Git rules

- The primary local environment is native Windows PowerShell.
- Agent shell commands must be PowerShell-compatible; do not assume Bash or WSL.
- Inspect Git state before starting work.
- Never rewrite published Git history or force push.
- Never use destructive Git commands merely to obtain a clean working tree.
- Commit and push only when the active task explicitly instructs them.
- Each phase must be one atomic commit.
- No commit may be created if required validation fails.
- No push may occur unless the required commit was created successfully.
- Preserve local commits and report authentication or push failures without
  destructive workarounds.
- Keep .venv and generated outputs out of Git.

## Current phase

Only the repository scaffold is implemented. Financial modules and their tests
remain placeholders. Do not begin financial implementation without a new task.
Validate editable installation, package import, pytest, and git diff --check
before committing this phase.
