import os
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from willbe_trends.api.basic_auth import BasicAuthMiddleware
from willbe_trends.api.routes import briefs, prompts, research, sources
from willbe_trends.config import get_settings
from willbe_trends.db.models import init_db


def resolve_web_dist() -> Path | None:
    candidates: list[Path] = []
    if env_path := os.environ.get("WILLBE_WEB_DIST"):
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path(__file__).resolve().parents[3] / "web" / "dist",
            Path("/app/web/dist"),
            Path.cwd() / "web" / "dist",
        ]
    )
    for path in candidates:
        if path.exists():
            return path
    return None


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
    if settings.http_auth_enabled():
        app.add_middleware(
            BasicAuthMiddleware,
            username=settings.willbe_http_auth_user,
            password=settings.willbe_http_auth_password,
            exempt_paths=frozenset({"/api/health"}),
        )
    app.include_router(research.router, prefix="/api")
    app.include_router(briefs.router, prefix="/api")
    app.include_router(prompts.router, prefix="/api")
    app.include_router(sources.router, prefix="/api")

    web_dist = resolve_web_dist()
    if web_dist is not None:
        assets_dir = web_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str):
            if full_path.startswith("api/"):
                return FileResponse(web_dist / "index.html", status_code=404)
            candidate = web_dist / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(web_dist / "index.html")

    return app


app = create_app()
