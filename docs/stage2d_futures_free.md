# Stage 2D-FREE — CME FX futures momentum diagnostic

Status: **PREREGISTERED / DIAGNOSTIC ONLY**

## Why this stage exists

Stage 2C requires actual one-month OTC forward data across a broad currency cross-section. A free, authoritative historical dataset of that scope was not found. Rather than substitute a non-tradable approximation, Stage 2D tests momentum directly on exchange-traded CME FX futures.

Futures prices embed the market's interest-rate differential and are themselves tradable. Therefore this stage is economically closer to a tradable carry-inclusive FX strategy than the Stage 2B policy-rate proxy. However, it is **not** a replication of Menkhoff et al.'s one-month OTC forward excess-return methodology.

## Free data limitation

The free diagnostic uses Yahoo Finance continuous CME futures symbols. This introduces a material limitation: the continuous-contract roll methodology is vendor-controlled and not independently fixed by this repository. Roll discontinuities or back-adjustment choices can affect both signals and realized returns.

Accordingly:

- positive results cannot promote the strategy to production;
- negative results are informative but may partly reflect continuous-series construction;
- any promising result must later be repeated with official CME settlement data and an explicit roll rule.

## Preregistered universe

EUR, JPY, GBP, AUD, CAD, CHF, NZD, MXN, ZAR.

The common research start is 2004-01-02. USD is not ranked because each futures contract is already a USD-relative instrument.

## Signals and portfolio

Formation horizons: 1M / 3M / 6M / 9M / 12M.

At each month end, contracts are ranked by trailing log futures return. The top third is long and the bottom third is short, equal-weighted within each side. Gross exposure is 1.0 and net exposure is 0.0. Holding period is one month.

No stop, regime filter, volatility targeting, leverage optimization, or post-result universe pruning is allowed.

## Acceptance gate

A family-level diagnostic pass requires:

1. positive mean rank IC for a majority of the five horizons;
2. positive winner-minus-loser spread for a majority;
3. positive 5 bp net CAGR for at least three horizons;
4. same directional result across 3M/6M/9M/12M;
5. at least one horizon with positive 5 bp CAGR in the 2000s, 2010s, and 2020s.

Even if all conditions pass, classification remains **DIAGNOSTIC PASS**, not Production Candidate, until repeated on official settlement data with an explicit roll methodology.
