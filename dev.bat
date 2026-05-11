@echo off
REM Dev launcher for Windows
REM Usage: dev.bat          (starts both)
REM        dev.bat backend  (backend only)
REM        dev.bat tui      (tui only)

setlocal
set ROOT_DIR=%~dp0
set TARGET=%1
if "%TARGET%"=="" set TARGET=all

echo Dream Foundry Dev
echo.

if "%TARGET%"=="all" (
    echo Starting backend...
    start /B "" python -m uvicorn dream_foundry.main:app --host 0.0.0.0 --port 8000 --reload
)

if "%TARGET%"=="backend" (
    echo Starting backend...
    python -m uvicorn dream_foundry.main:app --host 0.0.0.0 --port 8000 --reload
    goto :eof
)

if "%TARGET%"=="all" (
    echo Waiting for backend...
    :waitloop
    timeout /t 1 /nobreak >nul 2>&1
    curl -sf http://localhost:8000/api/health >nul 2>&1
    if errorlevel 1 goto waitloop
    echo Backend ready!
)

if "%TARGET%"=="tui" (
    echo Starting TUI...
    cd /d "%ROOT_DIR%tui"
    bun install
    bun run src/index.tsx
    goto :eof
)

if "%TARGET%"=="all" (
    echo Starting TUI...
    cd /d "%ROOT_DIR%tui"
    bun install
    bun run src/index.tsx
    taskkill /F /IM python.exe >nul 2>&1
)
