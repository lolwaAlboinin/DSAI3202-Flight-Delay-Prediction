"""Azure ML managed online endpoint scorer for DSAI3202 Flight Delay Prediction.

Input: {"data": [{nine precomputed features}, ...]}
Output: {"predictions": [{"prediction": 0|1, "delay_probability": float,
                           "threshold": 0.55, "model_version": "1"}, ...]}
Invalid requests raise ValueError. Serialized model must come from trusted source.
"""
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL = None
THRESHOLD = 0.55
FEATURES = [
    "Reporting_Airline", "Origin", "Dest", "Month", "CRSDepTime",
    "DepHour", "DayOfWeek", "IsWeekend", "Quarter"
]
TEXT_FIELDS = ["Reporting_Airline", "Origin", "Dest"]
NUMBER_FIELDS = [x for x in FEATURES if x not in TEXT_FIELDS]


def init():
    global MODEL
    root = os.environ.get("AZUREML_MODEL_DIR")
    if not root:
        raise RuntimeError("AZUREML_MODEL_DIR is not set")
    # Azure ML may mount model files inside a named/versioned subdirectory.
    files = list(Path(root).rglob("model.pkl"))
    if len(files) != 1:
        raise RuntimeError(f"Expected exactly one model.pkl under registered model: found {len(files)}")
    MODEL = joblib.load(files[0])
    if not hasattr(MODEL, "predict_proba"):
        raise RuntimeError("Registered model does not support predict_proba")


def _check_record(record):
    if not isinstance(record, dict):
        raise ValueError("Each flight must be a JSON object")
    missing = [name for name in FEATURES if name not in record]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    for name in TEXT_FIELDS:
        value = record[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a nonempty string")
    for name in NUMBER_FIELDS:
        value = record[name]
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise ValueError(f"{name} must be an integer")
    month, departure = record["Month"], record["CRSDepTime"]
    if not 1 <= month <= 12:
        raise ValueError("Month must be 1-12")
    if not (departure == 2400 or (0 <= departure <= 2359 and departure % 100 < 60)):
        raise ValueError("Invalid scheduled departure time")
    if record["DepHour"] != (0 if departure == 2400 else departure // 100):
        raise ValueError("DepHour does not match CRSDepTime")
    if record["Quarter"] != (month - 1) // 3 + 1:
        raise ValueError("Quarter does not match Month")
    if not 1 <= record["DayOfWeek"] <= 7:
        raise ValueError("DayOfWeek must be 1-7 (Sunday=1)")
    if record["IsWeekend"] != int(record["DayOfWeek"] in (1, 7)):
        raise ValueError("IsWeekend does not match DayOfWeek")
    return {key: record[key] for key in FEATURES}



def run(raw_data):
    if MODEL is None:
        raise RuntimeError("Model is not initialized")

    try:
        payload = (
            json.loads(raw_data)
            if isinstance(raw_data, (str, bytes, bytearray))
            else raw_data
        )

        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ValueError("Expected a JSON object with 'data': a list of flight records")

        if not 1 <= len(payload["data"]) <= 100:
            raise ValueError("Provide 1 to 100 flight records")

        rows = [_check_record(record) for record in payload["data"]]

    except (ValueError, TypeError) as error:
        return {
            "status": "error",
            "error_type": "InvalidInput",
            "message": str(error)
        }

    inputs = pd.DataFrame(rows, columns=FEATURES)
    probs = MODEL.predict_proba(inputs)[:, 1]

    predictions = [
        {
            "prediction": int(p >= THRESHOLD),
            "delay_probability": float(p),
            "threshold": THRESHOLD,
            "model_version": "1"
        }
        for p in probs
    ]

    return {"predictions": predictions}
