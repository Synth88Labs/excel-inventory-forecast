"""
inventory.py — Excel Demand & Inventory Forecaster.

Turns sales history into the two numbers every stock-keeper actually needs:
the **safety stock** and the **reorder point** — per SKU, for your lead time and
target service level.

Input is a CSV of demand history:

    sku,day,units
    A,1,20
    A,2,18
    B,1,5
    ...

The tool aggregates each SKU's demand, then computes:

    safety stock  = z * demand_std * sqrt(lead_time)
    reorder point = avg_demand * lead_time + safety stock

where z comes from your service level (95% -> 1.645) via the normal distribution.

Usage:
    python inventory.py <history.csv> --lead-time DAYS [--service-level 0.95]
                        [--units-col units] [--sku-col sku] [-o reorder.csv]

Author: Synth88Labs
License: MIT
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd


def inv_norm(p: float) -> float:
    """Inverse standard-normal CDF (Acklam's rational approximation)."""
    if p <= 0 or p >= 1:
        raise ValueError("service level must be strictly between 0 and 1")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5]) * q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def compute(df: pd.DataFrame, sku_col: str, units_col: str,
            lead_time: float, service_level: float) -> pd.DataFrame:
    for col in (sku_col, units_col):
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found. Available: {', '.join(map(str, df.columns))}")
    z = inv_norm(service_level)
    df = df.copy()
    df[units_col] = pd.to_numeric(df[units_col], errors="coerce")
    rows = []
    for sku, grp in df.groupby(sku_col, sort=False):
        demand = grp[units_col].dropna()
        if demand.empty:
            continue
        avg = demand.mean()
        std = demand.std(ddof=1)
        if pd.isna(std):
            std = 0.0
        safety = z * std * math.sqrt(lead_time)
        reorder = avg * lead_time + safety
        rows.append({
            "sku": sku,
            "avg_demand": round(avg, 2),
            "std_demand": round(std, 2),
            "lead_time": lead_time,
            "service_level": service_level,
            "safety_stock": round(safety, 1),
            "reorder_point": round(reorder, 1),
        })
    return pd.DataFrame(rows)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Compute safety stock and reorder points from demand history.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", type=Path, help="CSV/XLSX of demand history.")
    p.add_argument("--lead-time", type=float, required=True, help="Lead time (in the same period as your demand rows, e.g. days).")
    p.add_argument("--service-level", type=float, default=0.95, help="Target service level 0-1. Default: 0.95")
    p.add_argument("--sku-col", default="sku", help="SKU column name. Default: sku")
    p.add_argument("--units-col", default="units", help="Demand/units column name. Default: units")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output path (.csv or .xlsx).")
    p.add_argument("--sheet", default=None, help="For Excel input: sheet name (default: first).")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if not args.input.is_file():
        print(f"Error: '{args.input}' is not a file.", file=sys.stderr)
        return 1
    if not (0 < args.service_level < 1):
        print("Error: --service-level must be between 0 and 1 (e.g. 0.95).", file=sys.stderr)
        return 1
    try:
        if args.input.suffix.lower() == ".csv":
            df = pd.read_csv(args.input)
        else:
            df = pd.read_excel(args.input, sheet_name=args.sheet if args.sheet is not None else 0)
        result = compute(df, args.sku_col, args.units_col, args.lead_time, args.service_level)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if result.empty:
        print("No demand data found.", file=sys.stderr)
        return 1

    out_path = args.output or args.input.with_name(f"{args.input.stem}_reorder.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() == ".csv":
        result.to_csv(out_path, index=False)
    else:
        result.to_excel(out_path, index=False, sheet_name="Reorder")

    z = inv_norm(args.service_level)
    print("Demand & Inventory Forecast")
    print(f"  SKUs: {len(result)}   Lead time: {args.lead_time:g}   "
          f"Service level: {args.service_level:.0%} (z={z:.3f})")
    for _, r in result.iterrows():
        print(f"    {r['sku']}: avg {r['avg_demand']:g}/period  ->  "
              f"safety stock {r['safety_stock']:g}, reorder at {r['reorder_point']:g}")
    print(f"\nSaved: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
