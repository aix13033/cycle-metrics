# Bitcoin Cycle Top Web App – Metrics Integration & Technical Recommendations

## 1 Key metrics and their data sources

### Tier 1 – Core Early‑warning indicators
| metric/indicator | Description & available data source | Latest values/notes |
|---|---|---|
| **MVRV Z‑Score** | Measures how far Bitcoin’s market‑value‑to‑realized‑value (MVRV) ratio deviates from its long‑term average. High Z‑scores signal overheated markets. The open BGeometrics API provides a `mvrv-zscore/last` endpoint returning the latest value and date. The last response (Jul 28 2025) showed an MVRV Z‑score of **≈2.60**【959812087674982†L0】, which is below the extreme‑danger threshold (>7). | Use `https://bitcoin-data.com/api/v1/mvrv-zscore/last`. Rate‑limit: 10 calls/hour. |
| **Pi‑Cycle Top Indicator** | Based on the relationship between the 111‑day moving average (MA111) and twice the 350‑day moving average (2×MA350). A “cross” (MA111 > 2×MA350) historically marked cycle tops. BGeometrics does not provide a Pi‑Cycle endpoint, but its `btc-price` endpoints supply daily price data that can be used to compute the moving averages. Alternatively, Coinglass offers a Pi‑Cycle API (via your Coinglass key) if accessible. When computing manually, fetch at least 350 days of closing prices, calculate MA111 and 2×MA350 and monitor the proximity (e.g., ratio MA111/(2×MA350)). |
| **Puell Multiple** | Measures miner revenue compared with its long‑term average. High readings (>4) historically coincided with cycle tops. BGeometrics’ `puell-multiple/last` endpoint returned **≈1.332**【991472969883961†L0】 on Jul 28 2025. |
| **Reserve Risk** | Gauges long‑term holder confidence relative to market price. BGeometrics’ `reserve-risk/last` endpoint gave **≈0.002553**【181727746679687†L0】, far below the historical peak danger threshold (>0.02). |
| **Long‑Term Holder SOPR** | Reflects profitability of long‑term holders (LTH). High values (>10) indicate heavy profit‑taking. BGeometrics’ `lth-sopr/last` returned **≈2.999**【919901331135327†L0】 on Jul 28 2025. |
| **Long‑Term Holder MVRV** (supplementary) | Additional gauge of unrealised profit for long‑term holders. BGeometrics’ `lth-mvrv/last` endpoint reported **≈3.310**【201317256265637†L0】. |

### Tier 2 – Macro‑context dashboard

| macro indicator | Data source (latest observation) | Latest value & interpretation |
|---|---|---|
| **10‑year U.S. Treasury yield (DGS10)** | FRED series `DGS10`. The FRED dataset page reports the yield at **4.42 % on Jul 28 2025**【179953011931471†L85-L96】, slightly below the danger threshold (4.5 %). |
| **Federal funds rate** | FRED series `FEDFUNDS`. The effective federal funds rate for **Jun 2025 was 4.33 %**【207153598891283†L80-L97】. The next FOMC meeting (July 30 2025) could change this level. |
| **Dollar index (DXY proxy – Nominal Broad U.S. Dollar Index, DTWEXBGS)** | FRED series `DTWEXBGS`. The index measured **120.4082 on Jul 25 2025**【278708516359796†L80-L97】. Levels above ~106 historically signal dollar strength headwinds for Bitcoin. |
| **Bitcoin–S&P 500 correlation** | Requires price series for Bitcoin and the S&P 500. FRED provides S&P 500 daily closes (`SP500`), which were **6 389.77 on Jul 28 2025**【756766616643897†L80-L99】. Bitcoin prices can be pulled from BGeometrics (`btc-price` endpoint) or Coinglass. Compute the Pearson correlation of daily returns over a rolling window (e.g., 90 days); values above 0.8 indicate high risk‑on correlation. |
| **VIX (fear index)** | FRED series `VIXCLS`. The CBOE VIX closed at **15.03 on Jul 28 2025**【398546018291205†L80-L100】—well below the stress threshold (>30). |
| **Fed funds futures and macro events** | Use your FRED key or data sources such as CME FedWatch for probabilities of rate changes. Track FOMC meeting dates and macro releases. |

### Tier 3 – Market‑structure signals

