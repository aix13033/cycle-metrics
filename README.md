# Bitcoin Cycle Top Application Example

This repository contains a simple example script (`app_example.py`) that
demonstrates how to fetch Bitcoin on‑chain metrics and compute a cycle‑top
risk level. It uses the free **BGeometrics** API to retrieve key
indicators (MVRV Z‑Score, Puell Multiple, Reserve Risk and Long‑Term Holder
SOPR) and calculates the **Pi‑Cycle proximity** using historical price data.
The script then combines these metrics with a confluence approach to
generate an overall risk classification.

## Files in this package

| File           | Description |
|---------------|------------|
| `app_example.py` | The main Python script that fetches data, computes the Pi‑Cycle indicator, counts danger signals and prints the current risk level. |
| `README.md`     | This file, providing usage instructions and background information. |
| `report.md`     | A comprehensive report summarising the relevant metrics, data sources and design recommendations for building a full Bitcoin cycle‑top monitoring app. |

## Prerequisites

1. **Python 3.8+** and pip installed on your system.
2. **Dependencies:**
   - `pandas`
   - `requests`

   You can install these packages with:

   ```bash
   pip install pandas requests
   ```

3. (Optional) **pandas_datareader** – if you plan to fetch macroeconomic data from FRED using Python instead of scraping the website.

## Usage

1. Clone or download the repository.
2. Replace the placeholder API keys in `app_example.py` with your own keys:

   - `FRED_API_KEY` – your FRED API key (for macro data, if used).
   - `COINGLASS_API_KEY` – your Coinglass API secret (for derivatives metrics).
   - `CMC_API_KEY` – your CoinMarketCap API key (for additional market data).

   You can also set these keys as environment variables (`FRED_API_KEY`,
   `COINGLASS_API_KEY`, `CMC_API_KEY`) to avoid hard‑coding them in the file.

3. Run the script:

```bash
python app_example.py
```

Upon execution the script will fetch the latest values from BGeometrics,
compute the Pi‑Cycle proximity and then classify the risk level according
to the confluence of metrics. The output will look something like:

```
--- Bitcoin Cycle Top Metrics (latest) ---
mvrv_z: 2.6011
pi_cycle_proximity: 0.8845
puell_multiple: 1.3320
lth_sopr: 2.9990
reserve_risk: 0.0026
Overall risk level: ACCUMULATION/HOLD
```

## Disclaimer

This example script is provided for educational purposes and should not be
considered financial advice. The thresholds and risk classifications are
guidelines based on historical observations and may not accurately predict
future market behaviour. Always perform your own research before making
investment decisions.

For more information about how to build a complete application—including
dashboard design, data refresh strategies and alert systems—please refer
to the accompanying `report.md` file.