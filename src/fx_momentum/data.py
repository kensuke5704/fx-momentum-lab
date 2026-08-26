from __future__ import annotations

from pathlib import Path
import pandas as pd

REQUIRED = ["USD", "EUR", "JPY", "GBP", "AUD", "NZD", "CAD", "CHF"]


def load_usd_prices(path: str | Path) -> pd.DataFrame:
    """Load month-end USD price of one unit of each currency.

    CSV format: date,USD,EUR,JPY,GBP,AUD,NZD,CAD,CHF.
    Each value is USD per one unit of currency. USD must equal 1.0.
    """
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"missing currencies: {missing}")
    df = df[REQUIRED].astype(float)
    if not (df["USD"].dropna() == 1.0).all():
        raise ValueError("USD column must equal 1.0")
    if (df <= 0).any().any():
        raise ValueError("FX prices must be positive")
    return df


def to_month_end(df: pd.DataFrame) -> pd.DataFrame:
    """Take the last available observation in each calendar month."""
    return df.resample("ME").last().dropna(how="all")