| metric | Data source & notes | Comments |
|---|---|---|
| **Bitcoin dominance** | BGeometrics’ `bitcoin-dominance/last` endpoint returns dominance as a percentage of total crypto market cap; it was **≈59.55 %**【565239523392116†L0】 on Jul 28 2025. Values >65 % often coincide with cycle peaks, while drops below 60 % can signal alt‑season risk. |
| **Fear & Greed index** | Alternative.me API (`https://api.alternative.me/fng/`). The call returns current score and classification—on Jul 29 2025 the index was **73 (Greed)**【893915420670456†L0-L8】. |
| **Funding rates & liquidations** | Coinglass API (needs your Coinglass key) provides funding rates and liquidation data; BGeometrics also offers a `funding-rate/last` endpoint but is limited to 10 calls/hour. Positive funding rates above 1 % suggest excessive long positioning. |
| **Put/Call ratio** | CBOE publishes the total option put/call ratio (symbol `PCC`); this is available via market data providers (e.g., Alpha Vantage or Yahoo Finance). Look for values below 0.4 (complacency) or above 1.0 (fear). |
| **Exchange inflows/outflows** | Glassnode or BGeometrics (`exchange-inflows/last`) can supply daily BTC inflow volumes; >30 k BTC/day may precede selling pressure. |
| **Other metrics** | Open interest, futures curves, liquidations and DeFi TVL may require Coinglass, CoinMarketCap or DeFi Llama APIs. |

## 2 Designing the app’s structure

1. **Data ingestion layer**  
   - Create scheduled tasks (e.g., with Celery or cron) that pull data from BGeometrics, FRED, alternative.me and other APIs at different refresh rates. The provided example shows typical refresh frequencies (price: 1 min, on‑chain: hourly, macro: 4 hours, derivatives: 15 min).  
   - Implement caching to respect rate limits; store both latest values and historical series (e.g., 400 days of price to compute moving averages). Use a database (PostgreSQL or TimescaleDB) to persist time‑series data.
   - Because some APIs require headers (CoinMarketCap, Coinglass), use Python `requests` with `X-CMC_PRO_API_KEY` or `coinglassSecret` set in request headers. The container cannot fetch remote URLs directly, but within your production environment these calls should work.

2. **Indicator computation**

   - **MVRV Z‑Score, Puell Multiple, Reserve Risk, LTH SOPR/MVRV**: parse JSON from BGeometrics endpoints.  
   - **Pi‑Cycle**: after storing daily closing prices, compute `MA111` and `MA350` using a rolling window. The Pi‑Cycle proximity can be defined as `ma111 / (2*ma350)`. A value approaching or exceeding 1 signals risk.  
   - **Bitcoin–S&P 500 correlation**: compute log‑returns over a 90‑day window for BTC and S&P 500; use `pandas.Series.rolling(window=90).corr()`.

3. **Risk‑level calculation & alerts**

   - Use the provided function to classify the environment. Adjust thresholds if research suggests improved accuracy.  
   - When ≥3 Tier‑1 indicators exceed danger thresholds, mark the **risk level** as “EXTREME DANGER”; 2 triggers “HIGH RISK”; 1 triggers “ELEVATED CAUTION”; otherwise “ACCUMULATION/HOLD”.  
   - Send email/SMS/push alerts (via Twilio or SendGrid) when risk level escalates. Provide daily summaries and weekly trend reports.

4. **User interface**

   - **Executive dashboard (Page 1)**: display the overall risk level with a color‑coded traffic light; show how many of the 15 critical indicators are triggered; current BTC price vs the $135k cycle‑top target and progress bar; next review date (based on indicator refresh schedules).  
   - **On‑chain deep dive (Page 2)**: include interactive charts for MVRV Z‑score, Pi‑Cycle moving averages, Puell Multiple, LTH‑SOPR and exchange flows. Use line charts with historical overlays (2017 and 2021 cycles) and regression bands.  
   - **Macro environment (Page 3)**: display Fed policy tracker (current fed funds rate and FOMC meeting schedule), 10‑year yield trend with shading at 4.5 %, dollar index vs Bitcoin performance, correlation matrix heat map and ETF flows.  
   - **Market microstructure (Page 4)**: show funding rates, futures curves contango/backwardation, options term structure, Bitcoin dominance, DeFi TVL and mining economics (hash rate, profitability).  
   - **Historical context (Page 5)**: compare current cycle with 2017 and 2021 using normalized charts; show days since cycle low (current ~925 days); highlight seasonal patterns; include recommended exit strategies by risk level.

   Use responsive web technologies: for example, build the backend with **FastAPI** or **Flask** (Python) and the frontend with **React** plus **Ant Design** or **TailwindCSS**. Charting libraries like **Plotly.js**, **D3.js** or **ECharts** provide interactive zooming and overlays. Implement progress bars and gauges for distance to thresholds.

5. **September 2025 features**

   - **Countdown timer**: compute days until the expected window (September 5–10 2025) and display milestones (30‑day and 7‑day reminders).  
   - **Scenario modelling**: create an interface where users can simulate “what if” scenarios (e.g., BTC hitting $130k by Aug 15 or Pi‑Cycle crossing at a certain price). These can adjust risk thresholds and show projected metric paths.  
   - **Position management tools**: provide calculators for dollar‑cost‑averaging exit strategies, tax‑loss harvesting windows and profit‑taking ladders based on user risk profiles.

## 3 Sample Python code snippets

