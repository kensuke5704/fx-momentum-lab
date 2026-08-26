from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def annualized_stats(monthly_log_returns: pd.Series) -> dict[str, float]:
    r = monthly_log_returns.dropna()
    if r.empty:
        return {"cagr": np.nan, "vol": np.nan, "sharpe": np.nan, "max_dd": np.nan, "calmar": np.nan}
    equity = np.exp(r.cumsum())
    years = len(r) / 12.0
    cagr = equity.iloc[-1] ** (1 / years) - 1 if years > 0 else np.nan
    vol = r.std(ddof=1) * np.sqrt(12)
    sharpe = (r.mean() * 12) / vol if vol > 0 else np.nan
    peak = equity.cummax()
    dd = equity / peak - 1
    max_dd = dd.min()
    calmar = cagr / abs(max_dd) if max_dd < 0 else np.nan
    return {
        "cagr": cagr,
        "vol": vol,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "calmar": calmar,
        "win_rate": float((r > 0).mean()),
        "avg_monthly": float(r.mean()),
        "skew": float(stats.skew(r, bias=False)) if len(r) > 2 else np.nan,
        "months": int(len(r)),
    }


def monthly_rank_ic(strength: pd.DataFrame, next_returns: pd.DataFrame) -> pd.Series:
    vals: dict[pd.Timestamp, float] = {}
    for dt in strength.index.intersection(next_returns.index):
        x = strength.loc[dt]
        y = next_returns.loc[dt]
        valid = pd.concat([x, y], axis=1).dropna()
        if len(valid) >= 3:
            vals[dt] = valid.iloc[:, 0].corr(valid.iloc[:, 1], method="spearman")
    return pd.Series(vals, name="ic").sort_index()


def ic_stats(ic: pd.Series) -> dict[str, float]:
    x = ic.dropna()
    if x.empty:
        return {"mean_ic": np.nan, "median_ic": np.nan, "ic_positive_share": np.nan, "ic_tstat": np.nan}
    se = x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan
    return {
        "mean_ic": float(x.mean()),
        "median_ic": float(x.median()),
        "ic_positive_share": float((x > 0).mean()),
        "ic_tstat": float(x.mean() / se) if se and se > 0 else np.nan,
    }


def rank_forward_returns(strength: pd.DataFrame, next_returns: pd.DataFrame) -> pd.Series:
    buckets: dict[int, list[float]] = {}
    for dt in strength.index.intersection(next_returns.index):
        valid = pd.concat([strength.loc[dt], next_returns.loc[dt]], axis=1).dropna()
        if valid.empty:
            continue
        valid.columns = ["strength", "forward_return"]
        valid = valid.sort_values("strength", ascending=False)
        for rank, value in enumerate(valid["forward_return"], start=1):
            buckets.setdefault(rank, []).append(float(value))
    return pd.Series({rank: np.mean(v) for rank, v in buckets.items()}, name="avg_forward_return")
