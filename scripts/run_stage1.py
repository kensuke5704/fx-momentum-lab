from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fx_momentum.data import load_usd_prices, to_month_end
from fx_momentum.signals import composite_strength, next_month_currency_returns
from fx_momentum.portfolio import cross_sectional_weights, portfolio_returns
from fx_momentum.metrics import annualized_stats, monthly_rank_ic, ic_stats, rank_forward_returns


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/usd_prices.csv")
    parser.add_argument("--config", default="config/stage1.yaml")
    parser.add_argument("--out", default="results/stage1")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    prices = to_month_end(load_usd_prices(args.data))
    primary_start = pd.Timestamp(cfg["primary_start"])
    prices = prices.loc[prices.index >= primary_start]
    next_ret = next_month_currency_returns(prices)

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    rank_rows = []
    decade_rows = []

    for signal_cfg in cfg["signals"]:
        strength = composite_strength(
            prices,
            signal_cfg["lookbacks_months"],
            signal_cfg["weights"],
        )

        ic = monthly_rank_ic(strength, next_ret)
        ic.to_csv(outdir / f"ic_{signal_cfg['name']}.csv", header=True)
        ic_summary = ic_stats(ic)

        ranks = rank_forward_returns(strength, next_ret)
        for rank, value in ranks.items():
            rank_rows.append({"signal": signal_cfg["name"], "rank": rank, "avg_forward_return": value})

        for p_cfg in cfg["portfolios"]:
            weights = cross_sectional_weights(strength, p_cfg["top_n"])
            gross = portfolio_returns(weights, next_ret)
            gross.to_csv(outdir / f"returns_{signal_cfg['name']}_{p_cfg['name']}.csv", header=True)

            row = {
                "signal": signal_cfg["name"],
                "portfolio": p_cfg["name"],
                **annualized_stats(gross),
                **ic_summary,
            }
            summary_rows.append(row)

            for decade, chunk in gross.groupby((gross.index.year // 10) * 10):
                d = annualized_stats(chunk)
                decade_rows.append({
                    "signal": signal_cfg["name"],
                    "portfolio": p_cfg["name"],
                    "decade": int(decade),
                    **d,
                })

    pd.DataFrame(summary_rows).to_csv(outdir / "summary.csv", index=False)
    pd.DataFrame(rank_rows).to_csv(outdir / "rank_forward_returns.csv", index=False)
    pd.DataFrame(decade_rows).to_csv(outdir / "decade_summary.csv", index=False)

    print(pd.DataFrame(summary_rows).sort_values(["signal", "portfolio"]).to_string(index=False))


if __name__ == "__main__":
    main()
