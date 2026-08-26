from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

BULK_URL = "https://data.bis.org/static/bulk/WS_XRU_csv_flat.zip"

SERIES = {
    "USD": ("US", "USD"),
    "EUR": ("XM", "EUR"),
    "JPY": ("JP", "JPY"),
    "GBP": ("GB", "GBP"),
    "AUD": ("AU", "AUD"),
    "NZD": ("NZ", "NZD"),
    "CAD": ("CA", "CAD"),
    "CHF": ("CH", "CHF"),
}


def _norm_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    aliases = {
        "TIME": "TIME_PERIOD",
        "PERIOD": "TIME_PERIOD",
        "VALUE": "OBS_VALUE",
        "OBSERVATION_VALUE": "OBS_VALUE",
        "COLLECTION_INDICATOR": "COLLECTION",
    }
    return df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})


def _read_flat_csv(payload: bytes) -> pd.DataFrame:
    with ZipFile(BytesIO(payload)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError("BIS ZIP contains no CSV file")
        # Flat bulk archives normally contain one data CSV. If metadata CSVs are
        # ever added, prefer the largest CSV because it is the observation table.
        name = max(csv_names, key=lambda n: zf.getinfo(n).file_size)
        with zf.open(name) as fh:
            return _norm_columns(pd.read_csv(fh, low_memory=False))


def fetch_bis_monthly_end(timeout: int = 120) -> pd.DataFrame:
    response = requests.get(BULK_URL, timeout=timeout)
    response.raise_for_status()
    raw = _read_flat_csv(response.content)

    required = {"FREQ", "REF_AREA", "CURRENCY", "COLLECTION", "TIME_PERIOD", "OBS_VALUE"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise RuntimeError(
            f"Unexpected BIS flat CSV schema; missing {missing}. "
            f"Available columns: {sorted(raw.columns)}"
        )

    raw = raw[
        (raw["FREQ"].astype(str) == "M")
        & (raw["COLLECTION"].astype(str) == "E")
    ].copy()

    raw["TIME_PERIOD"] = pd.to_datetime(raw["TIME_PERIOD"], errors="coerce")
    raw["OBS_VALUE"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")

    pieces: list[pd.Series] = []
    for currency, (area, bis_currency) in SERIES.items():
        if currency == "USD":
            continue
        sub = raw[
            (raw["REF_AREA"].astype(str) == area)
            & (raw["CURRENCY"].astype(str) == bis_currency)
        ][["TIME_PERIOD", "OBS_VALUE"]].dropna()
        if sub.empty:
            raise RuntimeError(f"No BIS series found for M.{area}.{bis_currency}.E")
        sub = sub.drop_duplicates("TIME_PERIOD", keep="last").set_index("TIME_PERIOD").sort_index()

        # BIS XRU is units of local currency per 1 USD. The research pipeline
        # requires USD per 1 unit of currency, so invert the quotation.
        s = (1.0 / sub["OBS_VALUE"]).rename(currency)
        pieces.append(s)

    out = pd.concat(pieces, axis=1).sort_index()
    out.insert(0, "USD", 1.0)
    out.index.name = "date"

    # The primary G8 sample starts in 1999. Keep earlier observations in the
    # file for diagnostics, but rows are allowed to contain missing EUR before
    # its reliable G8 history begins.
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/usd_prices.csv")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    out = fetch_bis_monthly_end(timeout=args.timeout)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path)

    complete = out.dropna()
    print(f"wrote {path}: {len(out)} monthly rows")
    if not complete.empty:
        print(f"complete G8 coverage: {complete.index.min().date()} to {complete.index.max().date()} ({len(complete)} rows)")
    print(out.tail().to_string())


if __name__ == "__main__":
    main()
