from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
import yaml

# Stage 2D uses free vendor continuous futures strictly as a diagnostic source.


def fetch_symbol(symbol: str, start: str) -> pd.Series:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='')}"
    params = {
        "period1": int(pd.Timestamp(start, tz="UTC").timestamp()),
        "period2": int((pd.Timestamp.utcnow() + pd.Timedelta(days=2)).timestamp()),
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    }
    r = requests.get(url, params=params, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    payload = r.json()
    err = payload.get("chart", {}).get("error")
    if err:
        raise RuntimeError(f"Yahoo error for {symbol}: {err}")
    result = payload["chart"]["result"][0]
    ts = result.get("timestamp", [])
    quote_data = result.get("indicators", {}).get("quote", [{}])[0]
    close = quote_data.get("close", [])
    if not ts or not close:
        raise RuntimeError(f"No Yahoo history for {symbol}")
    idx = pd.to_datetime(ts, unit="s", utc=True).tz_convert(None)
    s = pd.Series(close, index=idx, name=symbol, dtype=float).dropna()
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="config/stage2d_futures_free.yaml")
    p.add_argument("--out", default="data/stage2d_futures_daily.csv")
    args = p.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    pieces = []
    coverage = []
    for currency, symbol in cfg["contracts"].items():
        s = fetch_symbol(symbol, cfg["primary_start"]).rename(currency)
        pieces.append(s)
        coverage.append({"currency": currency, "symbol": symbol, "start": s.index.min(), "end": s.index.max(), "rows": len(s)})

    df = pd.concat(pieces, axis=1).sort_index()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index_label="date")
    print(pd.DataFrame(coverage).to_string(index=False))
    print(f"wrote {path}: {df.shape[0]} daily rows x {df.shape[1]} contracts")


if __name__ == "__main__":
    main()
