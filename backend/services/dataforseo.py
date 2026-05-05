"""DataForSEO API v3 wrapper.

All methods cache results in Redis for 24h by default to minimise costs. The
client uses HTTP Basic auth and httpx async. Errors raise ``DataForSEOError``
with a normalised message.
"""

from __future__ import annotations

import base64
import logging
import re
from typing import Any, Dict, Iterable, List, Optional

import httpx
from tenacity import AsyncRetrying, RetryError, stop_after_attempt, wait_exponential

from config import settings
from services.cache import cached, make_key
from services.locations import language_code, location_code

log = logging.getLogger(__name__)

BASE_URL = "https://api.dataforseo.com/v3"
DEFAULT_TTL = 60 * 60 * 24  # 24h


class DataForSEOError(RuntimeError):
    pass


def _auth_header() -> Dict[str, str]:
    if not settings.dataforseo_login or not settings.dataforseo_password:
        raise DataForSEOError("DATAFORSEO_LOGIN/PASSWORD not configured")
    token = base64.b64encode(
        f"{settings.dataforseo_login}:{settings.dataforseo_password}".encode()
    ).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


async def _post(path: str, body: list) -> dict:
    """Low-level POST with retry. Returns the first task result envelope."""

    async def _do() -> dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{BASE_URL}{path}", headers=_auth_header(), json=body)
            if resp.status_code >= 500:
                raise DataForSEOError(f"DataForSEO {resp.status_code}: {resp.text[:200]}")
            data = resp.json()
            if data.get("status_code") not in (20000, 20100):
                raise DataForSEOError(
                    f"DataForSEO error {data.get('status_code')}: {data.get('status_message')}"
                )
            return data

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=True,
        ):
            with attempt:
                return await _do()
    except RetryError as e:
        raise DataForSEOError(str(e)) from e
    raise DataForSEOError("unreachable")


def _first_result(envelope: dict) -> Optional[dict]:
    tasks = envelope.get("tasks") or []
    if not tasks:
        return None
    task = tasks[0]
    if task.get("status_code") not in (20000, 20100):
        raise DataForSEOError(f"task error: {task.get('status_message')}")
    results = task.get("result") or []
    return results[0] if results else None


def _items(envelope: dict) -> List[dict]:
    res = _first_result(envelope)
    if not res:
        return []
    return res.get("items") or []


# ---------------- Keywords Explorer ----------------

async def keyword_overview(keywords: List[str], country: str = "US") -> List[dict]:
    keywords = [k.strip().lower() for k in keywords if k.strip()][:1000]
    if not keywords:
        return []
    key = make_key("dfs", "kw_overview", country, *sorted(keywords))
    body = [{
        "keywords": keywords,
        "location_code": location_code(country),
        "language_code": language_code(country),
    }]
    async def fetch():
        env = await _post("/dataforseo_labs/google/keyword_overview/live", body)
        return _items(env)
    return await cached(key, DEFAULT_TTL, fetch)


async def related_keywords(keyword: str, country: str = "US", limit: int = 100) -> List[dict]:
    key = make_key("dfs", "related", country, keyword.lower(), limit)
    body = [{
        "keyword": keyword.lower(),
        "location_code": location_code(country),
        "language_code": language_code(country),
        "limit": limit,
        "depth": 2,
    }]
    async def fetch():
        env = await _post("/dataforseo_labs/google/related_keywords/live", body)
        items = _items(env)
        out = []
        for it in items:
            kd = it.get("keyword_data") or {}
            info = kd.get("keyword_info") or {}
            out.append({
                "keyword": kd.get("keyword"),
                "search_volume": info.get("search_volume"),
                "cpc": info.get("cpc"),
                "competition": info.get("competition_level"),
                "difficulty": (kd.get("keyword_properties") or {}).get("keyword_difficulty"),
                "monthly_searches": info.get("monthly_searches") or [],
            })
        return out
    return await cached(key, DEFAULT_TTL, fetch)


async def keyword_suggestions(keyword: str, country: str = "US", limit: int = 100) -> List[dict]:
    key = make_key("dfs", "suggestions", country, keyword.lower(), limit)
    body = [{
        "keyword": keyword.lower(),
        "location_code": location_code(country),
        "language_code": language_code(country),
        "limit": limit,
    }]
    async def fetch():
        env = await _post("/dataforseo_labs/google/keyword_suggestions/live", body)
        items = _items(env)
        out = []
        for it in items:
            info = (it.get("keyword_info") or {})
            props = (it.get("keyword_properties") or {})
            out.append({
                "keyword": it.get("keyword"),
                "search_volume": info.get("search_volume"),
                "cpc": info.get("cpc"),
                "competition": info.get("competition_level"),
                "difficulty": props.get("keyword_difficulty"),
                "intent": (it.get("search_intent_info") or {}).get("main_intent"),
                "monthly_searches": info.get("monthly_searches") or [],
            })
        return out
    return await cached(key, DEFAULT_TTL, fetch)


_QUESTION_RE = re.compile(
    r"^(who|what|where|when|why|how|which|is|are|can|could|do|does|should|would|will)\b",
    re.IGNORECASE,
)


async def keyword_questions(keyword: str, country: str = "US", limit: int = 100) -> List[dict]:
    """Question variants — fetches keyword_ideas then filters question-pattern terms client-side.

    DataForSEO's keyword_ideas endpoint doesn't expose the filters API used on
    other Labs endpoints, so we over-fetch and prune locally.
    """
    key = make_key("dfs", "questions", country, keyword.lower(), limit)
    body = [{
        "keywords": [keyword.lower()],
        "location_code": location_code(country),
        "language_code": language_code(country),
        "limit": min(limit * 6, 1000),
    }]

    async def fetch():
        env = await _post("/dataforseo_labs/google/keyword_ideas/live", body)
        items = _items(env)
        out: List[dict] = []
        for it in items:
            kw = (it.get("keyword") or "").strip()
            if not kw or not _QUESTION_RE.match(kw):
                continue
            info = it.get("keyword_info") or {}
            out.append({
                "keyword": kw,
                "search_volume": info.get("search_volume"),
                "cpc": info.get("cpc"),
            })
            if len(out) >= limit:
                break
        return out

    return await cached(key, DEFAULT_TTL, fetch)


