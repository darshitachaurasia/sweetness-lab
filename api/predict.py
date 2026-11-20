"""Flask prediction API for the configured sensor feed and trained model."""
import json
import math
import os
from datetime import datetime, timezone
from functools import lru_cache

import joblib
import pandas as pd
import requests
from flask import Flask, jsonify

app = Flask(__name__)


@lru_cache(maxsize=1)
def load_configuration():
    with open(os.environ["SWEETNESS_FEATURES_FILE"], encoding="utf-8") as file:
        features = json.load(file)
    if (not isinstance(features, list) or not features
            or any(not isinstance(name, str) or not name for name in features)
            or len(set(features)) != len(features)):
        raise ValueError("Expected a list of unique feature names")
    model_path = os.environ["SWEETNESS_MODEL_FILE"]
    scaler_path = os.getenv("SWEETNESS_SCALER_FILE")
    thresholds = [float(value) for value in json.loads(os.environ["SWEETNESS_THRESHOLDS"])]
    if len(thresholds) != 4 or not all(map(math.isfinite, thresholds)) or sorted(set(thresholds), reverse=True) != thresholds:
        raise ValueError("Expected four strictly descending thresholds")
    return features, joblib.load(model_path), joblib.load(scaler_path) if scaler_path else None, thresholds


def error(message, status):
    return jsonify(ok=False, mode="live", error=message, status=status,
                   timestamp=datetime.now(timezone.utc).isoformat()), status


@app.get("/api/predict")
def predict():
    try:
        url = os.environ["SWEETNESS_SENSOR_URL"]
        features, model, scaler, thresholds = load_configuration()
    except Exception:
        app.logger.exception("Live prediction configuration is unavailable")
        return error("Live prediction needs a configured sensor feed and model artifacts.", 503)

    try:
        upstream = requests.get(url, timeout=(3, 5))
        upstream.raise_for_status()
        values = upstream.json()["values"]
        if isinstance(values, str):
            values = values.split(",")
        if isinstance(values, dict):
            values = [values[name] for name in features]
        if not isinstance(values, list) or len(values) != len(features):
            raise ValueError("Sensor count does not match the model feature list")
        if any(isinstance(value, bool) for value in values):
            raise ValueError("Boolean values are not sensor readings")
        numeric = [float(value) for value in values]
        if not all(map(math.isfinite, numeric)):
            raise ValueError("Sensor values must be finite")
    except requests.Timeout:
        return error("The sensor API request timed out.", 504)
    except (requests.RequestException, ValueError, TypeError, KeyError, OverflowError):
        return error("The sensor API did not provide a valid reading.", 502)

    try:
        frame = pd.DataFrame([numeric], columns=features)
        model_input = scaler.transform(frame) if scaler is not None else frame
        sweetness = round(float(model.predict(model_input)[0]), 2)
        if not math.isfinite(sweetness):
            raise ValueError("Model returned a non-finite score")
    except Exception:
        app.logger.exception("Sweetness prediction failed")
        return error("The model could not process the sensor reading.", 500)

    grade = next((label for label, cutoff in zip("ABCD", thresholds) if sweetness >= cutoff), "Below D")
    return jsonify(ok=True, mode="live", model=type(model).__name__, sweetness=sweetness,
                   grade=grade, timestamp=datetime.now(timezone.utc).isoformat(),
                   sensors=dict(zip(features, numeric)))
