# Stage 2B-PROXY Result — broad FX momentum with policy-rate carry proxy

Status: **DIAGNOSTIC PASS / NOT VALID FOR PRODUCTION**

Workflow: `stage2b-proxy-research`, successful run `32984026199`.
Primary sample: 1999-01 onward.
Universe: same preregistered 25 foreign currencies as Stage 2A; USD is base currency and is not ranked.
Return proxy: USD spot appreciation + (foreign BIS policy rate - US BIS policy rate) / 1200 per month.
Portfolio: top sixth long / bottom sixth short, monthly rebalance, one-month holding period.
Signals: trailing 1M / 3M / 6M / 9M / 12M proxy excess returns.

> Important: BIS central bank policy rates are not one-month tradable deposit rates or FX forward discounts. This experiment is diagnostic only and cannot validate true FX excess-return momentum.

## Gross results (0 bp)

| Signal | Winner-Loser monthly spread | CAGR | Sharpe | MaxDD | Mean IC | IC t-stat |
|---|---:|---:|---:|---:|---:|---:|
| 1M | +0.1028% | +0.619% | 0.138 | -24.44% | +0.0167 | 0.945 |
| 3M | +0.2700% | +1.633% | 0.382 | -17.65% | +0.0318 | 1.703 |
| 6M | +0.3140% | +1.902% | 0.430 | -11.75% | +0.0426 | 2.231 |
| 9M | +0.2934% | +1.776% | 0.389 | -17.59% | +0.0584 | 2.905 |
| 12M | +0.1880% | +1.134% | 0.256 | -22.60% | +0.0395 | 1.976 |

## 5 bp round-trip cost sensitivity

| Signal | CAGR | Sharpe |
|---|---:|---:|
| 1M | +0.141% | 0.032 |
| 3M | +1.335% | 0.313 |
| 6M | +1.693% | 0.383 |
| 9M | +1.602% | 0.351 |
| 12M | +0.972% | 0.219 |

All five preregistered lookbacks remain positive at 5 bp.

## Decade diagnostics at 5 bp

6M CAGR:
- 2000s: +2.89%
- 2010s: +0.61%
- 2020s: +1.54%

9M CAGR:
- 2000s: +2.34%
- 2010s: +0.12%
- 2020s: +1.95%

3M and 12M are negative in the 2010s, so decade robustness is strongest for 6M and 9M rather than the entire signal family.

## Preregistered acceptance checks

- Positive mean IC: **PASS** (5/5 lookbacks)
- Positive winner-loser spread for majority of lookbacks: **PASS** (5/5)
- Directional agreement across 3M/6M/9M/12M: **PASS**
- Positive net return at 5 bp for at least three lookbacks: **PASS** (5/5)
- Decade robustness: **PARTIAL/PASS AT 6M AND 9M; not universal across all lookbacks**

Overall classification remains **DIAGNOSTIC ONLY** because the carry component is a policy-rate proxy rather than a tradable forward return.

## Interpretation versus Stage 2A

Stage 2A spot-only momentum failed the preregistered family-level tests and showed positive results mainly at 9M/12M. Adding the policy-rate carry proxy changes the structure materially: all five horizons produce positive winner-loser spreads and positive mean IC, with strongest evidence around 6M-9M.

This supports the hypothesis that the return definition (spot vs excess-return-like) is central to reproducing FX momentum evidence. It does not establish a tradable strategy until the same test is repeated with actual one-month forward discounts or an economically equivalent tradable carry series.

## Next research gate

Do not optimize 6M or 9M yet. Before portfolio/risk-rule optimization, obtain or construct a defensible tradable one-month excess-return series and rerun the same preregistered 1/3/6/9/12M family. Only if that true-excess-return test passes should Stage 3 portfolio construction begin.
