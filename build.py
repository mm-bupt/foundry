#!/usr/bin/env python3
"""
Dream Foundry — Build Script
Produces a self-contained dist/dream-foundry/ folder:
  dist/dream-foundry/
  ├── dream-foundry.bat (or .sh)   ← single entry point
  ├── bin/
  │   ├── dream-foundry-server.exe ← PyInstaller backend
  │   └── bun.exe                  ← bundled Bun runtime
  └── lib/
      └── tui/                     ← TUI sources + node_modules
"""

import json
import os
import shutil
import subprocess
import sys
import platform
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist" / "dream-foundry"
FOUNDRY = ROOT / "foundry"
TUI = ROOT / "tui"

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

HIDDEN_IMPORTS = [
    "foundry_app",
    "foundry_app.main",
    "foundry_app.config",
    "foundry_app.agent.core",
    "foundry_app.agent.registry",
    "foundry_app.agent.tools",
    "foundry_app.agent.memory",
    "foundry_app.agent.context",
    "foundry_app.api.sessions",
    "foundry_app.api.models",
    "foundry_app.api.ws",
    "foundry_app.api.sse",
    "foundry_app.api.memory",
    "foundry_app.db.database",
    "foundry_app.db.crud",
    "foundry_app.db.models",
    "foundry_app.shared_protocol",
    "foundry_app.schemas.session",
    "foundry_app.schemas.chat",
    "foundry_app.schemas.memory",
    "aiosqlite",
    "sqlite_vec",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
]


def run(cmd, **kwargs):
    if isinstance(cmd, list):
        display = " ".join(str(c) for c in cmd)
    else:
        display = cmd
    print(f"\033[36m> {display}\033[0m")
    subprocess.run(cmd, cwd=kwargs.get("cwd", ROOT), check=True, shell=True)


def clean():
    parent = DIST.parent
    if parent.exists():
        shutil.rmtree(parent)
    parent.mkdir(parents=True)
    print(f"Cleaned {parent}")


def find_bun_exe():
    try:
        result = subprocess.run(
            ["bun", "-e", "console.log(process.execPath)"],
            capture_output=True, encoding="utf-8", errors="replace", shell=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            path = Path(result.stdout.strip())
            if path.exists():
                return path
    except Exception:
        pass
    if IS_WINDOWS:
        candidates = [
            Path.home() / ".bun" / "bin" / "bun.exe",
            Path(os.environ.get("USERPROFILE", "")) / "AppData" / "Roaming" / "npm" / "node_modules" / "bun" / "bin" / "bun.exe",
        ]
    else:
        candidates = [
            Path.home() / ".bun" / "bin" / "bun",
            Path("/usr/local/bin/bun"),
        ]
    for c in candidates:
        if c.exists():
            return c
    print("ERROR: Cannot find bun executable. Install bun first: https://bun.sh")
    sys.exit(1)


def build_backend():
    print("\n=== [1/4] Building Python Backend (PyInstaller) ===")
    run([sys.executable, "-m", "pip", "install", "-e", str(FOUNDRY)])
    run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    bin_dir = DIST / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "dream-foundry-server",
        "--distpath", str(bin_dir),
        "--workpath", str(DIST.parent / ".build_backend"),
        "--specpath", str(DIST.parent),
        "--onefile",
        "--clean",
        "--noconfirm",
    ]
    for mod in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", mod]
    for pkg in [
        "pydantic_ai_slim", "pydantic_ai", "pydantic",
        "fastapi", "starlette", "uvicorn", "sqlmodel", "sqlalchemy",
        "pydantic_settings", "pydantic_core",
    ]:
        cmd += ["--copy-metadata", pkg]

    import sqlite_vec as _sv
    vec_dll = os.path.join(os.path.dirname(_sv.loadable_path()), "vec0.dll" if IS_WINDOWS else "vec0.so")
    if os.path.exists(vec_dll):
        cmd += ["--add-binary", f"{vec_dll}{os.pathsep}sqlite_vec"]

    cmd += ["-y", str(FOUNDRY / "foundry_app" / "__main__.py")]
    run(cmd)

    shutil.rmtree(DIST.parent / ".build_backend", ignore_errors=True)
    exe_name = "dream-foundry-server.exe" if IS_WINDOWS else "dream-foundry-server"
    exe_path = bin_dir / exe_name
    if not exe_path.exists():
        print(f"ERROR: Backend binary not found at {exe_path}")
        sys.exit(1)
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"  Backend: {exe_path} ({size_mb:.1f} MB)")


