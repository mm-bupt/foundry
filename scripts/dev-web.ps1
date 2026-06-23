#Requires -Version 7.0
<#
.SYNOPSIS
    Var Dev Launcher (PowerShell)
.DESCRIPTION
    Starts backend and/or UI for development.
.EXAMPLE
    ./scripts/dev-web.ps1         # Starts both backend and WebUI
    ./scripts/dev-web.ps1 backend # Backend only
    ./scripts/dev-web.ps1 webui   # WebUI only
#>

param(
    [ValidateSet("all", "backend", "webui")]
    [string]$Target = "all"
)

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = if (Test-Path (Join-Path $RootDir ".venv\Scripts\python.exe")) {
    Join-Path $RootDir ".venv\Scripts\python.exe"
} else {
    "python"
}
$BackendPid = $null
$WebUiPid = $null

function Cleanup {
    if ($WebUiPid) {
        Write-Host "Stopping WebUI (PID $WebUiPid)..." -ForegroundColor Yellow
        Stop-Process -Id $WebUiPid -Force -ErrorAction SilentlyContinue
    }
    if ($BackendPid) {
        Write-Host "Stopping backend (PID $BackendPid)..." -ForegroundColor Yellow
        Stop-Process -Id $BackendPid -Force -ErrorAction SilentlyContinue
    }
}

trap { Cleanup; break }

Write-Host "Var Dev (WebUI)" -ForegroundColor Cyan
Write-Host ""

if ($Target -in "all", "backend") {
    Write-Host "Starting backend..." -ForegroundColor Green
    $backendProc = Start-Process -FilePath $VenvPython `
        -ArgumentList "-m", "uvicorn", "var_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", (Join-Path $RootDir "var" "var_app") `
        -WorkingDirectory $RootDir `
        -PassThru -NoNewWindow
    $BackendPid = $backendProc.Id
}

if ($Target -eq "all") {
    Write-Host "Waiting for backend..." -ForegroundColor Yellow
    $retries = 0
    while ($retries -lt 30) {
        try {
            $null = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 10 -ErrorAction Stop
            Write-Host "Backend ready!" -ForegroundColor Green
            break
        } catch {
            Start-Sleep -Seconds 1
            $retries++
        }
    }
    if ($retries -ge 30) {
        Write-Host "Backend did not start in 30s" -ForegroundColor Red
        Cleanup
        exit 1
    }
}

if ($Target -in "all", "webui") {
    Write-Host "Starting WebUI..." -ForegroundColor Green
    Push-Location (Join-Path $RootDir "webui")
    if (!(Test-Path "node_modules")) {
        Write-Host "Installing WebUI dependencies..." -ForegroundColor Yellow
        bun install
    }
    $BunExe = (Get-Command bun.exe -CommandType Application -ErrorAction SilentlyContinue).Source
    if (-not $BunExe) { $BunExe = "$env:USERPROFILE\.bun\bin\bun.exe" }
    $webUiProc = Start-Process -FilePath $BunExe `
        -ArgumentList "run", "dev" `
        -PassThru -NoNewWindow
    $WebUiPid = $webUiProc.Id
    Write-Host "WebUI running at http://localhost:5173" -ForegroundColor Cyan
    Pop-Location

    Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Yellow
    try {
        while ($true) {
            $backendRunning = Get-Process -Id $BackendPid -ErrorAction SilentlyContinue
            if (-not $backendRunning) {
                Write-Host "Backend stopped, exiting..." -ForegroundColor Red
                break
            }
            $webUiRunning = Get-Process -Id $WebUiPid -ErrorAction SilentlyContinue
            if (-not $webUiRunning) {
                Write-Host "WebUI stopped, exiting..." -ForegroundColor Red
                break
            }
            Start-Sleep -Seconds 1
        }
    } catch {
        # Ctrl+C pressed
    }
}

Cleanup