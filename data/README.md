# Data

Stage 1 expects `data/usd_prices.csv` with columns:

```text
date,USD,EUR,JPY,GBP,AUD,NZD,CAD,CHF
```

Each currency column must be expressed as **USD per one unit of currency**. `USD` must be exactly `1.0`.

The primary research sample begins in 1999 for the complete G8 universe. Pre-1999 robustness is kept separate and must not silently backfill EUR with synthetic history.

Raw source data should not be manually edited. Any transformation from vendor/BIS conventions into USD-per-currency form should be scripted and documented.
