"""
app_example.py
--------------

This module fetches key Bitcoin cycle metrics from the free BGeometrics API,
pulls historical BTC price data via FRED, computes the Pi‑Cycle proximity,
and classifies the current risk level.

Functions:
    fetch_metric(endpoint: str, key: str) -> float
    fetch_price_series(days: int = 400) -> pandas.Series
    calculate_pi_cycle_proximity(prices: pandas.Series) -> float
    calculate_risk_level(metrics: dict[str, float]) -> str
"""

import os
import datetime
from typing import Dict

import pandas as pd
import pandas_datareader.data as web
import requests


BGEOMETRICS_BASE = "https://bitcoin-data.com/api/v1"
# Optional: if you wish to set FRED_API_KEY via environment variables
FRED_API_KEY = os.getenv("FRED_API_KEY")


def fetch_metric(endpoint: str, key: str) -> float:
    """
    Fetch the latest value for a given on‑chain metric from BGeometrics.
    Args:
        endpoint: API endpoint slug, e.g. 'mvrv-zscore'.
        key: JSON key containing the desired value.
    Returns:
        A float representing the latest value.
    Raises:
        RuntimeError if the request fails or the key is missing.
    """
    url = f"{BGEOMETRICS_BASE}/{endpoint}/last"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if key not in data:
            raise RuntimeError(f"Key '{key}' not found in response.")
        return float(data[key])
    except Exception as ex:
        raise RuntimeError(f"Failed to fetch {endpoint}: {ex}") from ex


def fetch_price_series(days: int = 400) -> pd.Series:
    """
    Retrieve daily BTC price history from FRED using pandas_datareader.
    Args:
        days: Number of days of history to fetch (default 400).
    Returns:
        pandas.Series indexed by date containing BTC prices.
    Raises:
        RuntimeError if the data retrieval fails.
    """
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)
    try:
        # 'CBBTCUSD' = CoinBase Bitcoin Price (USD) series on FRED
        df = web.DataReader('CBBTCUSD', 'fred', start_date, end_date,
                            api_key=FRED_API_KEY)
        # Drop NaN values and return the series
        prices = df['CBBTCUSD'].dropna().astype(float)
        if prices.empty:
            raise RuntimeError("Price series is empty.")
        return prices
    except Exception as ex:
        raise RuntimeError(f"Failed to fetch price series: {ex}") from ex


def calculate_pi_cycle_proximity(prices: pd.Series) -> float:
    """
    Compute the Pi‑Cycle proximity (distance to cross) based on two moving averages:
        - 111‑day simple moving average (SMA)
        - 350‑day SMA multiplied by 2.
    Args:
        prices: pandas.Series of BTC prices indexed by date.
    Returns:
        Proximity ratio between 0 and 1 (1 = cross imminent).
    """
    sma_short = prices.rolling(window=111).mean()
    sma_long = prices.rolling(window=350).mean() * 2
    # Align series and drop NaNs
    valid_idx = (~sma_short.isna()) & (~sma_long.isna())
    # Latest values
    short_val = sma_short[valid_idx].iloc[-1]
    long_val = sma_long[valid_idx].iloc[-1]
    if short_val == 0:
        return 0.0
    # Proximity = 1 – (distance between moving averages normalized by short MA)
    distance = abs(short_val - long_val) / short_val
    return 1.0 - min(distance, 1.0)


def calculate_risk_level(metrics: Dict[str, float]) -> str:
    """
    Classify the current risk level based on Tier‑1 indicators.
    Args:
        metrics: Dict containing keys:
            mvrv_z, pi_cycle_proximity, puell_multiple, lth_sopr, reserve_risk
    Returns:
        Risk level as a string.
    """
    mvrv_z = metrics["mvrv_z"]
    pi_cycle_prox = metrics["pi_cycle_proximity"]
    puell_multiple = metrics["puell_multiple"]
    lth_sopr = metrics["lth_sopr"]
    reserve_risk = metrics["reserve_risk"]
    tier_1_signals = sum([
        mvrv_z > 6.0,
        pi_cycle_prox > 0.95,
        puell_multiple > 3.0,
        lth_sopr > 8.0,
        reserve_risk > 0.015,
    ])
    if tier_1_signals >= 3:
        return "EXTREME DANGER"
    elif tier_1_signals >= 2:
        return "HIGH RISK"
    elif tier_1_signals >= 1:
        return "ELEVATED CAUTION"
    else:
        return "ACCUMULATION/HOLD"


if __name__ == "__main__":
    # Example CLI invocation to print metrics and risk
    metrics = {
        "mvrv_z": fetch_metric("mvrv-zscore", "mvrvZscore"),
        "pi_cycle_proximity": calculate_pi_cycle_proximity(
            fetch_price_series(400)
        ),
        "puell_multiple": fetch_metric("puell-multiple", "puellMultiple"),
        "lth_sopr": fetch_metric("lth-sopr", "lthSopr"),
        "reserve_risk": fetch_metric("reserve-risk", "reserveRisk"),
    }
    risk = calculate_risk_level(metrics)
    print(metrics)
    print(f"Risk Level: {risk}")
