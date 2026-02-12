#!/usr/bin/env bash
# FleetPredict Pro - Start everything: migrations, ASGI server, telemetry simulator,
# and (if no model) wait for enough data to train; then continuous learning (retrain from JSON periodically).
# Run from dev/: ./start_all.sh
# Stop: Ctrl+C (or kill the PIDs shown).

set -e

DEV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DEV_DIR"

ML_JSON="${ML_TRAINING_DATA_JSON:-media/models/ml_training_data.json}"
ML_MODEL="${ML_FAILURE_PREDICTOR_PATH:-media/models/failure_predictor.joblib}"
MIN_SAMPLES="${ML_MIN_SAMPLES_TO_TRAIN:-80}"
CL_INTERVAL="${ML_CONTINUOUS_LEARNING_INTERVAL:-900}"

# Optional: activate venv if present
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
  echo "[*] Activating venv..."
  # shellcheck source=/dev/null
  source venv/bin/activate
fi

echo "[*] Checking migrations..."
python manage.py migrate --noinput

echo "[*] Ensuring ML model directory exists..."
mkdir -p media/models

echo "[*] Starting ASGI server (Daphne) on http://127.0.0.1:8000 ..."
python -m daphne -b 127.0.0.1 -p 8000 fleetpredict.asgi:application &
SERVER_PID=$!

# Wait for server to be up
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/" 2>/dev/null | grep -q 200; then
    break
  fi
  sleep 1
done

echo "[*] Starting telemetry simulator (WebSocket clients)..."
python -m simulators.telemetry_client --url "ws://127.0.0.1:8000/ws/telemetry/" --interval 2 &
SIM_PID=$!

CL_PID=""
if [ ! -f "$ML_MODEL" ]; then
  echo "[*] No ML model found. Waiting for enough telemetry to train (min $MIN_SAMPLES samples)..."
  while true; do
    python manage.py build_ml_dataset --output-json "$ML_JSON" --days 90 2>/dev/null || true
    COUNT=0
    [ -f "$ML_JSON" ] && COUNT=$(python -c "import json; d=json.load(open('$ML_JSON')); print(len(d.get('samples',[])))" 2>/dev/null) || true
    COUNT=${COUNT:-0}
    if [ "$COUNT" -ge "$MIN_SAMPLES" ] 2>/dev/null; then
      echo "[*] Samples: $COUNT. Training model..."
      if python manage.py train_failure_predictor --input-json "$ML_JSON"; then
        echo "[*] Model saved to $ML_MODEL"
        break
      fi
    else
      echo "[*] Samples: $COUNT / $MIN_SAMPLES. Waiting 60s for more telemetry..."
    fi
    sleep 60
  done
fi

# Continuous learning: periodically rebuild JSON from DB and retrain (model file updated; app picks it up on next restart or cache clear)
(
  while true; do
    sleep "$CL_INTERVAL"
    python manage.py build_ml_dataset --output-json "$ML_JSON" --days 90 2>/dev/null || true
    [ -f "$ML_JSON" ] && python manage.py train_failure_predictor --input-json "$ML_JSON" 2>/dev/null || true
  done
) &
CL_PID=$!

cleanup() {
  echo ""
  echo "[*] Stopping server, simulator and continuous learning..."
  kill "$SERVER_PID" 2>/dev/null || true
  kill "$SIM_PID" 2>/dev/null || true
  [ -n "$CL_PID" ] && kill "$CL_PID" 2>/dev/null || true
  exit 0
}

trap cleanup INT TERM

echo ""
echo "=============================================="
echo "  FleetPredict Pro is running"
echo "=============================================="
echo "  App:        http://127.0.0.1:8000/"
echo "  WebSocket:  ws://127.0.0.1:8000/ws/telemetry/"
echo "  Server PID: $SERVER_PID"
echo "  Simulator:  $SIM_PID"
echo "  Training:   $ML_JSON (continuous learning every ${CL_INTERVAL}s)"
echo ""
echo "  ML model: $ML_MODEL (reloaded on app restart after retrain)."
echo "  Press Ctrl+C to stop all."
echo "=============================================="
echo ""

wait $SERVER_PID $SIM_PID 2>/dev/null || true
cleanup
