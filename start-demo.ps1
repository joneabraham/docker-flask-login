<#
.SYNOPSIS
    One-command spin-up for the Flask login demo.

.DESCRIPTION
    Checks Docker is running, creates .env from .env.example on first run
    (with a random SECRET_KEY), builds and starts the stack, waits for the
    /health endpoint, then opens the app in your browser.

.EXAMPLE
    ./start-demo.ps1            # start
    ./start-demo.ps1 -Down      # stop and remove containers
    ./start-demo.ps1 -Reset     # stop and wipe the database volume
#>
param(
    [switch]$Down,
    [switch]$Reset,
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

try { docker info *> $null } catch { }
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

if ($Down -or $Reset) {
    Write-Step "Stopping stack"
    if ($Reset) { docker compose down -v } else { docker compose down }
    exit $LASTEXITCODE
}

if (-not (Test-Path .env)) {
    Write-Step "Creating .env from .env.example"
    $secret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ })
    (Get-Content .env.example) -replace '^SECRET_KEY=.*', "SECRET_KEY=$secret" | Set-Content .env
}

$port = (Get-Content .env | Where-Object { $_ -match '^APP_PORT=' }) -replace 'APP_PORT=', ''
if (-not $port) { $port = 5000 }

Write-Step "Building and starting containers"
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Step "Waiting for http://localhost:$port/health"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$healthy = $false
while ((Get-Date) -lt $deadline) {
    try {
        $res = Invoke-RestMethod -Uri "http://localhost:$port/health" -TimeoutSec 3
        if ($res.status -eq 'ok') { $healthy = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
}

if (-not $healthy) {
    Write-Host "App did not become healthy in $TimeoutSeconds s. Recent logs:" -ForegroundColor Red
    docker compose logs --tail 40
    exit 1
}

Write-Host "App is up at http://localhost:$port" -ForegroundColor Green
Start-Process "http://localhost:$port"
