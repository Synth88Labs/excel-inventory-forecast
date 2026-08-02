# Test Results — Excel Demand & Inventory Forecaster

Full local test run + a live demo. CI re-runs the suite on Python 3.9, 3.11, 3.12.

## Unit tests

```
$ python -m pytest -v
tests/test_inventory.py::test_inv_norm_known_values         PASSED
tests/test_inventory.py::test_inv_norm_rejects_out_of_range PASSED
tests/test_inventory.py::test_reorder_point_math            PASSED
tests/test_inventory.py::test_safety_stock_uses_z_and_std   PASSED
tests/test_inventory.py::test_multiple_skus                 PASSED
tests/test_inventory.py::test_missing_column_raises         PASSED

======================= 6 passed =======================
```

**Result: 6/6 passed.**

### What each test proves
| Test | Verifies |
|---|---|
| `test_inv_norm_known_values` | The inverse-normal gives correct z: 0.5→0, 0.95→1.645, 0.975→1.960, 0.99→2.326 |
| `test_inv_norm_rejects_out_of_range` | Service levels of 0/1/out-of-range are rejected |
| `test_reorder_point_math` | Constant demand → safety stock 0, reorder = avg × lead time |
| `test_safety_stock_uses_z_and_std` | Safety stock = z × std × √(lead time) |
| `test_multiple_skus` | Each SKU is computed independently |
| `test_missing_column_raises` | A missing units/sku column raises a clear error |

## Live demo (sample_data/demand_history.csv — 2 SKUs, 14 days each)

```
$ python inventory.py sample_data/demand_history.csv --lead-time 7 --service-level 0.95

Demand & Inventory Forecast
  SKUs: 2   Lead time: 7   Service level: 95% (z=1.645)
    A: avg 20.29/period  ->  safety stock 11.6, reorder at 153.6
    B: avg 5.71/period   ->  safety stock 7.1,  reorder at 47.1
```

Output:

| sku | avg_demand | std_demand | lead_time | service_level | safety_stock | reorder_point |
|---|---|---|---|---|---|---|
| A | 20.29 | 2.67 | 7 | 0.95 | 11.6 | 153.6 |
| B | 5.71 | 1.64 | 7 | 0.95 | 7.1 | 47.1 |

**Interpretation:** for a 7-day lead time at a 95% service level, reorder SKU A when
stock hits ~154 units and SKU B at ~47 — the extra 11.6 / 7.1 units of safety stock
absorb normal demand variability so you don't stock out while waiting for resupply.
