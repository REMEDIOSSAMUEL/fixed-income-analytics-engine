"""Placeholder for interest-rate and curve-risk analytics.

Planned zero-rate valuation uses DF(t) = exp(-r(t) * t), with years and decimal
continuously compounded annual zero rates, distinct from YTM pricing.
Planned scope: parallel/piecewise-linear shocks, steepeners, flatteners,
and key-rate DV01 with default keys 2Y, 5Y, 10Y, 30Y.
Key bases will interpolate linearly, equal one at their own key and zero at
other keys, extend the first/last basis flat into the tails, and sum to one.
No financial calculations exist yet.
"""