Below is an illustrative example (to be adapted in your production environment) showing how to fetch data and compute indicators using Python. Replace the placeholder keys with your own and handle exceptions and caching.

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

# API keys
GLASSNODE_API_KEY = 'YOUR_GLASSNODE_KEY'
FRED_API_KEY = 'bf43fb90b9f787dfae4b7fc15c24e7a0'
CMC_API_KEY = 'a7a7e85b-9bf3-41ac-9c1d-6da915e1b4bf'

# Example: fetch latest on‑chain metrics from BGeometrics
base_url = 'https://bitcoin-data.com/api/v1'
def fetch_metric(endpoint: str, field: str) -> float:
    """Fetch a single metric and return its numeric value"""
    url = f"{base_url}/{endpoint}/last"
    resp = requests.get(url, timeout=10)
    data = resp.json()
    return float(data[field])

mvrv_z = fetch_metric('mvrv-zscore', 'mvrvZscore')
puell = fetch_metric('puell-multiple', 'puellMultiple')
reserve_risk = fetch_metric('reserve-risk', 'reserveRisk')
lth_sopr = fetch_metric('lth-sopr', 'lthSopr')

# Example: compute Pi‑Cycle proximity using price series
def fetch_price_series(days: int = 400) -> pd.Series:
    url = f"{base_url}/btc-price/last/{days}"
    resp = requests.get(url, timeout=10)
    df = pd.DataFrame(resp.json())
    df['d'] = pd.to_datetime(df['d'])
    df.set_index('d', inplace=True)
    return df['btcPrice'].astype(float)

prices = fetch_price_series(400)
ma111 = prices.rolling(window=111).mean()
ma350 = prices.rolling(window=350).mean()
pi_cycle_proximity = ma111.iloc[-1] / (2 * ma350.iloc[-1])

# Example: risk‑level calculation
risk_level = calculate_risk_level({
    'mvrv_z': mvrv_z,
    'pi_cycle_proximity': pi_cycle_proximity,
    'puell_multiple': puell,
    'lth_sopr': lth_sopr,
    'reserve_risk': reserve_risk
})
print('Current risk level:', risk_level)

# Example: fetch macro data from FRED (requires proper API call – use in production)
import pandas_datareader.data as web
end = datetime.today()
start = end - timedelta(days=30)
dgs10 = web.DataReader('DGS10', 'fred', start, end)
sp500 = web.DataReader('SP500', 'fred', start, end)
# compute 90‑day correlation using rolling window
returns_btc = prices.pct_change().dropna()
returns_sp = sp500['SP500'].pct_change().dropna()
combined = pd.concat([returns_btc, returns_sp], axis=1).dropna()
correlation = combined[returns_btc.name].rolling(90).corr(combined['SP500']).iloc[-1]
print('BTC–SP500 correlation (90d):', correlation)
```

### Notes
- The script uses `pandas_datareader` to pull macro series from FRED.  
- For Coinglass or CoinMarketCap calls, use appropriate endpoints with required headers and respect rate limits.  
- Implement error handling (API downtime, missing data) and caching to limit repeated calls.

## 4 Practical tips and common pitfalls

1. **Respect data provider terms and cache data** – BGeometrics allows ~30 calls/hour; Coinglass and FRED also have limits. Store responses locally and update only as needed.  
2. **Don’t over‑optimize thresholds** – the provided thresholds are guides; avoid curve‑fitting to past cycles. Periodically review and adjust thresholds as market structure evolves (e.g., the impact of spot ETFs).  
3. **Display last update time and data source** – each metric should indicate when it was last refreshed and which provider supplied the data to maintain transparency.  
4. **Simplify user experience** – avoid overwhelming users with too many numbers; use visual cues (colour‑coded gauges, tool‑tips) and provide “learn more” links for deeper explanations.  
5. **Plan for mobile responsiveness** – design the dashboard using responsive frameworks; keep the top section with the current price, risk level and timer always visible.

## Conclusion

Building a Bitcoin cycle‑top monitoring app requires integrating on‑chain signals, macroeconomic data and market micro‑structure metrics into a single, coherent dashboard. The BGeometrics API offers free access to key on‑chain indicators (MVRV Z‑score, Puell Multiple, Reserve Risk, LTH SOPR/MVRV and Bitcoin dominance), while FRED provides macro series like treasury yields, fed funds rate, dollar index and volatility (VIX). Supplement these with data from Coinglass (funding rates, Pi‑Cycle and derivatives), CoinMarketCap (dominance, ETF flows) and alternative.me (fear & greed). Compute derived metrics such as the Pi‑Cycle indicator and Bitcoin–SP500 correlation locally using stored price series. Use the provided risk‑level calculator as the core of an alert system, and design the interface with clear visual hierarchy, scenario modelling and September 2025 countdown features so users can quickly answer “How close are we to the top?” and “What should I do about it?”.
