#Requires -Version 7.0
<#
.SYNOPSIS
    Foundry Dev Launcher (PowerShell)
.DESCRIPTION
    Starts backend and/or UI for development.
.EXAMPLE
    ./scripts/dev.ps1          # Starts both backend and WebUI
    ./scripts/dev.ps1 backend  # Backend only
    ./scripts/dev.ps1 webui    # WebUI only
    ./scripts/dev.ps1 tui      # TUI only
#>

param(
    [ValidateSet("all", "backend", "webui", "tui")]
    [string]$Target = "all"
)

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendPid = $null
$WebUiPid = $null
$TuiPid = $null

function Cleanup {
    if ($TuiPid) {
        Write-Host "Stopping TUI (PID $TuiPid)..." -ForegroundColor Yellow
        Stop-Process -Id $TuiPid -Force -ErrorAction SilentlyContinue
    }
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

Write-Host "Foundry Dev" -ForegroundColor Cyan
Write-Host ""

if ($Target -in "all", "backend") {
    Write-Host "Starting backend..." -ForegroundColor Green
    $backendProc = Start-Process -FilePath "python" `
        -ArgumentList "-m", "uvicorn", "foundry_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", (Join-Path $RootDir "foundry" "foundry_app") `
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
        npm install
    }
    $webUiProc = Start-Process -FilePath "npm" `
        -ArgumentList "run", "dev" `
        -PassThru -NoNewWindow
    $WebUiPid = $webUiProc.Id
    Write-Host "WebUI running at http://localhost:5173" -ForegroundColor Cyan
    Pop-Location
    
    # Keep script running to manage both processes
    Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Yellow
    try {
        while ($true) {
            # Check if backend is still running
            $backendRunning = Get-Process -Id $BackendPid -ErrorAction SilentlyContinue
            if (-not $backendRunning) {
                Write-Host "Backend stopped, exiting..." -ForegroundColor Red
                break
            }
            # Check if webui is still running
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

if ($Target -eq "tui") {
    Write-Host "Starting TUI..." -ForegroundColor Green
    Push-Location (Join-Path $RootDir "tui")
    bun install
    bun run src/index.tsx
    Pop-Location
}

Cleanup
