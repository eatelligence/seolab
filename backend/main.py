import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import (
    ai_visibility,
    audit,
    auth as auth_router,
    backlinks,
    competitors,
    content,
    dashboard,
    gsc,
    health,
    domain,
    keywords,
    onpage,
    projects,
    rankings,
    serp,
)
from services.auth import decode_token

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("seolab")


# Endpoints exempt from JWT auth.
# - /api/health: monitoring & uptime probes
# - /api/auth/login: must be reachable to obtain a token
# - /api/gsc/oauth/callback: hit by user-agent following Google's 302 redirect
PUBLIC_API_PATHS = (
    "/api/health",
    "/api/auth/login",
    "/api/gsc/oauth/callback",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("SEOLab API starting (env=%s)", settings.environment)

    import datetime as _dt
    from sqlalchemy import select, update
    from database import AsyncSessionLocal
    from models.audit import AuditRun
    from models.user import User
    from services.auth import hash_password

    # ---- Reset orphan audit runs interrupted by previous shutdown ----
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(AuditRun)
                .where(AuditRun.status.in_(["pending", "running"]))
                .values(
                    status="failed",
                    error="Interrupted: backend restarted while audit was running",
                    completed_at=_dt.datetime.now(_dt.timezone.utc),
                )
            )
            if result.rowcount:
                log.warning("Reset %s orphan audit run(s) on startup", result.rowcount)
            await db.commit()
    except Exception as e:
        log.warning("Orphan-run cleanup failed: %s", e)

    # ---- Bootstrap initial admin user from env (only when DB has zero users) ----
    try:
        async with AsyncSessionLocal() as db:
            existing = (await db.execute(select(User).limit(1))).scalar_one_or_none()
            if existing is None:
                email = (settings.seolab_admin_email or "").strip().lower()
                pw = settings.seolab_admin_password or ""
                if email and len(pw) >= 8:
                    db.add(User(
                        email=email,
                        password_hash=hash_password(pw),
                        is_active=True,
                        is_admin=True,
                    ))
                    await db.commit()
                    log.warning("Bootstrapped admin user %s — change the password from the UI then unset SEOLAB_ADMIN_PASSWORD in .env", email)
                else:
                    log.warning(
                        "No users in DB and SEOLAB_ADMIN_EMAIL/PASSWORD not set "
                        "(or password < 8 chars). Auth will block all API access until "
                        "an admin user exists."
                    )
    except Exception as e:
        log.warning("Admin bootstrap failed: %s", e)

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


@app.middleware("http")
async def jwt_gate(request: Request, call_next):
    """Block unauthenticated /api/* requests except for the public allowlist.

    Non-API paths (the SPA bundle) are served by Nginx in the frontend
    container and never reach this middleware.
    """
    if request.method == "OPTIONS":
        return await call_next(request)
    path = request.url.path
    if not path.startswith("/api/"):
        return await call_next(request)
    if any(path.startswith(p) for p in PUBLIC_API_PATHS):
        return await call_next(request)

    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return JSONResponse(
            status_code=401,
            content={"success": False, "data": None, "error": "Not authenticated"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_token(auth[7:].strip())
    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "data": None, "error": "Invalid or expired token"},
        )
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "error": "Internal server error"},
    )


app.include_router(auth_router.router)
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
app.include_router(serp.router)
app.include_router(domain.router)
app.include_router(onpage.router)


@app.get("/")
async def root():
    return {"success": True, "data": {"service": "seolab", "version": "0.1.0"}, "error": None}