# ---------------- SERP / Rank checking ----------------

async def serp_organic(keyword: str, country: str = "US", target_domain: Optional[str] = None) -> dict:
    """Returns first SERP page items + (if target_domain set) position of that domain."""
    key = make_key("dfs", "serp", country, keyword.lower(), target_domain or "")
    body = [{
        "keyword": keyword.lower(),
        "location_code": location_code(country),
        "language_code": language_code(country),
        "device": "desktop",
        "depth": 100,
    }]
    async def fetch():
        env = await _post("/serp/google/organic/live/regular", body)
        res = _first_result(env)
        items = (res or {}).get("items") or []
        organic = [it for it in items if it.get("type") == "organic"]
        features = sorted({it.get("type") for it in items if it.get("type") and it.get("type") != "organic"})
        position = None
        url = None
        if target_domain:
            td = target_domain.lower().lstrip(".")
            for it in organic:
                domain = (it.get("domain") or "").lower()
                if domain == td or domain.endswith("." + td):
                    position = it.get("rank_absolute") or it.get("rank_group")
                    url = it.get("url")
                    break
        return {
            "keyword": keyword,
            "country": country,
            "items": organic[:20],
            "serp_features": features,
            "target_position": position,
            "target_url": url,
            "checked_at": (res or {}).get("datetime"),
        }
    # SERP cache: 6h (rankings change faster than search volume)
    return await cached(key, 60 * 60 * 6, fetch)


# ---------------- Backlinks ----------------

async def backlinks_summary(target: str) -> dict:
    key = make_key("dfs", "bl_summary", target)
    body = [{"target": target, "internal_list_limit": 10, "backlinks_status_type": "live"}]
    async def fetch():
        env = await _post("/backlinks/summary/live", body)
        return _first_result(env) or {}
    return await cached(key, DEFAULT_TTL, fetch)


async def backlinks_list(target: str, limit: int = 100, mode: str = "as_is") -> List[dict]:
    key = make_key("dfs", "bl_list", target, limit, mode)
    body = [{
        "target": target, "limit": limit, "mode": mode,
        "backlinks_status_type": "live",
        "include_subdomains": True,
    }]
    async def fetch():
        env = await _post("/backlinks/backlinks/live", body)
        return _items(env)
    return await cached(key, DEFAULT_TTL, fetch)


async def referring_domains(target: str, limit: int = 100) -> List[dict]:
    key = make_key("dfs", "refdomains", target, limit)
    body = [{"target": target, "limit": limit, "backlinks_status_type": "live"}]
    async def fetch():
        env = await _post("/backlinks/referring_domains/live", body)
        return _items(env)
    return await cached(key, DEFAULT_TTL, fetch)


async def anchor_distribution(target: str, limit: int = 100) -> List[dict]:
    key = make_key("dfs", "anchors", target, limit)
    body = [{"target": target, "limit": limit, "backlinks_status_type": "live"}]
    async def fetch():
        env = await _post("/backlinks/anchors/live", body)
        return _items(env)
    return await cached(key, DEFAULT_TTL, fetch)


# ---------------- Competitors / Domain analytics ----------------

async def domain_overview(target: str, country: str = "US") -> dict:
    key = make_key("dfs", "domain_overview", country, target)
    body = [{
        "target": target,
        "location_code": location_code(country),
        "language_code": language_code(country),
    }]
    async def fetch():
        env = await _post("/dataforseo_labs/google/domain_rank_overview/live", body)
        items = _items(env)
        return items[0] if items else {}
    return await cached(key, DEFAULT_TTL, fetch)


async def organic_competitors(target: str, country: str = "US", limit: int = 20) -> List[dict]:
    key = make_key("dfs", "competitors", country, target, limit)
    body = [{
        "target": target,
        "location_code": location_code(country),
        "language_code": language_code(country),
        "limit": limit,
    }]
    async def fetch():
        env = await _post("/dataforseo_labs/google/competitors_domain/live", body)
        return _items(env)
    return await cached(key, DEFAULT_TTL, fetch)


async def keyword_gap(target: str, competitors: Iterable[str], country: str = "US", limit: int = 200) -> List[dict]:
    """Keywords competitors rank for that target does not."""
    competitors = [c for c in competitors if c]
    if not competitors:
        return []
    key = make_key("dfs", "kw_gap", country, target, *sorted(competitors), limit)
    body = [{
        "target1": competitors[0],
        "target2": target,
        "location_code": location_code(country),
        "language_code": language_code(country),
        "limit": limit,
        "intersections": False,
    }]
    async def fetch():
        env = await _post("/dataforseo_labs/google/domain_intersection/live", body)
        return _items(env)
    return await cached(key, DEFAULT_TTL, fetch)


async def top_pages(target: str, country: str = "US", limit: int = 100) -> List[dict]:
    key = make_key("dfs", "top_pages", country, target, limit)
    body = [{
        "target": target,
        "location_code": location_code(country),
        "language_code": language_code(country),
        "limit": limit,
    }]
    async def fetch():
        env = await _post("/dataforseo_labs/google/relevant_pages/live", body)
        return _items(env)
    return await cached(key, DEFAULT_TTL, fetch)
