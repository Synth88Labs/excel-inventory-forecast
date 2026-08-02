# Excel Demand & Inventory Forecaster 📦

[![CI](https://github.com/Synth88Labs/excel-inventory-forecast/actions/workflows/ci.yml/badge.svg)](https://github.com/Synth88Labs/excel-inventory-forecast/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Turn sales history into the two numbers every stock-keeper actually needs:
**safety stock** and the **reorder point** — per SKU, for your lead time and target
service level.

Built for the operational question templates never answer: *"how low do I let this SKU
get before I reorder — without stocking out or over-ordering?"*

## The formulas (industry-standard)

```
safety stock  = z × demand_std × √(lead_time)
reorder point = avg_demand × lead_time + safety stock
```

`z` is the **service-level factor** from the normal distribution (95% → 1.645), computed
here with a proper inverse-normal function so *any* service level works — not just the
handful of hard-coded values most templates offer.

## Installation

```bash
git clone https://github.com/Synth88Labs/excel-inventory-forecast.git
cd excel-inventory-forecast
pip install -r requirements.txt
```

Requires Python 3.9+.

## Usage

```bash
python inventory.py <history.csv> --lead-time DAYS [--service-level 0.95] [-o reorder.csv]
```

Input is demand history — one row per period per SKU:

```
sku,day,units
A,1,20
A,2,18
B,1,5
```

### Quick start (try it on the included sample — 2 SKUs, 14 days each)

```bash
python inventory.py sample_data/demand_history.csv --lead-time 7 --service-level 0.95
```

Example output:

```
Demand & Inventory Forecast
  SKUs: 2   Lead time: 7   Service level: 95% (z=1.645)
    A: avg 20.x/period  ->  safety stock ~14, reorder at ~15x
    B: avg 5.x/period   ->  safety stock ~7,  reorder at ~4x
```

### Options

| Option | Description |
|---|---|
| `--lead-time DAYS` | **Required.** Lead time, in the same period unit as your rows |
| `--service-level` | Target service level 0–1. Default: 0.95 |
| `--sku-col` / `--units-col` | Column names (defaults: `sku`, `units`) |
| `-o`, `--output` | Output path (`.csv` or `.xlsx`) |

## Test results

See [TEST_RESULTS.md](TEST_RESULTS.md), or run them yourself:

```bash
pip install pytest
python -m pytest
```

## 📚 Learn More — Free Excel Tutorials

Practical Excel, inventory & forecasting guides at
**[ExcelGuru.io](https://excelguru.io/category/tutorials/)**.

## License

MIT — see [LICENSE](LICENSE).
