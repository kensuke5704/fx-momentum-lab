# Stage 2C Data Gate — true 1M FX excess returns

Status: **BLOCKED ON DATA / METHOD FROZEN**

## Objective

Validate broad cross-sectional FX momentum using actual one-month forward-based excess returns, without changing the Stage 2A/2B research family after seeing results.

## Why Stage 2B-PROXY is insufficient

Stage 2B-PROXY used BIS central-bank policy-rate differentials as a carry approximation. That is useful diagnostically but is not the same object as a tradable one-month forward discount and cannot be promoted to production evidence.

## Required return definition

For a foreign currency quoted as foreign-currency units per USD, the one-month long-foreign-currency excess return must be constructed from spot and the one-month forward quote with a consistent quotation convention. The implementation must explicitly document and test the sign convention before any performance results are inspected.

Accepted input fields:

- `date` — month-end signal date
- `<CCY>_spot` — month-end spot quote
- `<CCY>_fwd1m` — one-month forward quote observed at the same month-end fixing

The exact excess-return formula is determined by the quotation convention declared in metadata and must pass synthetic sign tests.

## Frozen research family

- Base currency: USD, not ranked
- Foreign-currency universe: same 25-currency preregistered list as Stage 2A/2B when data are available
- Dynamic availability: allowed; no backfilling of unavailable currencies
- Formation horizons: 1 / 3 / 6 / 9 / 12 months
- Portfolio: top one-sixth long / bottom one-sixth short
- Rebalance: monthly
- Holding: one month
- Costs: 0 / 2 / 5 / 10 bp round-trip sensitivity
- Minimum currencies per month: unchanged from Stage 2A/2B
- No stop, volatility target, leverage optimization, macro filter, or parameter search

## Acceptance checks

Use the same family-level logic as Stage 2A/2B:

1. positive mean rank IC across the hypothesis family,
2. positive winner-minus-loser spread for a majority of lookbacks,
3. directional agreement across 3/6/9/12M,
4. positive 5 bp net return for at least three lookbacks,
5. decade robustness, with special attention to whether 6M/9M remain positive without selecting them ex post.

## Public-data audit

- BIS bilateral exchange rates provide long spot histories but not a 25-currency historical 1M forward cross-section.
- The published FX-momentum literature commonly uses WM/Reuters and Barclays forward data via Datastream/Refinitiv.
- Bank of England provides public forward series, but its accessible forward set is not a substitute for the required broad 25-currency USD cross-section.

Therefore no free public series has been accepted as a faithful replacement for the broad true-forward dataset. The research gate remains blocked rather than silently lowering the evidence standard.

## Valid data routes

Preferred, in order:

1. Refinitiv / Datastream historical spot + 1M forward series,
2. Bloomberg historical spot + 1M forward series,
3. another institutional vendor with documented month-end spot and 1M forward fixings and sufficient history.

A reduced-universe public-data experiment may be run only as a separately preregistered **DIAGNOSTIC** study; it must not be labeled Stage 2C validation of the 25-currency hypothesis.
