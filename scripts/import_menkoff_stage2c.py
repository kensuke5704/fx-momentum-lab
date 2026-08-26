from __future__ import annotations

import argparse
from pathlib import Path
import re

import pandas as pd


def _slug(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", str(value).strip().upper()).strip("_")


def inspect_workbook(path: str | Path) -> dict[str, list[str]]:
    xls = pd.ExcelFile(path)
    return {sheet: [str(c) for c in pd.read_excel(path, sheet_name=sheet, nrows=3).columns] for sheet in xls.sheet_names}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect/import the official Menkhoff et al. replication workbook for Stage 2C.")
    parser.add_argument("workbook")
    parser.add_argument("--inspect", action="store_true", help="Print sheet names and first-row column labels only; no transformation.")
    parser.add_argument("--out-dir", default="data/stage2c_menkoff")
    args = parser.parse_args()

    workbook = Path(args.workbook)
    if not workbook.exists():
        raise FileNotFoundError(workbook)

    structure = inspect_workbook(workbook)
    print("Workbook structure:")
    for sheet, cols in structure.items():
        print(f"- {sheet}: {cols}")

    if args.inspect:
        return

    # The historical JFE workbook schema is not assumed in advance. This importer
    # intentionally refuses to guess which sheets/columns are spot, 1M forward,
    # or precomputed excess returns. After the official workbook is received,
    # map its documented schema explicitly and commit that mapping before running
    # Stage 2C. This preserves the data-quality gate and avoids silent misuse.
    raise RuntimeError(
        "Official workbook received, but schema mapping is intentionally unset. "
        "Run with --inspect, document the workbook layout, then add an explicit "
        "sheet/column mapping before producing Stage 2C inputs."
    )


if __name__ == "__main__":
    main()
