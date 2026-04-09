# Scripts Quick Guide

This folder contains startup scripts to run FleetPredict Pro end-to-end:

- apply migrations
- start Daphne (ASGI)
- start telemetry simulator
- bootstrap ML model when missing
- keep continuous learning running in background

## Run Commands

### Linux / macOS

```bash
cd dev
./scripts/start_all.sh
```

### Windows PowerShell

```powershell
cd dev
powershell -ExecutionPolicy Bypass -File scripts/start_all.ps1
```

### Windows CMD / Double-click

```cmd
cd dev
scripts\start_all.bat
```

## Stop Everything

Press `Ctrl+C` in the same terminal/session where the script is running.

## Optional Environment Variables

- `ML_TRAINING_DATA_JSON` (default: `static/models/ml_training_data.json`)
- `ML_FAILURE_PREDICTOR_PATH` (default: `static/models/failure_predictor.joblib`)
- `ML_MIN_SAMPLES_TO_TRAIN` (default: `80`)
- `ML_CONTINUOUS_LEARNING_INTERVAL` (default: `900`, seconds)

## Notes

- Scripts are designed to be executed from the `dev/` directory.
- If `venv/` exists, scripts try to auto-activate it.
- Startup readiness accepts `2xx` and `3xx` responses from `http://127.0.0.1:8000/`.
