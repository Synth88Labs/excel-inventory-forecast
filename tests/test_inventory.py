"""Tests for Excel Demand & Inventory Forecaster. Run with:  python -m pytest"""

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inventory import compute, inv_norm  # noqa: E402


def test_inv_norm_known_values():
    assert abs(inv_norm(0.5) - 0.0) < 1e-6
    assert abs(inv_norm(0.95) - 1.6449) < 1e-3
    assert abs(inv_norm(0.975) - 1.95996) < 1e-3
    assert abs(inv_norm(0.99) - 2.32635) < 1e-3


def test_inv_norm_rejects_out_of_range():
    for p in (0, 1, -0.1, 1.5):
        try:
            inv_norm(p)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for p={p}")


def test_reorder_point_math():
    # constant demand of 10/day, std 0 -> safety 0, reorder = 10*lead
    df = pd.DataFrame({"sku": ["X"] * 5, "units": [10, 10, 10, 10, 10]})
    out = compute(df, "sku", "units", lead_time=7, service_level=0.95)
    row = out.iloc[0]
    assert row["avg_demand"] == 10
    assert row["std_demand"] == 0
    assert row["safety_stock"] == 0
    assert row["reorder_point"] == 70


def test_safety_stock_uses_z_and_std():
    df = pd.DataFrame({"sku": ["X"] * 4, "units": [8, 12, 8, 12]})  # mean 10, std=2.309...
    out = compute(df, "sku", "units", lead_time=4, service_level=0.95)
    row = out.iloc[0]
    std = pd.Series([8, 12, 8, 12]).std(ddof=1)
    expected_safety = 1.6449 * std * math.sqrt(4)
    assert abs(row["safety_stock"] - round(expected_safety, 1)) < 0.2


def test_multiple_skus():
    df = pd.DataFrame({"sku": ["A", "A", "B", "B"], "units": [20, 20, 5, 5]})
    out = compute(df, "sku", "units", lead_time=7, service_level=0.9)
    assert set(out["sku"]) == {"A", "B"}
    assert out[out["sku"] == "A"].iloc[0]["reorder_point"] == 140  # 20*7, std 0


def test_missing_column_raises():
    df = pd.DataFrame({"sku": ["A"], "units": [1]})
    try:
        compute(df, "sku", "nope", 7, 0.95)
    except ValueError:
        return
    raise AssertionError("expected ValueError for missing column")
