# FleetPredict Pro - Start everything (Windows): migrations, ASGI server, telemetry simulator,
# and (if no model) wait for enough data to train; then continuous learning.
# Run from dev/: powershell -ExecutionPolicy Bypass -File start_all.ps1
# Or: .\start_all.bat
# Stop: Ctrl+C

$ErrorActionPreference = "Stop"

$DevDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $DevDir

$ML_JSON = if ($env:ML_TRAINING_DATA_JSON) { $env:ML_TRAINING_DATA_JSON } else { "static/models/ml_training_data.json" }
$ML_MODEL = if ($env:ML_FAILURE_PREDICTOR_PATH) { $env:ML_FAILURE_PREDICTOR_PATH } else { "static/models/failure_predictor.joblib" }
$MIN_SAMPLES = if ($env:ML_MIN_SAMPLES_TO_TRAIN) { [int]$env:ML_MIN_SAMPLES_TO_TRAIN } else { 80 }
$CL_INTERVAL = if ($env:ML_CONTINUOUS_LEARNING_INTERVAL) { [int]$env:ML_CONTINUOUS_LEARNING_INTERVAL } else { 900 }

# Optional: activate venv if present
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "[*] Activating venv..."
    & "venv\Scripts\Activate.ps1"
}

Write-Host "[*] Checking migrations..."
python manage.py migrate --noinput

Write-Host "[*] Ensuring ML model directory exists..."
New-Item -ItemType Directory -Force -Path "static\models" | Out-Null

# Processes to kill on exit
$script:ServerProc = $null
$script:SimProc = $null
$script:CLJob = $null

function Stop-AllProcesses {
    Write-Host ""
    Write-Host "[*] Stopping server, simulator and continuous learning..."
    if ($script:ServerProc -and !$script:ServerProc.HasExited) {
        $script:ServerProc.Kill()
    }
    if ($script:SimProc -and !$script:SimProc.HasExited) {
        $script:SimProc.Kill()
    }
    if ($script:CLJob) {
        Stop-Job $script:CLJob -ErrorAction SilentlyContinue
        Remove-Job $script:CLJob -ErrorAction SilentlyContinue
    }
}

try {
    Write-Host "[*] Starting ASGI server (Daphne) on http://127.0.0.1:8000 ..."
    $script:ServerProc = Start-Process -FilePath "python" -ArgumentList "-m", "daphne", "-b", "127.0.0.1", "-p", "8000", "fleetpredict.asgi:application" -PassThru -NoNewWindow

    # Wait for server to be up
    $maxAttempts = 10
    $attempt = 0
    $ready = $false
    while ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 1
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { $ready = $true; break }
        } catch {}
        $attempt++
    }

    Write-Host "[*] Starting telemetry simulator (WebSocket clients)..."
    $script:SimProc = Start-Process -FilePath "python" -ArgumentList "-m", "simulators.telemetry_client", "--url", "ws://127.0.0.1:8000/ws/telemetry/", "--interval", "2" -PassThru -NoNewWindow

    # If no ML model, wait for enough data and train
    if (!(Test-Path $ML_MODEL)) {
        Write-Host "[*] No ML model found. Waiting for enough telemetry to train (min $MIN_SAMPLES samples)..."
        while ($true) {
            python manage.py build_ml_dataset --output-json $ML_JSON --days 90 2>$null
            $COUNT = 0
            if (Test-Path $ML_JSON) {
                try {
                    $json = Get-Content $ML_JSON -Raw | ConvertFrom-Json
                    $COUNT = if ($json.samples) { @($json.samples).Count } else { 0 }
                } catch { $COUNT = 0 }
            }
            if ($COUNT -ge $MIN_SAMPLES) {
                Write-Host "[*] Samples: $COUNT. Training model..."
                python manage.py train_failure_predictor --input-json $ML_JSON
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[*] Model saved to $ML_MODEL"
                    break
                }
            } else {
                Write-Host "[*] Samples: $COUNT / $MIN_SAMPLES. Waiting 60s for more telemetry..."
            }
            Start-Sleep -Seconds 60
        }
    }

    # Continuous learning: run in background job
    $script:CLJob = Start-Job -ScriptBlock {
        param($DevDir, $ML_JSON, $CL_INT)
        Set-Location $DevDir
        while ($true) {
            Start-Sleep -Seconds $CL_INT
            python manage.py build_ml_dataset --output-json $ML_JSON --days 90 2>$null
            if (Test-Path $ML_JSON) {
                python manage.py train_failure_predictor --input-json $ML_JSON 2>$null
            }
        }
    } -ArgumentList $DevDir, $ML_JSON, $CL_INTERVAL

    Write-Host ""
    Write-Host "=============================================="
    Write-Host "  FleetPredict Pro is running"
    Write-Host "=============================================="
    Write-Host "  App:        http://127.0.0.1:8000/"
    Write-Host "  WebSocket:  ws://127.0.0.1:8000/ws/telemetry/"
    Write-Host "  Server PID: $($script:ServerProc.Id)"
    Write-Host "  Simulator:  $($script:SimProc.Id)"
    Write-Host "  Training:   $ML_JSON (continuous learning every ${CL_INTERVAL}s)"
    Write-Host ""
    Write-Host "  ML model: $ML_MODEL (reloaded on app restart after retrain)."
    Write-Host "  Press Ctrl+C to stop all."
    Write-Host "=============================================="
    Write-Host ""

    # Wait for server process (main one); when it exits we cleanup
    $script:ServerProc.WaitForExit()
} finally {
    Stop-AllProcesses
}
