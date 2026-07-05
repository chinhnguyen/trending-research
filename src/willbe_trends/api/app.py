from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from willbe_trends.api.routes import prompts, research, sources
from willbe_trends.config import get_settings
from willbe_trends.db.models import init_db

WEB_DIST = Path(__file__).resolve().parents[3] / "web" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Willbe Trends API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(research.router, prefix="/api")
    app.include_router(prompts.router, prefix="/api")
    app.include_router(sources.router, prefix="/api")

    if WEB_DIST.exists():
        assets_dir = WEB_DIST / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str):
            if full_path.startswith("api/"):
                return FileResponse(WEB_DIST / "index.html", status_code=404)
            candidate = WEB_DIST / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(WEB_DIST / "index.html")

    return app


app = create_app()
