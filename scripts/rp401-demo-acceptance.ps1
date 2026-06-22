param(
  [int]$BackendPort = 8004,
  [int]$FrontendPort = 5174
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "backend\job-platform"
$Frontend = Join-Path $Root "frontend\wechat-prototype"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$NodeScript = Join-Path $Frontend "output\playwright\manual-rp401-demo-acceptance.cjs"
$SeedScript = Join-Path $Backend "scripts\seed_rp401_demo.py"

function Test-Port {
  param([int]$Port)
  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
    if (-not $async.AsyncWaitHandle.WaitOne(500)) {
      return $false
    }
    $client.EndConnect($async)
    return $true
  } catch {
    return $false
  } finally {
    $client.Close()
  }
}

function Wait-Port {
  param(
    [int]$Port,
    [string]$Name,
    [int]$TimeoutSeconds = 30
  )
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Port $Port) {
      Write-Host "$Name is listening on 127.0.0.1:$Port"
      return
    }
    Start-Sleep -Milliseconds 500
  }
  throw "$Name did not start on 127.0.0.1:$Port within $TimeoutSeconds seconds"
}

if (-not (Test-Path $Python)) {
  throw "Python venv not found: $Python"
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw "node is required to run the browser acceptance script"
}

if (-not (Test-Port $BackendPort)) {
  Write-Host "Starting backend on 127.0.0.1:$BackendPort"
  Start-Process `
    -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$BackendPort") `
    -WorkingDirectory $Backend `
    -RedirectStandardOutput (Join-Path $Backend "manual-rp401-$BackendPort.out.log") `
    -RedirectStandardError (Join-Path $Backend "manual-rp401-$BackendPort.err.log") `
    -WindowStyle Hidden
} else {
  Write-Host "Reusing backend on 127.0.0.1:$BackendPort"
}
Wait-Port -Port $BackendPort -Name "Backend"

if (-not (Test-Port $FrontendPort)) {
  if ($FrontendPort -ne 5174) {
    throw "The existing npm dev script uses strict port 5174. Start frontend manually for custom port $FrontendPort."
  }
  Write-Host "Starting frontend on 127.0.0.1:$FrontendPort"
  Start-Process `
    -FilePath "npm.cmd" `
    -ArgumentList @("run", "dev") `
    -WorkingDirectory $Frontend `
    -RedirectStandardOutput (Join-Path $Frontend "output\playwright\rp401-vite.out.log") `
    -RedirectStandardError (Join-Path $Frontend "output\playwright\rp401-vite.err.log") `
    -WindowStyle Hidden
} else {
  Write-Host "Reusing frontend on 127.0.0.1:$FrontendPort"
}
Wait-Port -Port $FrontendPort -Name "Frontend"

Write-Host "Seeding deterministic RP401 demo data"
Push-Location $Backend
try {
  & $Python $SeedScript
  if ($LASTEXITCODE -ne 0) {
    throw "Seed script failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}

Write-Host "Running browser acceptance"
$env:API_BASE_URL = "http://127.0.0.1:$BackendPort"
$env:APP_BASE_URL = "http://127.0.0.1:$FrontendPort"
Push-Location $Root
try {
  node $NodeScript
  if ($LASTEXITCODE -ne 0) {
    throw "Browser acceptance failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}

Write-Host ""
Write-Host "RP401 demo acceptance completed."
Write-Host "Admin account: 13700137001 / Admin1234"
Write-Host "Open: http://127.0.0.1:$FrontendPort/#/admin-ra/match-quality"
Write-Host "Screenshots:"
Write-Host "  frontend\wechat-prototype\output\playwright\rp401-demo-quality-insights.png"
Write-Host "  frontend\wechat-prototype\output\playwright\rp401-demo-risk-city-filter.png"
