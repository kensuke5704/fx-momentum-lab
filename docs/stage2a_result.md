# Stage 2A Result — broad USD spot momentum

Status: **FAIL (DIAGNOSTIC SIGNAL AT 9M/12M)**

Workflow: `stage2a-research`, successful run `32983600788`.
Primary sample: 1999-01 onward, dynamic availability from a preregistered list of 25 foreign currencies; USD is base currency and is not ranked.
Portfolio: monthly rebalance, top sixth long / bottom sixth short, gross exposure 1.0, one-month holding period.
Signals: 1M / 3M / 6M / 9M / 12M lagged USD spot return.

## Gross results (0 bp)

| Signal | Winner-Loser avg monthly spread | CAGR | Sharpe | MaxDD | Mean IC | IC t-stat |
|---|---:|---:|---:|---:|---:|---:|
| 1M | -0.0650% | -0.389% | -0.093 | -32.44% | -0.0102 | -0.592 |
| 3M | -0.0474% | -0.284% | -0.070 | -25.09% | -0.0023 | -0.128 |
| 6M | -0.0006% | -0.004% | -0.001 | -11.95% | +0.0114 | +0.621 |
| 9M | +0.2229% | +1.346% | +0.330 | -12.31% | +0.0319 | +1.678 |
| 12M | +0.1230% | +0.741% | +0.174 | -19.93% | +0.0174 | +0.907 |

## 5 bp round-trip cost sensitivity

| Signal | CAGR | Sharpe |
|---|---:|---:|
| 1M | -0.861% | -0.207 |
| 3M | -0.577% | -0.142 |
| 6M | -0.217% | -0.055 |
| 9M | +1.171% | +0.287 |
| 12M | +0.582% | +0.137 |

Only two of five lookbacks remain positive at 5 bp, below the preregistered requirement of at least three.

## Decade diagnostics (gross)

9M CAGR:
- 2000s: +2.35%
- 2010s: +0.18%
- 2020s: +1.26%

12M CAGR:
- 2000s: +1.90%
- 2010s: -0.37%
- 2020s: +0.69%

The 9M signal is the most internally consistent diagnostic result, but it was not selected ex ante as a standalone strategy and therefore must not be promoted to production based on this run.

## Preregistered acceptance checks

- Positive mean IC across the hypothesis family: **FAIL** (1M and 3M negative; 6M/9M/12M positive)
- Positive winner-loser spread for majority of lookbacks: **FAIL** (2/5 positive; 6M approximately zero but negative)
- Directional agreement across 3M/6M/9M/12M: **FAIL**
- Positive net return at 5 bp for at least three lookbacks: **FAIL** (2/5)
- Decade robustness: **PARTIAL** (9M passes directionally across 2000s/2010s/2020s; family does not)

Overall classification: **FAIL / DIAGNOSTIC ONLY**.

## Interpretation

Broadening the cross-section and treating USD as the base currency materially changes the result relative to Stage 1. Medium/long formation horizons, especially 9M, show a positive signal, but the effect is not broad enough across preregistered horizons to establish a robust spot-only momentum alpha.

Do not optimize around 9M. The next research step should address the main remaining methodological gap versus the published FX momentum literature: momentum is conventionally formed and evaluated on currency excess returns using one-month forwards (or a defensible equivalent carry measure), not spot returns alone.
