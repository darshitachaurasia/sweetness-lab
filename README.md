# Sweetness Lab

The website demonstrates sweetness grading with an illustrative sensor feed, scaler, linear estimator, and thresholds. Set a scenario in the simulator to see how malformed responses and timeouts affect the pipeline.

## Run the demo

Serve the static dashboard with `python -m http.server 8000 --directory public` and open http://localhost:8000. Vercel and Netlify configurations point to the public directory. Netlify serves the static demo. The Flask endpoint can run locally or on Vercel when the Python dependencies and model files are included.

## Connect the live Flask prediction route

Install the dependencies using `python -m pip install -r requirements.txt`. Use the same scikit-learn, NumPy, and Joblib versions used during training, and load model artifacts you trust.

| Environment variable | Value |
| --- | --- |
| SWEETNESS_SENSOR_URL | Sensor endpoint that returns the latest reading |
| SWEETNESS_FEATURES_FILE | Path to a JSON array of feature names in training order |
| SWEETNESS_MODEL_FILE | Path to the trained Joblib model |
| SWEETNESS_SCALER_FILE | Optional path to the fitted Joblib scaler |
| SWEETNESS_THRESHOLDS | JSON array with calibrated minimum scores for A, B, C, and D in descending order |

The upstream JSON must have a `values` field containing a feature-name mapping, a numeric array, or a comma-separated string in training order. If your feed uses another format, update the extraction in `api/predict.py`.

Start the endpoint with `python -m flask --app api.predict run` and request `GET http://localhost:5000/api/predict`. The route returns the sweetness score, grade, model name, sensor readings, and prediction timestamp. The dashboard remains an independent simulation and previews the equivalent response.
