$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $root "logs"
$prefixes = @("backend", "frontend", "ingestion")
$jobs = @()

if (-not (Test-Path $logDir)) {
  Write-Host "No logs directory found at $logDir. Run .\run-all.ps1 first."
  exit 1
}

foreach ($prefix in $prefixes) {
  $latest = Get-ChildItem -Path $logDir -Filter "$prefix-*.log" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

  if ($null -ne $latest) {
    Write-Host "Tailing $($latest.FullName)"
    $jobs += Start-Job -ScriptBlock {
      param($path)
      Get-Content -Path $path -Tail 200 -Wait
    } -ArgumentList $latest.FullName
  } else {
    Write-Host "No logs found for $prefix."
  }
}

if ($jobs.Count -eq 0) {
  exit 1
}

Receive-Job -Job $jobs -Wait
