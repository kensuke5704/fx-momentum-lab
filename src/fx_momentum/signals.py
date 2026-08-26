from __future__ import annotations

import numpy as np
import pandas as pd


def currency_log_returns(usd_prices: pd.DataFrame, months: int) -> pd.DataFrame:
    """Currency returns versus the equal-weight basket of the other currencies.

    usd_prices must be USD per unit of currency. Pair log return i/j equals
    log(P_i/P_i[-L]) - log(P_j/P_j[-L]). Averaging over j != i is equivalent
    to the cross-sectional currency-strength definition used in Stage 1.
    """
    own = np.log(usd_prices / usd_prices.shift(months))
    n = own.shape[1]
    total = own.sum(axis=1)
    return (n * own.sub(total / n, axis=0)) / (n - 1)


def composite_strength(
    usd_prices: pd.DataFrame,
    lookbacks: list[int],
    weights: list[float],
) -> pd.DataFrame:
    if len(lookbacks) != len(weights):
        raise ValueError("lookbacks and weights must have equal length")
    if not np.isclose(sum(weights), 1.0):
        raise ValueError("weights must sum to 1")
    pieces = [currency_log_returns(usd_prices, lb) * w for lb, w in zip(lookbacks, weights)]
    out = pieces[0].copy()
    for part in pieces[1:]:
        out = out.add(part, fill_value=np.nan)
    return out


def next_month_currency_returns(usd_prices: pd.DataFrame) -> pd.DataFrame:
    """One-month-ahead currency return versus the cross-sectional basket."""
    one_month = np.log(usd_prices.shift(-1) / usd_prices)
    n = one_month.shape[1]
    total = one_month.sum(axis=1)
    return (n * one_month.sub(total / n, axis=0)) / (n - 1)
