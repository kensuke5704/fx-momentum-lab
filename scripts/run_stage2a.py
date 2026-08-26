from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fx_momentum.metrics import annualized_stats
from fx_momentum.portfolio import apply_transaction_costs, portfolio_turnover


def load_prices(path: str | Path, currencies: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    missing = [c for c in currencies if c not in df.columns]
    if missing:
        raise ValueError(f"missing preregistered currencies: {missing}")
    return df[currencies].astype(float)


def spot_signal(prices: pd.DataFrame, lookback: int) -> pd.DataFrame:
    return np.log(prices / prices.shift(lookback))


def next_spot_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return np.log(prices.shift(-1) / prices)


def sixth_weights(signal: pd.DataFrame, next_ret: pd.DataFrame, min_currencies: int) -> pd.DataFrame:
    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for dt in signal.index.intersection(next_ret.index):
        valid = pd.concat([signal.loc[dt], next_ret.loc[dt]], axis=1).dropna()
        if len(valid) < min_currencies:
            continue
        valid.columns = ["signal", "forward"]
        ordered = valid.sort_values("signal", ascending=True).index.to_numpy()
        groups = np.array_split(ordered, 6)
        losers = list(groups[0])
        winners = list(groups[-1])
        if not losers or not winners:
            continue
        weights.loc[dt, winners] = 0.5 / len(winners)
        weights.loc[dt, losers] = -0.5 / len(losers)
    return weights


def portfolio_returns(weights: pd.DataFrame, next_ret: pd.DataFrame) -> pd.Series:
    w, r = weights.align(next_ret, join="inner", axis=0)
    w, r = w.align(r, join="inner", axis=1)
    active = w.abs().sum(axis=1) > 0
    return (w.mul(r).sum(axis=1).where(active)).rename("return")


def monthly_ic(signal: pd.DataFrame, next_ret: pd.DataFrame, min_currencies: int) -> pd.Series:
    vals: dict[pd.Timestamp, float] = {}
    for dt in signal.index.intersection(next_ret.index):
        valid = pd.concat([signal.loc[dt], next_ret.loc[dt]], axis=1).dropna()
        if len(valid) >= min_currencies:
            vals[dt] = valid.iloc[:, 0].corr(valid.iloc[:, 1], method="spearman")
    return pd.Series(vals, name="ic").sort_index()


def ic_summary(ic: pd.Series) -> dict[str, float]:
    x = ic.dropna()
    if x.empty:
        return {"mean_ic": np.nan, "median_ic": np.nan, "ic_positive_share": np.nan, "ic_tstat": np.nan}
    se = x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan
    return {
        "mean_ic": float(x.mean()),
        "median_ic": float(x.median()),
        "ic_positive_share": float((x > 0).mean()),
        "ic_tstat": float(x.mean() / se) if np.isfinite(se) and se > 0 else np.nan,
    }


def six_bucket_forward_returns(signal: pd.DataFrame, next_ret: pd.DataFrame, min_currencies: int) -> pd.Series:
    buckets: dict[int, list[float]] = {i: [] for i in range(1, 7)}
    for dt in signal.index.intersection(next_ret.index):
        valid = pd.concat([signal.loc[dt], next_ret.loc[dt]], axis=1).dropna()
        if len(valid) < min_currencies:
            continue
        valid.columns = ["signal", "forward"]
        ordered = valid.sort_values("signal", ascending=True)
        groups = np.array_split(np.arange(len(ordered)), 6)
        for bucket, positions in enumerate(groups, start=1):
            if len(positions):
                buckets[bucket].append(float(ordered.iloc[positions]["forward"].mean()))
    return pd.Series({k: np.mean(v) if v else np.nan for k, v in buckets.items()}, name="avg_forward_return")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/stage2a_usd_prices.csv")
    parser.add_argument("--config", default="config/stage2a.yaml")
    parser.add_argument("--out", default="results/stage2a")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    prices = load_prices(args.data, cfg["currencies"])
    prices = prices.loc[prices.index >= pd.Timestamp(cfg["primary_start"])]
    next_ret = next_spot_returns(prices)
    min_currencies = int(cfg["min_currencies_per_month"])

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict] = []
    bucket_rows: list[dict] = []
    decade_rows: list[dict] = []

    available = prices.notna().sum(axis=1).rename("available_currencies")
    available.to_csv(outdir / "available_currencies.csv", header=True)

    for scfg in cfg["signals"]:
        name = scfg["name"]
        signal = spot_signal(prices, int(scfg["lookback_months"]))
        ic = monthly_ic(signal, next_ret, min_currencies)
        ic.to_csv(outdir / f"ic_{name}.csv", header=True)
        ic_s = ic_summary(ic)

        bucket = six_bucket_forward_returns(signal, next_ret, min_currencies)
        for b, value in bucket.items():
            bucket_rows.append({"signal": name, "bucket": int(b), "avg_forward_return": value})
        winner_loser = float(bucket.loc[6] - bucket.loc[1])

        weights = sixth_weights(signal, next_ret, min_currencies)
        gross = portfolio_returns(weights, next_ret)
        turnover = portfolio_turnover(weights)
        turnover.to_csv(outdir / f"turnover_{name}.csv", header=True)

        for bps in cfg["transaction_cost_bps_round_trip"]:
            net = apply_transaction_costs(gross, turnover, float(bps))
            net.to_csv(outdir / f"returns_{name}_cost{bps}bp.csv", header=True)
            row = {
                "signal": name,
                "cost_bps": float(bps),
                "winner_loser_spread_monthly": winner_loser,
                "avg_monthly_turnover": float(turnover.reindex(net.index).mean()),
                **annualized_stats(net),
                **ic_s,
            }
            summary_rows.append(row)

            for decade, chunk in net.dropna().groupby((net.dropna().index.year // 10) * 10):
                decade_rows.append({"signal": name, "cost_bps": float(bps), "decade": int(decade), **annualized_stats(chunk)})

    summary = pd.DataFrame(summary_rows)
    buckets = pd.DataFrame(bucket_rows)
    decades = pd.DataFrame(decade_rows)
    summary.to_csv(outdir / "summary.csv", index=False)
    buckets.to_csv(outdir / "six_bucket_forward_returns.csv", index=False)
    decades.to_csv(outdir / "decade_summary.csv", index=False)

    print("Stage 2A summary")
    print(summary.to_string(index=False))
    print("\nSix-bucket average next-month spot returns (1=loser, 6=winner)")
    print(buckets.pivot(index="signal", columns="bucket", values="avg_forward_return").to_string())


if __name__ == "__main__":
    main()
