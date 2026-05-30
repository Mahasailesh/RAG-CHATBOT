param(
  [switch]$SkipIngestion
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvActivate = Join-Path $backend ".venv\Scripts\Activate.ps1"
$logDir = Join-Path $root "logs"

if (-not (Test-Path $logDir)) {
  New-Item -ItemType Directory -Path $logDir | Out-Null
}

function Start-Task {
  param(
    [string]$Name,
    [string]$Command
  )

  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $logPath = Join-Path $logDir "$Name-$timestamp.log"
  $wrapped = "$Command 2>&1 | Tee-Object -FilePath `"$logPath`""
  Start-Process powershell -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-NoExit","-Command", $wrapped
}

$backendCmd = "cd `"$backend`"; if (Test-Path `"$venvActivate`") { . `"$venvActivate`" }; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Task -Name "backend" -Command $backendCmd

$frontendCmd = "cd `"$frontend`"; pnpm run dev"
Start-Task -Name "frontend" -Command $frontendCmd

if (-not $SkipIngestion) {
  $ingestionCmd = "cd `"$backend\ingestion`"; if (Test-Path `"$venvActivate`") { . `"$venvActivate`" }; python ingestion_pipeline.py"
  Start-Task -Name "ingestion" -Command $ingestionCmd
}
