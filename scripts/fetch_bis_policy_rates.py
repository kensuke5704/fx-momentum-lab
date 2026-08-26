from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

BULK_URL = "https://data.bis.org/static/bulk/WS_CBPOL_csv_flat.zip"
AREAS = {
    "USD":"US","EUR":"XM","JPY":"JP","GBP":"GB","AUD":"AU","NZD":"NZ","CAD":"CA","CHF":"CH",
    "NOK":"NO","SEK":"SE","DKK":"DK","CZK":"CZ","HUF":"HU","PLN":"PL","ISK":"IS","BRL":"BR",
    "MXN":"MX","ZAR":"ZA","KRW":"KR","SGD":"SG","THB":"TH","IDR":"ID","INR":"IN","ILS":"IL",
    "MYR":"MY","PHP":"PH"
}


def _code(value: object) -> str:
    text = str(value).strip()
    return text.split(":", 1)[0].strip() if ":" in text else text


def fetch(timeout: int = 120) -> pd.DataFrame:
    r = requests.get(BULK_URL, timeout=timeout)
    r.raise_for_status()
    with ZipFile(BytesIO(r.content)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith('.csv')]
        if not names:
            raise RuntimeError('No CSV in BIS policy-rate archive')
        name = max(names, key=lambda n: zf.getinfo(n).file_size)
        with zf.open(name) as fh:
            raw = pd.read_csv(fh, low_memory=False)
    raw.columns = [_code(c).upper() for c in raw.columns]
    required = {'FREQ','REF_AREA','TIME_PERIOD','OBS_VALUE'}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise RuntimeError(f'Unexpected CBPOL schema, missing {missing}; columns={sorted(raw.columns)}')
    raw['FREQ'] = raw['FREQ'].map(_code)
    raw['REF_AREA'] = raw['REF_AREA'].map(_code)
    raw = raw[raw['FREQ'] == 'M'].copy()
    raw['TIME_PERIOD'] = pd.to_datetime(raw['TIME_PERIOD'], errors='coerce')
    raw['OBS_VALUE'] = pd.to_numeric(raw['OBS_VALUE'], errors='coerce')

    pieces = []
    for ccy, area in AREAS.items():
        sub = raw[raw['REF_AREA'] == area][['TIME_PERIOD','OBS_VALUE']].dropna()
        if sub.empty:
            pieces.append(pd.Series(dtype=float, name=ccy))
            continue
        sub = sub.drop_duplicates('TIME_PERIOD', keep='last').set_index('TIME_PERIOD').sort_index()
        pieces.append(sub['OBS_VALUE'].rename(ccy))
    out = pd.concat(pieces, axis=1, sort=True).sort_index()
    out.index.name = 'date'
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='data/stage2b_policy_rates.csv')
    p.add_argument('--timeout', type=int, default=120)
    args = p.parse_args()
    out = fetch(args.timeout)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path)
    coverage = pd.DataFrame({'start': out.apply(lambda s:s.first_valid_index()), 'end':out.apply(lambda s:s.last_valid_index()), 'months':out.notna().sum()})
    print(coverage.to_string())
    print(f'wrote {path}: {len(out)} rows x {out.shape[1]} series')

if __name__ == '__main__':
    main()
