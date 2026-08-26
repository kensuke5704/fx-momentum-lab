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


def load(path: str, columns: list[str]) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=['date']).set_index('date').sort_index()
    return df.reindex(columns=columns).astype(float)


def monthly_proxy_excess(prices: pd.DataFrame, rates: pd.DataFrame) -> pd.DataFrame:
    # Holding from t to t+1: spot appreciation plus start-of-period policy-rate differential.
    spot = np.log(prices.shift(-1) / prices)
    usd = rates['USD']
    carry = rates.drop(columns=['USD']).sub(usd, axis=0) / 1200.0
    spot, carry = spot.align(carry, join='inner', axis=0)
    spot, carry = spot.align(carry, join='inner', axis=1)
    return spot + carry


def trailing_sum(realized_next: pd.DataFrame, months: int) -> pd.DataFrame:
    # realized_next at t is return earned from t to t+1. At signal date t,
    # only returns ending at t are known: realized_next.shift(1).
    return realized_next.shift(1).rolling(months, min_periods=months).sum()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--prices', default='data/stage2a_usd_prices.csv')
    p.add_argument('--rates', default='data/stage2b_policy_rates.csv')
    p.add_argument('--config', default='config/stage2b_proxy.yaml')
    p.add_argument('--out', default='results/stage2b_proxy')
    args = p.parse_args()

    with open(args.config, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    currencies = cfg['currencies']
    prices = load(args.prices, currencies)
    rates = load(args.rates, ['USD'] + currencies)
    start = pd.Timestamp(cfg['primary_start'])
    prices = prices.loc[prices.index >= start]
    rates = rates.loc[rates.index >= start]
    next_ret = monthly_proxy_excess(prices, rates)
    min_ccy = int(cfg['min_currencies_per_month'])
    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)

    rows=[]; bucket_rows=[]; decade_rows=[]
    next_ret.notna().sum(axis=1).rename('available_currencies').to_csv(outdir/'available_currencies.csv', header=True)
    for scfg in cfg['signals']:
        name=scfg['name']; signal=trailing_sum(next_ret, int(scfg['lookback_months']))
        ic=monthly_ic(signal,next_ret,min_ccy); ic.to_csv(outdir/f'ic_{name}.csv',header=True); ics=ic_summary(ic)
        bucket=six_bucket_forward_returns(signal,next_ret,min_ccy)
        for b,v in bucket.items(): bucket_rows.append({'signal':name,'bucket':int(b),'avg_forward_return':v})
        spread=float(bucket.loc[6]-bucket.loc[1])
        w=sixth_weights(signal,next_ret,min_ccy); gross=portfolio_returns(w,next_ret); turnover=portfolio_turnover(w)
        turnover.to_csv(outdir/f'turnover_{name}.csv',header=True)
        for bps in cfg['transaction_cost_bps_round_trip']:
            net=apply_round_trip_costs(gross,w,float(bps)); net.to_csv(outdir/f'returns_{name}_cost{bps}bp.csv',header=True)
            rows.append({'signal':name,'cost_bps':float(bps),'winner_loser_spread_monthly':spread,'avg_monthly_turnover':float(turnover.reindex(net.index).mean()),**annualized_stats(net),**ics})
            for decade,chunk in net.dropna().groupby((net.dropna().index.year//10)*10):
                decade_rows.append({'signal':name,'cost_bps':float(bps),'decade':int(decade),**annualized_stats(chunk)})
    pd.DataFrame(rows).to_csv(outdir/'summary.csv',index=False)
    pd.DataFrame(bucket_rows).to_csv(outdir/'six_bucket_forward_returns.csv',index=False)
    pd.DataFrame(decade_rows).to_csv(outdir/'decade_summary.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))

if __name__ == '__main__':
    main()
