import numpy as np
import pandas as pd

from fx_momentum.portfolio import portfolio_turnover, apply_round_trip_costs


def test_initial_open_is_half_round_trip_and_full_replacement_is_one():
    idx = pd.to_datetime(["2024-01-31", "2024-02-29"])
    w = pd.DataFrame(
        [[0.5, -0.5, 0.0, 0.0], [0.0, 0.0, 0.5, -0.5]],
        index=idx,
        columns=["A", "B", "C", "D"],
    )
    t = portfolio_turnover(w)
    assert np.isclose(t.iloc[0], 0.5)
    assert np.isclose(t.iloc[1], 1.0)


def test_round_trip_cost_is_deducted_in_log_space():
    idx = pd.to_datetime(["2024-01-31"])
    w = pd.DataFrame([[0.5, -0.5]], index=idx, columns=["A", "B"])
    gross = pd.Series([0.0], index=idx)
    net = apply_round_trip_costs(gross, w, 10.0)
    expected = np.log1p(-0.5 * 10.0 / 10_000.0)
    assert np.isclose(net.iloc[0], expected)
