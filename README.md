# VN25 Index

A custom Vietnamese equity index that removes Vingroup and Vietjet concentration risk from the VN30.

![VN25 vs VN30 Performance](vn25_vs_vn30_chart.png)

## Why VN25?

Vietnam's benchmark **VN30 Index** allocates a disproportionate weight to five tickers tied to a single conglomerate — **Vingroup** (VIC, VHM, VRE, VPL) and its affiliate **Vietjet** (VJC). This concentration means the index often reflects the fortune of one corporate group rather than the broader Vietnamese large-cap market.

**VN25 permanently excludes those five tickers** and re-weights the remaining 25 constituents using free-float market-cap weighting with a **10% per-stock cap**, producing a cleaner benchmark for Vietnam's blue-chip equities.

## Methodology

| Parameter | Detail |
|---|---|
| **Universe** | VN30 constituents (quarterly rebalanced by HOSE) |
| **Exclusions** | VIC, VHM, VRE, VPL, VJC |
| **Weighting** | Free-float market-cap weighted |
| **Single-stock cap** | 10% at each rebalance |
| **Rebalance frequency** | Quarterly (aligned with HOSE schedule) |
| **Base value** | 1,000 |
| **History** | Jan 2023 – present (~3 years) |

### Weight-Capping Algorithm

At each quarterly rebalance:
1. Compute raw weights from `free_float_pct × shares_for_index × close_price`
2. Cap any stock exceeding 10%
3. Redistribute excess weight pro-rata among uncapped stocks
4. Repeat until no stock breaches the cap

## Project Structure

```
vn25-index/
├── 02_fetch_historical_prices.py   # Fetch daily OHLCV for all VN30 tickers via vnstock
├── 03_simulate_vn25.py             # Build the VN25 index (exclude, weight, cap, chain-link)
├── 04_analyze_vn25_vs_vn30.py      # Compare VN25 vs real VN30 — metrics & chart
├── data/
│   ├── vn30_freefloat_history.csv  # Quarterly VN30 basket composition & free-float data
│   ├── vn25_historical_index.csv   # Output: daily VN25 index values
│   ├── vn25_daily_weights.csv      # Output: daily constituent weights
│   └── prices/                     # Daily OHLCV per ticker (ACB.csv, FPT.csv, …)
├── vn25_vs_vn30_chart.png          # Performance comparison chart
├── requirements.txt
├── LICENSE
└── README.md
```

## Pipeline

The pipeline runs in three steps:

### Step 1 — Fetch Prices (`02_fetch_historical_prices.py`)

Reads the unique tickers from `data/vn30_freefloat_history.csv` and downloads daily OHLCV data for each one using the [`vnstock`](https://github.com/thinh-vu/vnstock) library. Output is saved as one CSV per ticker under `data/prices/`.

### Step 2 — Simulate VN25 (`03_simulate_vn25.py`)

The core script. For each quarterly rebalance period:
- Loads the VN30 basket composition and daily prices
- Excludes the five Vingroup/Vietjet tickers
- Computes free-float market-cap weights with iterative 10% capping
- Chain-links daily returns to build a continuous index series (base = 1,000)

Outputs `data/vn25_historical_index.csv` and `data/vn25_daily_weights.csv`.

### Step 3 — Analyze (`04_analyze_vn25_vs_vn30.py`)

Fetches the real VN30 index, rebases both series to 1,000, and generates:
- A side-by-side performance chart (`vn25_vs_vn30_chart.png`)
- Key metrics: total return, annualized return, annualized volatility, max drawdown

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/vn25-index.git
cd vn25-index
pip install -r requirements.txt
```

### Usage

Run the scripts in order:

```bash
# 1. Download historical price data
python 02_fetch_historical_prices.py

# 2. Build the VN25 index
python 03_simulate_vn25.py

# 3. Generate comparison chart & metrics
python 04_analyze_vn25_vs_vn30.py
```

The performance chart will be saved as `vn25_vs_vn30_chart.png` in the project root.

## Data Sources

- **VN30 basket composition & free-float data** — Ho Chi Minh Stock Exchange (HOSE) quarterly announcements
- **Daily OHLCV prices** — [`vnstock`](https://github.com/thinh-vu/vnstock) (Python wrapper for Vietnamese market data)

## Limitations

- Free-float percentages are sourced from HOSE regulatory disclosures and may lag actual changes
- The index does not account for dividends (price-return only)
- Transaction costs and slippage from rebalancing are not modeled
- `vnstock` API availability may vary; historical data coverage depends on the upstream provider

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
