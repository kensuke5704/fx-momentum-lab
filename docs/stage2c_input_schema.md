# Stage 2C input schema

Expected file: `data/stage2c_true_forward.csv`

The file is intentionally not committed because licensed vendor data must not be redistributed.

## Required quotation convention

Both spot and one-month forward quotes must be **foreign-currency units per 1 USD** at the same month-end fixing.

Example columns:

```text
date,EUR_spot,EUR_fwd1m,JPY_spot,JPY_fwd1m,...
1999-01-29,0.91,0.909,115.20,114.95,...
```

Values shown above are illustrative only and must not be used as research data.

## Required fields

For every preregistered currency `<CCY>`:

- `<CCY>_spot`
- `<CCY>_fwd1m`

Missing observations are allowed and drive dynamic monthly availability. Missing currencies must not be synthesized or backfilled merely to satisfy the minimum cross-section.

## Return convention

For foreign-currency-units-per-USD quotes:

```text
rx[t -> t+1] = log(F_t) - log(S_{t+1})
```

where `F_t` is the 1M forward observed at month-end `t`, and `S_{t+1}` is the spot quote at the next month-end.

The signal at date `t` is formed only from realized excess returns ending no later than `t`. `run_stage2c.py` therefore shifts realized next-month returns by one month before computing trailing 1/3/6/9/12M sums.

## Vendor metadata to preserve outside the data file

Record alongside each export:

- vendor and product name,
- series identifiers / RICs / tickers,
- fixing source and fixing time,
- quotation convention,
- forward tenor definition,
- export timestamp,
- any vendor treatment of holidays / month-end dates.

The Stage 2C result is invalid if spot and forward are sourced from mismatched fixings without documented alignment.
