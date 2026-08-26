import numpy as np
import pandas as pd

from fx_momentum.signals import currency_log_returns, next_month_currency_returns


def test_relative_strength_sums_to_zero_cross_sectionally():
    idx = pd.date_range("2020-01-31", periods=3, freq="ME")
    prices = pd.DataFrame(
        {
            "USD": [1.0, 1.0, 1.0],
            "EUR": [1.0, 1.1, 1.21],
            "JPY": [1.0, 0.9, 0.81],
        },
        index=idx,
    )
    s = currency_log_returns(prices, 1).dropna()
    assert np.allclose(s.sum(axis=1).values, 0.0)


def test_forward_returns_use_next_period():
    idx = pd.date_range("2020-01-31", periods=3, freq="ME")
    prices = pd.DataFrame(
        {
            "USD": [1.0, 1.0, 1.0],
            "EUR": [1.0, 1.1, 1.21],
            "JPY": [1.0, 1.0, 1.0],
        },
        index=idx,
    )
    fwd = next_month_currency_returns(prices)
    assert fwd.loc[idx[0], "EUR"] > 0
    assert np.isnan(fwd.loc[idx[-1], "EUR"])
