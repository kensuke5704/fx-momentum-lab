from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))

from fx_momentum.metrics import annualized_stats
from fx_momentum.portfolio import apply_round_trip_costs, portfolio_turnover
from run_stage2a import sixth_weights, portfolio_returns, monthly_ic, ic_summary, six_bucket_forward_returns


def _required_columns(currencies: list[str]) -> list[str]:
    cols = ['date']
    for ccy in currencies:
        cols.extend([f'{ccy}_spot', f'{ccy}_fwd1m'])
    return cols


def load_true_forward_data(path: str | Path, currencies: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(path, parse_dates=['date']).set_index('date').sort_index()
    required = set(_required_columns(currencies)) - {'date'}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f'missing Stage 2C columns: {missing}')
    spot = df[[f'{c}_spot' for c in currencies]].copy()
    fwd = df[[f'{c}_fwd1m' for c in currencies]].copy()
    spot.columns = currencies
    fwd.columns = currencies
    return spot.astype(float), fwd.astype(float)


def true_excess_returns_foreign_per_usd(spot: pd.DataFrame, fwd: pd.DataFrame) -> pd.DataFrame:
    """One-month long-foreign-currency log excess returns.

    Required quotation: foreign-currency units per USD for both spot and 1M forward.
    If s_t = log(FC/USD) and f_t = log(FC/USD 1M forward), the long-foreign
    excess return over t->t+1 is f_t - s_{t+1}.
    Positive values mean the foreign-currency long outperformed USD after carry.
    """
    if (spot <= 0).any().any() or (fwd <= 0).any().any():
        raise ValueError('spot and forward quotes must be strictly positive')
    spot, fwd = spot.align(fwd, join='inner', axis=0)
    spot, fwd = spot.align(fwd, join='inner', axis=1)
    return (np.log(fwd) - np.log(spot.shift(-1))).rename_axis(index='date')


def trailing_excess_signal(realized_next: pd.DataFrame, months: int) -> pd.DataFrame:
    # realized_next at t is earned from t to t+1. At signal date t only returns
    # ending at t are known, hence shift(1) before the trailing sum.
    return realized_next.shift(1).rolling(months, min_periods=months).sum()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--data', default='data/stage2c_true_forward.csv')
    p.add_argument('--config', default='config/stage2c.yaml')
    p.add_argument('--out', default='results/stage2c')
    args = p.parse_args()

    with open(args.config, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    currencies = cfg['currencies']
    spot, fwd = load_true_forward_data(args.data, currencies)
    start = pd.Timestamp(cfg['primary_start'])
    spot = spot.loc[spot.index >= start]
    fwd = fwd.loc[fwd.index >= start]
    next_ret = true_excess_returns_foreign_per_usd(spot, fwd)
    min_ccy = int(cfg['min_currencies_per_month'])

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    next_ret.notna().sum(axis=1).rename('available_currencies').to_csv(outdir / 'available_currencies.csv', header=True)

    rows: list[dict] = []
    bucket_rows: list[dict] = []
    decade_rows: list[dict] = []

    for scfg in cfg['signals']:
        name = scfg['name']
        signal = trailing_excess_signal(next_ret, int(scfg['lookback_months']))
        ic = monthly_ic(signal, next_ret, min_ccy)
        ic.to_csv(outdir / f'ic_{name}.csv', header=True)
        ics = ic_summary(ic)

        bucket = six_bucket_forward_returns(signal, next_ret, min_ccy)
        for b, value in bucket.items():
            bucket_rows.append({'signal': name, 'bucket': int(b), 'avg_forward_return': value})
        spread = float(bucket.loc[6] - bucket.loc[1])

        weights = sixth_weights(signal, next_ret, min_ccy)
        gross = portfolio_returns(weights, next_ret)
        turnover = portfolio_turnover(weights)
        turnover.to_csv(outdir / f'turnover_{name}.csv', header=True)

        for bps in cfg['transaction_cost_bps_round_trip']:
            net = apply_round_trip_costs(gross, weights, float(bps))
            net.to_csv(outdir / f'returns_{name}_cost{bps}bp.csv', header=True)
            rows.append({
                'signal': name,
                'cost_bps': float(bps),
                'winner_loser_spread_monthly': spread,
                'avg_monthly_turnover': float(turnover.reindex(net.index).mean()),
                **annualized_stats(net),
                **ics,
            })
            for decade, chunk in net.dropna().groupby((net.dropna().index.year // 10) * 10):
                decade_rows.append({'signal': name, 'cost_bps': float(bps), 'decade': int(decade), **annualized_stats(chunk)})

    pd.DataFrame(rows).to_csv(outdir / 'summary.csv', index=False)
    pd.DataFrame(bucket_rows).to_csv(outdir / 'six_bucket_forward_returns.csv', index=False)
    pd.DataFrame(decade_rows).to_csv(outdir / 'decade_summary.csv', index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == '__main__':
    main()
