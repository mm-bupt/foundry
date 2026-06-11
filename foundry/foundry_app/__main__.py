import argparse
import uvicorn
from foundry_app.config import settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Foundry Server")
    parser.add_argument("--work-dir", type=str, default=None, help="Agent working directory")
    args, remaining = parser.parse_known_args()

    if args.work_dir:
        from pathlib import Path
        settings.work_dir = Path(args.work_dir).resolve()

    uvicorn.run(
        "foundry_app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
