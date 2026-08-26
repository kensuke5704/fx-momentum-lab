# Stage 1 Result — G8 Cross-Sectional Spot Momentum

Status: **FAIL**

Primary sample: 1999 onward, 331 monthly observations in the completed run.
Universe: USD, EUR, JPY, GBP, AUD, NZD, CAD, CHF.
Signals: 1M, 3M, 6M, 12M, 3M+6M, 1M+3M+6M.
Portfolios: Top1/Bottom1 and Top2/Bottom2.
Costs: 0, 2, 5, 10 bp round-trip sensitivity.

## Preregistered acceptance checks

1. Positive winner-loser spread: **FAIL overall**. Only 3M showed a positive Rank1-Rank8 spread; the other five signals did not.
2. Positive mean IC: **FAIL**. Mean Spearman IC was negative for all six signals.
3. Multi-lookback directional agreement: **FAIL**.
4. Top1/Top2 directional agreement: **FAIL**. The isolated positive 3M Top1 result did not survive Top2 diversification.
5. Decade robustness: **FAIL**. Results weakened materially after the 2000s and were generally negative in the 2010s/2020s.

## Key gross results (0 bp)

| Signal | Portfolio | CAGR | Sharpe | Mean IC |
|---|---|---:|---:|---:|
| 1M | Top1/Bottom1 | -0.80% | -0.125 | -0.0143 |
| 3M | Top1/Bottom1 | +0.81% | +0.117 | -0.0068 |
| 6M | Top1/Bottom1 | -0.06% | -0.010 | -0.0073 |
| 12M | Top1/Bottom1 | -0.32% | -0.048 | -0.0096 |
| 3M+6M | Top1/Bottom1 | -0.47% | -0.071 | -0.0105 |
| 1M+3M+6M | Top1/Bottom1 | -0.03% | -0.005 | -0.0147 |

Top2/Bottom2 was negative for 1M, 3M, 6M, 12M, and 1M+3M+6M; 3M+6M was effectively flat before costs and negative after costs.

## Interpretation

The preregistered hypothesis that relative spot momentum among only the eight major currencies provides a robust monthly cross-sectional forecasting signal is not supported by this sample.

No stop, volatility target, macro filter, carry filter, or parameter optimization should be added to rescue this specification. Doing so would convert a failed alpha test into post-hoc optimization.

The next research step, if FX momentum is pursued, should be a separately preregistered diagnostic specification that explains why this G8 spot-only setup differs from broader academic FX momentum evidence. Candidate structural differences include broader currency universes and excess-return/carry treatment rather than spot-only returns.
