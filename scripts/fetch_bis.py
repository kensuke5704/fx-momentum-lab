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

DIMENSION_COLUMNS = ["FREQ", "REF_AREA", "CURRENCY", "COLLECTION"]


def _code(value: object) -> str:
    text = str(value).strip()
    return text.split(":", 1)[0].strip() if ":" in text else text


def _norm_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize BIS flat-CSV headers to their SDMX concept codes."""
    df = df.copy()
    normalized = []
    for col in df.columns:
        name = str(col).strip().upper()
        if ":" in name:
            name = name.split(":", 1)[0].strip()
        normalized.append(name)
    df.columns = normalized
    aliases = {
        "TIME": "TIME_PERIOD",
        "PERIOD": "TIME_PERIOD",
        "VALUE": "OBS_VALUE",
        "OBSERVATION_VALUE": "OBS_VALUE",
        "COLLECTION_INDICATOR": "COLLECTION",
    }
    df = df.rename(columns={k: v for k, v in aliases.items() if k in df.columns})
    for col in DIMENSION_COLUMNS:
        if col in df.columns:
            df[col] = df[col].map(_code)
    return df


def _read_flat_csv(payload: bytes) -> pd.DataFrame:
    with ZipFile(BytesIO(payload)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError("BIS ZIP contains no CSV file")
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

    raw = raw[(raw["FREQ"] == "M") & (raw["COLLECTION"] == "E")].copy()
    raw["TIME_PERIOD"] = pd.to_datetime(raw["TIME_PERIOD"], errors="coerce")
    raw["OBS_VALUE"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")

    pieces: list[pd.Series] = []
    for currency, (area, bis_currency) in SERIES.items():
        if currency == "USD":
            continue
        sub = raw[
            (raw["REF_AREA"] == area)
            & (raw["CURRENCY"] == bis_currency)
        ][["TIME_PERIOD", "OBS_VALUE"]].dropna()
        if sub.empty:
            available = raw.loc[raw["CURRENCY"] == bis_currency, "REF_AREA"].dropna().unique().tolist()[:20]
            raise RuntimeError(
                f"No BIS series found for M.{area}.{bis_currency}.E; "
                f"available REF_AREA for {bis_currency}: {available}"
            )
        sub = sub.drop_duplicates("TIME_PERIOD", keep="last").set_index("TIME_PERIOD").sort_index()
        s = (1.0 / sub["OBS_VALUE"]).rename(currency)
        pieces.append(s)

    out = pd.concat(pieces, axis=1).sort_index()
    out.insert(0, "USD", 1.0)
    out.index.name = "date"
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
