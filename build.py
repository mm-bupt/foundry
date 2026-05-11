#!/usr/bin/env python3
"""
Dream Foundry — Build Script
Packages Python backend (PyInstaller) + Bun TUI into dist/.
"""

import os
import shutil
import subprocess
import sys
import platform
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
FOUNDRY = ROOT / "foundry"
TUI = ROOT / "tui"

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


def run(cmd, **kwargs):
    if isinstance(cmd, list):
        display = " ".join(str(c) for c in cmd)
    else:
        display = cmd
    print(f"\033[36m> {display}\033[0m")
    subprocess.run(cmd, cwd=kwargs.get("cwd", ROOT), check=True, shell=True)


def clean():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    print(f"Cleaned {DIST}")


def build_backend():
    print("\n=== Building Python Backend ===")
    run([sys.executable, "-m", "pip", "install", "-e", str(FOUNDRY)])
    run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    backend_dist = DIST / "backend"
    backend_dist.mkdir(exist_ok=True)

    run([
        sys.executable, "-m", "PyInstaller",
        "--name", "dream-foundry-server",
        "--distpath", str(backend_dist),
        "--workpath", str(DIST / ".build_backend"),
        "--specpath", str(DIST),
        "--onefile",
        "--clean",
        "--noconfirm",
        "--hidden-import", "dream_foundry",
        "--hidden-import", "dream_foundry.main",
        "--hidden-import", "dream_foundry.config",
        "--hidden-import", "dream_foundry.agent.core",
        "--hidden-import", "dream_foundry.agent.registry",
        "--hidden-import", "dream_foundry.agent.tools",
        "--hidden-import", "dream_foundry.agent.memory",
        "--hidden-import", "dream_foundry.agent.context",
        "--hidden-import", "dream_foundry.api.sessions",
        "--hidden-import", "dream_foundry.api.models",
        "--hidden-import", "dream_foundry.api.ws",
        "--hidden-import", "dream_foundry.api.sse",
        "--hidden-import", "dream_foundry.api.memory",
        "--hidden-import", "dream_foundry.db.database",
        "--hidden-import", "dream_foundry.db.crud",
        "--hidden-import", "dream_foundry.db.models",
        "--hidden-import", "dream_foundry.shared_protocol",
        "--hidden-import", "dream_foundry.schemas.session",
        "--hidden-import", "dream_foundry.schemas.chat",
        "--hidden-import", "dream_foundry.schemas.memory",
        "--hidden-import", "aiosqlite",
        "--hidden-import", "sqlite_vec",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "-y",
        str(FOUNDRY / "dream_foundry" / "__main__.py"),
    ])

    shutil.rmtree(DIST / ".build_backend", ignore_errors=True)
    exe_name = "dream-foundry-server.exe" if IS_WINDOWS else "dream-foundry-server"
    exe_path = backend_dist / exe_name
    if not exe_path.exists():
        print(f"ERROR: Backend binary not found at {exe_path}")
        sys.exit(1)
    print(f"Backend built: {exe_path}")


def build_tui():
    print("\n=== Building TUI ===")
    if not (TUI / "node_modules").exists():
        run(["bun", "install"], cwd=TUI)

    tui_dist = DIST / "tui"
    if tui_dist.exists():
        shutil.rmtree(tui_dist)

    print("Copying TUI sources...")
    shutil.copytree(TUI, tui_dist, ignore=shutil.ignore_patterns("node_modules", ".git"))
    shutil.copytree(TUI / "node_modules", tui_dist / "node_modules")

    entry_script = tui_dist / ("start.bat" if IS_WINDOWS else "start.sh")
    if IS_WINDOWS:
        entry_script.write_text(
            '@echo off\nbun run src/index.tsx %*\n',
            encoding="utf-8",
        )
    else:
        entry_script.write_text(
            '#!/usr/bin/env bash\nbun run src/index.tsx "$@"\n',
            encoding="utf-8",
        )
        entry_script.chmod(0o755)

    print(f"TUI built: {tui_dist}")
    print(f"  Run: bun run {tui_dist / 'src' / 'index.tsx'}")


def build_launcher():
    print("\n=== Building Launcher ===")
    launcher_path = DIST / ("dream-foundry" + (".bat" if IS_WINDOWS else ".sh"))
    backend_exe = "dream-foundry-server" + (".exe" if IS_WINDOWS else "")

    if IS_WINDOWS:
        content = f"""@echo off
echo Dream Foundry v0.1.0
echo.

start /B "" "%~dp0backend\\{backend_exe}" --host 127.0.0.1 --port 8000

:wait_server
timeout /t 1 /nobreak >nul 2>&1
curl -s http://127.0.0.1:8000/api/health >nul 2>&1
if errorlevel 1 goto wait_server

cd /d "%~dp0tui"
bun run src/index.tsx

for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq {backend_exe}" /NH 2^>nul ^| findstr /i dream-foundry') do (
    taskkill /F /PID %%a >nul 2>&1
)
"""
    else:
        content = f"""#!/usr/bin/env bash
set -e

echo "Dream Foundry v0.1.0"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

"$SCRIPT_DIR/backend/{backend_exe}" --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

(cd "$SCRIPT_DIR/tui" && bun run src/index.tsx)

kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
"""

    launcher_path.write_text(content, encoding="utf-8")
    if not IS_WINDOWS:
        launcher_path.chmod(0o755)
    print(f"Launcher built: {launcher_path}")


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
    if target == "all":
        build_launcher()

    print(f"\n\033[32mBuild complete! Output in {DIST}/\033[0m")
    if target == "all":
        launcher = "dream-foundry" + (".bat" if IS_WINDOWS else ".sh")
        print(f"  Run: ./{DIST.name}/{launcher}")


if __name__ == "__main__":
    main()
