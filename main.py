"""
A minimal FastAPI application exposing Bitcoin cycle metrics and risk level.
Run locally with: uvicorn main:app --reload
"""
from fastapi import FastAPI, HTTPException
from app_example import (
    fetch_metric,
    fetch_price_series,
    calculate_pi_cycle_proximity,
    calculate_risk_level,
)

app = FastAPI(title="Bitcoin Cycle Top API")

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to the Bitcoin Cycle Top API! Use /metrics to fetch current metrics."}

@app.get("/metrics")
def get_metrics() -> dict[str, float | str]:
    try:
        mvrv_z = fetch_metric("mvrv-zscore", "mvrvZscore")
        puell_multiple = fetch_metric("puell-multiple", "puellMultiple")
        reserve_risk = fetch_metric("reserve-risk", "reserveRisk")
        lth_sopr = fetch_metric("lth-sopr", "lthSopr")

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
