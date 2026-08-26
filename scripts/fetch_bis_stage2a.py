from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

BULK_URL = "https://data.bis.org/static/bulk/WS_XRU_csv_flat.zip"

SERIES = {
    "EUR": ("XM", "EUR"),
    "JPY": ("JP", "JPY"),
    "GBP": ("GB", "GBP"),
    "AUD": ("AU", "AUD"),
    "NZD": ("NZ", "NZD"),
    "CAD": ("CA", "CAD"),
    "CHF": ("CH", "CHF"),
    "NOK": ("NO", "NOK"),
    "SEK": ("SE", "SEK"),
    "DKK": ("DK", "DKK"),
    "CZK": ("CZ", "CZK"),
    "HUF": ("HU", "HUF"),
    "PLN": ("PL", "PLN"),
    "ISK": ("IS", "ISK"),
    "BRL": ("BR", "BRL"),
    "MXN": ("MX", "MXN"),
    "ZAR": ("ZA", "ZAR"),
    "KRW": ("KR", "KRW"),
    "SGD": ("SG", "SGD"),
    "THB": ("TH", "THB"),
    "IDR": ("ID", "IDR"),
    "INR": ("IN", "INR"),
    "ILS": ("IL", "ILS"),
    "MYR": ("MY", "MYR"),
    "PHP": ("PH", "PHP"),
}


def _code(value: object) -> str:
    text = str(value).strip()
    return text.split(":", 1)[0].strip() if ":" in text else text


def _norm_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_code(c).upper() for c in df.columns]
    return df


def _read_flat_csv(payload: bytes) -> pd.DataFrame:
    with ZipFile(BytesIO(payload)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError("BIS ZIP contains no CSV file")
        name = max(csv_names, key=lambda n: zf.getinfo(n).file_size)
        with zf.open(name) as fh:
            return _norm_columns(pd.read_csv(fh, low_memory=False))


def fetch(timeout: int = 120) -> pd.DataFrame:
    response = requests.get(BULK_URL, timeout=timeout)
    response.raise_for_status()
    raw = _read_flat_csv(response.content)

    required = {"FREQ", "REF_AREA", "CURRENCY", "COLLECTION", "TIME_PERIOD", "OBS_VALUE"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise RuntimeError(f"Unexpected BIS schema; missing {missing}")

    for col in ["FREQ", "REF_AREA", "CURRENCY", "COLLECTION"]:
        raw[col] = raw[col].map(_code)

    raw = raw[(raw["FREQ"] == "M") & (raw["COLLECTION"] == "E")].copy()
    raw["TIME_PERIOD"] = pd.to_datetime(raw["TIME_PERIOD"], errors="coerce")
    raw["OBS_VALUE"] = pd.to_numeric(raw["OBS_VALUE"], errors="coerce")

    pieces: list[pd.Series] = []
    missing_series: list[str] = []
    for currency, (area, bis_currency) in SERIES.items():
        sub = raw[(raw["REF_AREA"] == area) & (raw["CURRENCY"] == bis_currency)][["TIME_PERIOD", "OBS_VALUE"]].dropna()
        if sub.empty:
            missing_series.append(f"M.{area}.{bis_currency}.E")
            continue
        sub = sub.drop_duplicates("TIME_PERIOD", keep="last").set_index("TIME_PERIOD").sort_index()
        # BIS publishes local-currency units per USD; invert to USD per currency unit.
        pieces.append((1.0 / sub["OBS_VALUE"]).rename(currency))

    if missing_series:
        raise RuntimeError(f"Missing preregistered BIS series: {missing_series}")

    out = pd.concat(pieces, axis=1).sort_index()
    out.index.name = "date"
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/stage2a_usd_prices.csv")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    out = fetch(args.timeout)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path)
    coverage = pd.DataFrame({"start": out.apply(lambda s: s.first_valid_index()), "end": out.apply(lambda s: s.last_valid_index()), "months": out.notna().sum()})
    print(coverage.to_string())
    print(f"wrote {path}: {len(out)} rows x {out.shape[1]} currencies")


if __name__ == "__main__":
    main()
