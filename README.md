# fx-momentum-lab

Research repository for G8 cross-sectional FX momentum.

## Stage 1 objective

Test whether relative currency momentum predicts next-month relative FX returns before adding leverage, stop rules, volatility targeting, carry filters, or macro overlays.

### Universe

USD, EUR, JPY, GBP, AUD, NZD, CAD, CHF.

### Pre-registered models

Six signals x two portfolio constructions = 12 models:

- 1M
- 3M
- 6M
- 12M
- 3M+6M
- 1M+3M+6M

Portfolio variants:

- strongest 1 vs weakest 1
- strongest 2 vs weakest 2

### Primary sample

1999 onward for the complete G8 universe.

### Extended robustness sample

Pre-1999 can be analyzed separately as G7 without EUR. Synthetic EUR history is not part of the primary result.

### Stage 1 acceptance criteria

A Stage 1 result is considered structurally promising only if:

1. Winner-minus-loser spread is positive.
2. Mean rank IC is positive.
3. Multiple lookbacks point in the same direction.
4. Top1 and Top2 portfolio constructions agree directionally.
5. Results are not concentrated in a single decade or a few extreme episodes.
6. The signal remains economically meaningful after transaction-cost sensitivity tests.

The repository is intentionally designed to preserve pre-registration and research history so parameter changes are visible in Git history.