def build_tui():
    print("\n=== [2/4] Building TUI (sources + node_modules) ===")
    if not (TUI / "node_modules").exists():
        run(["bun", "install"], cwd=TUI)

    tui_dist = DIST / "lib" / "tui"
    if tui_dist.exists():
        shutil.rmtree(tui_dist)

    shutil.copytree(TUI, tui_dist, ignore=shutil.ignore_patterns("node_modules", ".git"))
    shutil.copytree(TUI / "node_modules", tui_dist / "node_modules")

    print(f"  TUI: {tui_dist} ({sum(f.stat().st_size for f in tui_dist.rglob('*') if f.is_file()) / (1024*1024):.1f} MB)")


def bundle_bun():
    print("\n=== [3/4] Bundling Bun runtime ===")
    bun_src = find_bun_exe()
    bun_name = "bun.exe" if IS_WINDOWS else "bun"
    bun_dst = DIST / "bin" / bun_name
    shutil.copy2(bun_src, bun_dst)
    if not IS_WINDOWS:
        bun_dst.chmod(0o755)
    size_mb = bun_dst.stat().st_size / (1024 * 1024)
    print(f"  Bun: {bun_dst} ({size_mb:.1f} MB)")


def build_launcher():
    print("\n=== [4/4] Building Launcher ===")
    server_name = "dream-foundry-server.exe" if IS_WINDOWS else "dream-foundry-server"
    bun_name = "bun.exe" if IS_WINDOWS else "bun"

    if IS_WINDOWS:
        launcher_path = DIST / "dream-foundry.bat"
        content = f"""@echo off
setlocal EnableDelayedExpansion
title Dream Foundry

echo Dream Foundry v0.1.0
echo.

set "ROOT=%~dp0"
set "SERVER=%ROOT%bin\\{server_name}"
set "BUN=%ROOT%bin\\{bun_name}"
set "TUI_DIR=%ROOT%lib\\tui"

if not exist "%SERVER%" (
    echo ERROR: Backend not found at %SERVER%
    pause
    exit /b 1
)

if not exist "%BUN%" (
    echo ERROR: Bun not found at %BUN%
    pause
    exit /b 1
)

echo Starting backend...
start "" /B "%SERVER%" --host 127.0.0.1 --port 8000 %*
set SERVER_PID=

:wait_server
timeout /t 1 /nobreak >nul 2>&1
curl -sf http://127.0.0.1:8000/api/health >nul 2>&1
if errorlevel 1 goto wait_server
echo Backend ready!

echo Starting TUI...
cd /d "%TUI_DIR%"
"%BUN%" run src/index.tsx
set TUI_EXIT=%errorlevel%

echo Cleaning up...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq {server_name}" /NH 2^>nul ^| findstr /i dream-foundry') do (
    taskkill /F /PID %%a >nul 2>&1
)

exit /b %TUI_EXIT%
"""
    else:
        launcher_path = DIST / "dream-foundry.sh"
        content = f"""#!/usr/bin/env bash
set -e

echo "Dream Foundry v0.1.0"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER="$SCRIPT_DIR/bin/{server_name}"
BUN="$SCRIPT_DIR/bin/{bun_name}"
TUI_DIR="$SCRIPT_DIR/lib/tui"

if [ ! -f "$SERVER" ]; then
    echo "ERROR: Backend not found at $SERVER"
    exit 1
fi

if [ ! -f "$BUN" ]; then
    echo "ERROR: Bun not found at $BUN"
    exit 1
fi

echo "Starting backend..."
"$SERVER" --host 127.0.0.1 --port 8000 "$@" &
SERVER_PID=$!

for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
        echo "Backend ready!"
        break
    fi
    sleep 1
done

echo "Starting TUI..."
(cd "$TUI_DIR" && "$BUN" run src/index.tsx)

kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
"""

    launcher_path.write_text(content, encoding="utf-8")
    if not IS_WINDOWS:
        launcher_path.chmod(0o755)
    print(f"  Launcher: {launcher_path}")


def print_summary():
    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"\n\033[32m{'='*50}")
    print(f"  Build complete!")
    print(f"  Output: {DIST}")
    print(f"  Size: {total / (1024*1024):.1f} MB")
    if IS_WINDOWS:
        print(f"  Run: dist\\dream-foundry\\dream-foundry.bat")
    else:
        print(f"  Run: ./dist/dream-foundry/dream-foundry.sh")
    print(f"{'='*50}\033[0m")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target == "clean":
        clean()
        return

    clean()

    if target in ("all", "backend"):
        build_backend()
    if target in ("all", "tui"):
        build_tui()
    if target in ("all", "bun"):
        bundle_bun()
    if target == "all":
        build_launcher()
        print_summary()


if __name__ == "__main__":
    main()
