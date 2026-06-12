import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from foundry_app.config import settings
from foundry_app.db.database import init_db, get_db, close_db
from foundry_app.api import sessions, models, memory
from foundry_app.api.ws import router as ws_router
from foundry_app.api.sse import router as sse_router
from foundry_app.api.compact import router as compact_router
from foundry_app.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.debug)
    db = await get_db()
    await init_db(db)
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(models.router)
app.include_router(memory.router)
app.include_router(compact_router)
app.include_router(ws_router)
app.include_router(sse_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version}


@app.get("/api/config")
async def get_config():
    return {"work_dir": str(settings.work_dir)}


_webui_dist = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "webui",
    "dist",
)
if os.path.isdir(_webui_dist):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=_webui_dist, html=True), name="webui")
