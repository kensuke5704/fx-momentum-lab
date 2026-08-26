from __future__ import annotations

import numpy as np
import pandas as pd


def cross_sectional_weights(strength: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Build gross-1, net-0 long/short weights from currency strength ranks."""
    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    if 2 * top_n > strength.shape[1]:
        raise ValueError("top_n is too large for universe")

    weights = pd.DataFrame(0.0, index=strength.index, columns=strength.columns)
    for dt, row in strength.iterrows():
        valid = row.dropna()
        if len(valid) < 2 * top_n:
            continue
        longs = valid.nlargest(top_n).index
        shorts = valid.nsmallest(top_n).index
        weights.loc[dt, longs] = 0.5 / top_n
        weights.loc[dt, shorts] = -0.5 / top_n
    return weights


def portfolio_returns(weights: pd.DataFrame, next_returns: pd.DataFrame) -> pd.Series:
    """Apply signal-date weights to next-month currency log returns."""
    aligned_w, aligned_r = weights.align(next_returns, join="inner", axis=0)
    aligned_w, aligned_r = aligned_w.align(aligned_r, join="inner", axis=1)
    return (aligned_w * aligned_r).sum(axis=1).rename("return")


def portfolio_turnover(weights: pd.DataFrame) -> pd.Series:
    """One-way portfolio turnover, with the first portfolio opened from cash.

    0.5 * sum(abs(delta weights)) gives turnover of 1.0 for a complete
    replacement of a gross-1 portfolio. The initial gross-1 opening therefore
    has turnover 0.5, corresponding to half of a quoted round trip.
    """
    prev = weights.shift(1).fillna(0.0)
    return (0.5 * (weights - prev).abs().sum(axis=1)).rename("turnover")


def apply_round_trip_costs(
    gross_log_returns: pd.Series,
    weights: pd.DataFrame,
    round_trip_bps: float,
) -> pd.Series:
    """Deduct proportional transaction costs from monthly log returns."""
    if round_trip_bps < 0:
        raise ValueError("round_trip_bps must be non-negative")
    turnover = portfolio_turnover(weights).reindex(gross_log_returns.index).fillna(0.0)
    cost_fraction = turnover * (round_trip_bps / 10_000.0)
    if (cost_fraction >= 1).any():
        raise ValueError("transaction cost fraction must be below 100%")
    net = gross_log_returns + np.log1p(-cost_fraction)
    return net.rename("return")
