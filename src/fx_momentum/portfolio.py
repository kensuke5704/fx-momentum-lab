from __future__ import annotations

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
    """Apply signal-date weights to next-month currency returns."""
    aligned_w, aligned_r = weights.align(next_returns, join="inner", axis=0)
    aligned_w, aligned_r = aligned_w.align(aligned_r, join="inner", axis=1)
    return (aligned_w * aligned_r).sum(axis=1).rename("return")
