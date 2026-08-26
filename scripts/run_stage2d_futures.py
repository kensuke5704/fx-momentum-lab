from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from fx_momentum.metrics import annualized_stats
from fx_momentum.portfolio import apply_round_trip_costs, portfolio_turnover
from run_stage2a import monthly_ic, ic_summary


def load_monthly(path: str | Path, start: str) -> pd.DataFrame:
    daily = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index().astype(float)
    daily = daily.loc[daily.index >= pd.Timestamp(start)]
    return daily.resample("ME").last()


def top_bottom_third_weights(signal: pd.DataFrame, forward: pd.DataFrame, min_contracts: int) -> pd.DataFrame:
    w = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for dt in signal.index.intersection(forward.index):
        valid = pd.concat([signal.loc[dt], forward.loc[dt]], axis=1).dropna()
        if len(valid) < min_contracts:
            continue
        valid.columns = ["signal", "forward"]
        ordered = valid.sort_values("signal").index.tolist()
        n = max(1, len(ordered) // 3)
        losers, winners = ordered[:n], ordered[-n:]
        w.loc[dt, winners] = 0.5 / len(winners)
        w.loc[dt, losers] = -0.5 / len(losers)
    return w


def portfolio_returns(weights: pd.DataFrame, forward: pd.DataFrame) -> pd.Series:
    w, r = weights.align(forward, join="inner", axis=0)
    w, r = w.align(r, join="inner", axis=1)
    active = w.abs().sum(axis=1) > 0
    return w.mul(r).sum(axis=1).where(active).rename("return")


def winner_loser_spread(signal: pd.DataFrame, forward: pd.DataFrame, min_contracts: int) -> float:
    vals = []
    for dt in signal.index.intersection(forward.index):
        valid = pd.concat([signal.loc[dt], forward.loc[dt]], axis=1).dropna()
        if len(valid) < min_contracts:
            continue
        valid.columns = ["signal", "forward"]
        ordered = valid.sort_values("signal")
        n = max(1, len(ordered) // 3)
        vals.append(float(ordered.iloc[-n:]["forward"].mean() - ordered.iloc[:n]["forward"].mean()))
    return float(np.mean(vals)) if vals else np.nan


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/stage2d_futures_daily.csv")
    p.add_argument("--config", default="config/stage2d_futures_free.yaml")
    p.add_argument("--out", default="results/stage2d_futures_free")
    args = p.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    prices = load_monthly(args.data, cfg["primary_start"])
    fwd = np.log(prices.shift(-1) / prices)
    min_contracts = int(cfg["portfolio"]["min_contracts_per_month"])
    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)

    rows, decade_rows = [], []
    prices.notna().sum(axis=1).rename("available_contracts").to_csv(outdir / "available_contracts.csv", header=True)

    for scfg in cfg["signals"]:
        name = scfg["name"]
        signal = np.log(prices / prices.shift(int(scfg["lookback_months"])))
        ic = monthly_ic(signal, fwd, min_contracts)
        ic.to_csv(outdir / f"ic_{name}.csv", header=True)
        ics = ic_summary(ic)
        spread = winner_loser_spread(signal, fwd, min_contracts)
        w = top_bottom_third_weights(signal, fwd, min_contracts)
        gross = portfolio_returns(w, fwd)
        turnover = portfolio_turnover(w)
        turnover.to_csv(outdir / f"turnover_{name}.csv", header=True)

        for bps in cfg["transaction_cost_bps_round_trip"]:
            net = apply_round_trip_costs(gross, w, float(bps))
            net.to_csv(outdir / f"returns_{name}_cost{bps}bp.csv", header=True)
            rows.append({
                "signal": name,
                "cost_bps": float(bps),
                "winner_loser_spread_monthly": spread,
                "avg_monthly_turnover": float(turnover.reindex(net.index).mean()),
                **annualized_stats(net),
                **ics,
            })
            x = net.dropna()
            for decade, chunk in x.groupby((x.index.year // 10) * 10):
                decade_rows.append({"signal": name, "cost_bps": float(bps), "decade": int(decade), **annualized_stats(chunk)})

    summary = pd.DataFrame(rows)
    decades = pd.DataFrame(decade_rows)
    summary.to_csv(outdir / "summary.csv", index=False)
    decades.to_csv(outdir / "decade_summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
