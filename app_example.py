"""
app_example.py
----------------

This script provides a reference implementation for fetching Bitcoin on‑chain
and macroeconomic indicators to assess cycle‑top risk. It demonstrates how
to query the free BGeometrics API for metrics such as the MVRV Z‑Score,
Puell Multiple, Reserve Risk and Long‑Term Holder SOPR. It also includes
functions for computing the Pi‑Cycle indicator using historical price data
and calculating a risk level based on a confluence of early warning signals.

The code is intended as a starting point for building a more complete
application. To use it in a production environment you should add proper
error handling, caching to respect API rate limits, authentication for
premium data providers and integration with a front‑end/dashboard.

Usage:
    python app_example.py

Environment variables or configuration files should be used to store API
keys securely in real deployments. For simplicity, API keys are defined
as constants below. Replace the placeholder values with your actual keys.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, Any

import pandas as pd
import requests

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# API keys (replace with your actual keys; DO NOT commit real keys to source
# control). It is recommended to load these from environment variables instead.
FRED_API_KEY = os.getenv("FRED_API_KEY", "YOUR_FRED_API_KEY")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY", "YOUR_COINGLASS_API_KEY")
CMC_API_KEY = os.getenv("CMC_API_KEY", "YOUR_COINMARKETCAP_API_KEY")

# Base URL for the BGeometrics API
BGEOMETRICS_BASE_URL = "https://bitcoin-data.com/api/v1"


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def fetch_json(url: str) -> Dict[str, Any]:
    """Fetch a JSON document from the given URL.

    Args:
        url: Full URL to fetch.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        requests.HTTPError: If the request fails or returns an error status.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


def fetch_metric(endpoint: str, field: str) -> float:
    """Fetch a single metric from BGeometrics and return its numeric value.

    The BGeometrics API exposes many endpoints under /api/v1. Each endpoint
    returns JSON with one or more fields. This helper fetches the latest
    value by appending '/last' to the endpoint and extracts the specified
    field.

    Args:
        endpoint: The endpoint name, e.g. 'mvrv-zscore'.
        field: The JSON field in the response that contains the value.

    Returns:
        The metric value as a float.

    Example:
        mvrv_z = fetch_metric('mvrv-zscore', 'mvrvZscore')
    """
    url = f"{BGEOMETRICS_BASE_URL}/{endpoint}/last"
    data = fetch_json(url)
    value = data.get(field)
    if value is None:
        raise KeyError(f"Field '{field}' not found in response from {url}")
    return float(value)


def fetch_price_series(days: int = 400) -> pd.Series:
    """Fetch Bitcoin price series from BGeometrics for the past `days` days.

    This function calls the `btc-price/last/{days}` endpoint, which returns
    daily closing prices for the specified number of days. The resulting
    pandas Series has a datetime index and float values.

    Args:
        days: The number of daily price points to retrieve.

    Returns:
        A pandas Series indexed by date with the closing price.
    """
    url = f"{BGEOMETRICS_BASE_URL}/btc-price/last/{days}"
    data = fetch_json(url)
    df = pd.DataFrame(data)
    df['d'] = pd.to_datetime(df['d'])
    df.set_index('d', inplace=True)
    return df['btcPrice'].astype(float)


def calculate_pi_cycle_proximity(prices: pd.Series) -> float:
    """Compute the Pi‑Cycle proximity indicator.

    The Pi‑Cycle indicator compares the 111‑day moving average (MA111) of
    Bitcoin's price against twice the 350‑day moving average (MA350). A
    proximity value near or above 1 suggests that MA111 is close to or above
    2×MA350, indicating a potential cycle top.

    Args:
        prices: Pandas Series of historical prices.

    Returns:
        The ratio MA111 / (2 * MA350) for the most recent day.
    """
    ma111 = prices.rolling(window=111).mean()
    ma350 = prices.rolling(window=350).mean()
    if len(ma350.dropna()) == 0:
        raise ValueError("Not enough price data to compute the Pi‑Cycle indicator."
                         " Need at least 350 days.")
    return float(ma111.iloc[-1] / (2 * ma350.iloc[-1]))


def calculate_risk_level(metrics: Dict[str, float]) -> str:
    """Calculate the overall risk level based on the confluence of metrics.

    The thresholds used here follow guidance from the user requirements. You
    may fine‑tune them based on further research or historical analysis.

    Args:
        metrics: A dictionary containing the following keys:
            - 'mvrv_z': MVRV Z‑Score
            - 'pi_cycle_proximity': Pi‑Cycle proximity (MA111/(2×MA350))
            - 'puell_multiple': Puell Multiple
            - 'lth_sopr': Long‑Term Holder SOPR
            - 'reserve_risk': Reserve Risk

    Returns:
        A string describing the risk category: 'EXTREME DANGER', 'HIGH RISK',
        'ELEVATED CAUTION' or 'ACCUMULATION/HOLD'.
    """
    # Count Tier‑1 signals exceeding their danger thresholds
    tier_1_signals = sum([
        metrics['mvrv_z'] > 7.0,
        metrics['pi_cycle_proximity'] > 0.95,
        metrics['puell_multiple'] > 4.0,
        metrics['lth_sopr'] > 10.0,
        metrics['reserve_risk'] > 0.02
    ])
    if tier_1_signals >= 3:
        return "EXTREME DANGER"
    elif tier_1_signals == 2:
        return "HIGH RISK"
    elif tier_1_signals == 1:
        return "ELEVATED CAUTION"
    else:
        return "ACCUMULATION/HOLD"


# -----------------------------------------------------------------------------
# Main script logic
# -----------------------------------------------------------------------------

def main() -> None:
    """Fetch metrics, compute risk level and display the results."""
    try:
        # Fetch on‑chain metrics
        mvrv_z = fetch_metric('mvrv-zscore', 'mvrvZscore')
        puell_multiple = fetch_metric('puell-multiple', 'puellMultiple')
        reserve_risk = fetch_metric('reserve-risk', 'reserveRisk')
        lth_sopr = fetch_metric('lth-sopr', 'lthSopr')

        # Fetch price series and compute Pi‑Cycle
        prices = fetch_price_series(400)
        pi_cycle_proximity = calculate_pi_cycle_proximity(prices)

        # Compose metrics dictionary
        metrics = {
            'mvrv_z': mvrv_z,
            'pi_cycle_proximity': pi_cycle_proximity,
            'puell_multiple': puell_multiple,
            'lth_sopr': lth_sopr,
            'reserve_risk': reserve_risk,
        }
        risk_level = calculate_risk_level(metrics)

        # Display results
        print("--- Bitcoin Cycle Top Metrics (latest) ---")
        for name, value in metrics.items():
            print(f"{name}: {value:.4f}")
        print(f"Overall risk level: {risk_level}")

    except requests.HTTPError as err:
        print(f"HTTP error occurred while fetching data: {err}")
    except Exception as exc:
        print(f"An unexpected error occurred: {exc}")


if __name__ == "__main__":
    main()