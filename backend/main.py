import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import (
    ai_visibility,
    audit,
    backlinks,
    competitors,
    content,
    dashboard,
    gsc,
    health,
    keywords,
    projects,
    rankings,
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("seolab")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("SEOLab API starting (env=%s)", settings.environment)
    yield
    log.info("SEOLab API shutting down")


app = FastAPI(
    title="SEOLab API",
    version="0.1.0",
    description="Open SEO analytics platform",
    lifespan=lifespan,
    default_response_class=JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "error": "Internal server error"},
    )


app.include_router(health.router)
app.include_router(projects.router)
app.include_router(keywords.router)
app.include_router(rankings.router)
app.include_router(gsc.router)
app.include_router(dashboard.router)
app.include_router(audit.router)
app.include_router(backlinks.router)
app.include_router(competitors.router)
app.include_router(content.router)
app.include_router(ai_visibility.router)


@app.get("/")
async def root():
    return {"success": True, "data": {"service": "seolab", "version": "0.1.0"}, "error": None}
