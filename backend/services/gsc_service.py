"""Google Search Console OAuth + Search Analytics queries.

OAuth flow:
  1. /api/projects/{id}/gsc/auth-url returns Google authorization URL with state=project_id
  2. user authorizes; Google redirects to /api/gsc/oauth/callback?code=...&state=...
  3. ``exchange_code`` swaps the code for tokens and stores the encrypted refresh token
     against the project. Subsequent API calls obtain fresh access tokens automatically.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from typing import Any, Dict, List, Optional

import httpx
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.gsc import GSCToken
from services.crypto import decrypt, encrypt

log = logging.getLogger(__name__)

GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
SEARCH_ANALYTICS_URL = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
SITES_LIST_URL = "https://searchconsole.googleapis.com/webmasters/v3/sites"


class GSCError(RuntimeError):
    pass


def _require_oauth_config():
    if not settings.google_client_id or not settings.google_client_secret:
        raise GSCError("GOOGLE_CLIENT_ID/SECRET not configured")


def authorization_url(project_id: uuid.UUID) -> str:
    _require_oauth_config()
    from urllib.parse import urlencode
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": " ".join(GSC_SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": str(project_id),
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_code(db: AsyncSession, project_id: uuid.UUID, code: str) -> GSCToken:
    _require_oauth_config()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if resp.status_code != 200:
            raise GSCError(f"token exchange failed: {resp.text[:300]}")
        payload = resp.json()

    refresh = payload.get("refresh_token")
    if not refresh:
        raise GSCError("Google did not return a refresh_token (use prompt=consent)")
    access = payload.get("access_token")
    expires_in = payload.get("expires_in", 0)
    expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=int(expires_in)) if expires_in else None

    result = await db.execute(select(GSCToken).where(GSCToken.project_id == project_id))
    token = result.scalar_one_or_none()
    if token is None:
        token = GSCToken(project_id=project_id, refresh_token=encrypt(refresh))
        db.add(token)
    else:
        token.refresh_token = encrypt(refresh)
    token.access_token = encrypt(access) if access else None
    token.access_token_expires_at = expires_at
    token.scope = payload.get("scope")
    await db.commit()
    await db.refresh(token)
    return token


async def _credentials(db: AsyncSession, project_id: uuid.UUID) -> Credentials:
    result = await db.execute(select(GSCToken).where(GSCToken.project_id == project_id))
    token = result.scalar_one_or_none()
    if not token:
        raise GSCError("Google Search Console not connected for this project")

    refresh = decrypt(token.refresh_token)
    access = decrypt(token.access_token) if token.access_token else None

    creds = Credentials(
        token=access,
        refresh_token=refresh,
        token_uri=TOKEN_URL,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=GSC_SCOPES,
        expiry=token.access_token_expires_at.replace(tzinfo=None) if token.access_token_expires_at else None,
    )
    if not creds.valid:
        creds.refresh(GoogleRequest())
        token.access_token = encrypt(creds.token)
        token.access_token_expires_at = (
            creds.expiry.replace(tzinfo=dt.timezone.utc) if creds.expiry else None
        )
        await db.commit()
    return creds


async def _api_get(creds: Credentials, url: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {creds.token}"})
        if resp.status_code != 200:
            raise GSCError(f"GSC GET {url} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()


async def _api_post(creds: Credentials, url: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
            json=body,
        )
        if resp.status_code != 200:
            raise GSCError(f"GSC POST {url} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()


async def list_properties(db: AsyncSession, project_id: uuid.UUID) -> List[Dict[str, Any]]:
    creds = await _credentials(db, project_id)
    data = await _api_get(creds, SITES_LIST_URL)
    return data.get("siteEntry") or []


async def search_analytics(
    db: AsyncSession,
    project_id: uuid.UUID,
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: Optional[List[str]] = None,
    row_limit: int = 1000,
    filters: Optional[List[dict]] = None,
) -> List[Dict[str, Any]]:
    creds = await _credentials(db, project_id)
    body: Dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "rowLimit": min(row_limit, 25000),
    }
    if dimensions:
        body["dimensions"] = dimensions
    if filters:
        body["dimensionFilterGroups"] = [{"filters": filters}]
    from urllib.parse import quote
    url = SEARCH_ANALYTICS_URL.format(site=quote(site_url, safe=""))
    data = await _api_post(creds, url, body)
    return data.get("rows") or []


async def performance_summary(db: AsyncSession, project_id: uuid.UUID, site_url: str, days: int = 90) -> dict:
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    rows = await search_analytics(
        db, project_id, site_url,
        start.isoformat(), end.isoformat(),
        dimensions=["date"], row_limit=days + 1,
    )
    series = [
        {
            "date": r["keys"][0],
            "clicks": int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr": float(r.get("ctr", 0)),
            "position": float(r.get("position", 0)),
        }
        for r in rows
    ]
    series.sort(key=lambda x: x["date"])
    totals = {
        "clicks": sum(s["clicks"] for s in series),
        "impressions": sum(s["impressions"] for s in series),
        "avg_ctr": (sum(s["ctr"] for s in series) / len(series)) if series else 0,
        "avg_position": (sum(s["position"] for s in series) / len(series)) if series else 0,
    }
    return {"series": series, "totals": totals, "days": days}


async def top_keywords(db: AsyncSession, project_id: uuid.UUID, site_url: str, days: int = 28, limit: int = 100):
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    rows = await search_analytics(
        db, project_id, site_url, start.isoformat(), end.isoformat(),
        dimensions=["query"], row_limit=limit,
    )
    return [
        {
            "keyword": r["keys"][0],
            "clicks": int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr": float(r.get("ctr", 0)),
            "position": float(r.get("position", 0)),
        }
        for r in rows
    ]


async def top_pages(db: AsyncSession, project_id: uuid.UUID, site_url: str, days: int = 28, limit: int = 50):
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    rows = await search_analytics(
        db, project_id, site_url, start.isoformat(), end.isoformat(),
        dimensions=["page"], row_limit=limit,
    )
    return [
        {
            "page": r["keys"][0],
            "clicks": int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr": float(r.get("ctr", 0)),
            "position": float(r.get("position", 0)),
        }
        for r in rows
    ]
