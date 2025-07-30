"""
main.py
-------

A minimal FastAPI application exposing Bitcoin cycle metrics and the
overall risk level. It reuses helper functions defined in app_example.py
and provides a simple API for deployment on services like Render.
"""

from fastapi import FastAPI, HTTPException
from app_example import (
    fetch_metric,
    fetch_price_series,
    calculate_pi_cycle_proximity,
    calculate_risk_level,
)

app = FastAPI(
    title="Bitcoin Cycle Top API",
    description="Endpoints to fetch Bitcoin cycle metrics.",
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint with a welcome message."""
    return {
        "message": "Welcome to the Bitcoin Cycle Top API! Use /metrics to fetch current metrics."
    }


@app.get("/metrics")
def get_metrics() -> dict[str, float | str]:
    """
    Return the latest metrics and overall risk level.
    Raises HTTPException on failure.
    """
    try:
        mvrv_z = fetch_metric("mvrv-zscore", "mvrvZscore")
        puell_multiple = fetch_metric("puell-multiple", "puellMultiple")
        reserve_risk = fetch_metric("reserve-risk", "reserveRisk")
        lth_sopr = fetch_metric("lth-sopr", "lthSopr")
        # Fetch price series for Pi‑Cycle
        prices = fetch_price_series(400)
        pi_cycle_proximity = calculate_pi_cycle_proximity(prices)
        metrics = {
            "mvrv_z": mvrv_z,
            "pi_cycle_proximity": pi_cycle_proximity,
            "puell_multiple": puell_multiple,
            "lth_sopr": lth_sopr,
            "reserve_risk": reserve_risk,
        }
        risk_level = calculate_risk_level(metrics)
        return {**metrics, "risk_level": risk_level}
    except Exception as err:
        raise HTTPException(status_code=503, detail=str(err))
