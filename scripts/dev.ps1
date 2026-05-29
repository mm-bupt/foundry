#Requires -Version 7.0
<#
.SYNOPSIS
    Dream Foundry Dev Launcher (PowerShell)
.DESCRIPTION
    Starts backend and/or TUI for development.
.EXAMPLE
    ./scripts/dev.ps1          # Starts both backend and TUI
    ./scripts/dev.ps1 backend  # Backend only
    ./scripts/dev.ps1 tui      # TUI only
#>

param(
    [ValidateSet("all", "backend", "tui")]
    [string]$Target = "all"
)

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendPid = $null

function Cleanup {
    if ($BackendPid) {
        Write-Host "Stopping backend (PID $BackendPid)..." -ForegroundColor Yellow
        Stop-Process -Id $BackendPid -Force -ErrorAction SilentlyContinue
    }
}

trap { Cleanup; break }

Write-Host "Dream Foundry Dev" -ForegroundColor Cyan
Write-Host ""

if ($Target -in "all", "backend") {
    Write-Host "Starting backend..." -ForegroundColor Green
    Push-Location (Join-Path $RootDir "foundry")
    $backendProc = Start-Process -FilePath "python" `
        -ArgumentList "-m", "uvicorn", "foundry_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" `
        -PassThru -NoNewWindow
    $BackendPid = $backendProc.Id
    Pop-Location
}

if ($Target -eq "all") {
    Write-Host "Waiting for backend..." -ForegroundColor Yellow
    $retries = 0
    while ($retries -lt 30) {
        try {
            $null = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction Stop
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

if ($Target -in "all", "tui") {
    Write-Host "Starting TUI..." -ForegroundColor Green
    Push-Location (Join-Path $RootDir "tui")
    bun install
    bun run src/index.tsx
    Pop-Location
}

Cleanup
