"""Open PageRank API (https://www.domcop.com/openpagerank/)."""

from __future__ import annotations

import logging
from typing import Dict, List

import httpx

from config import settings
from services.cache import cached, make_key

log = logging.getLogger(__name__)

ENDPOINT = "https://openpagerank.com/api/v1.0/getPageRank"


class OpenPageRankError(RuntimeError):
    pass


async def domain_authority(domains: List[str]) -> Dict[str, float]:
    """Returns {domain: page_rank_decimal (0-10)}. Missing domains default to 0.0."""
    domains = [d.strip().lower() for d in domains if d and d.strip()]
    if not domains:
        return {}
    if not settings.open_pagerank_api_key:
        log.warning("OPEN_PAGERANK_API_KEY not set; returning zeros")
        return {d: 0.0 for d in domains}

    key = make_key("openpr", *sorted(domains))

    async def fetch():
        out: Dict[str, float] = {}
        # API caps at 100 domains per call
        async with httpx.AsyncClient(timeout=20.0) as client:
            for i in range(0, len(domains), 100):
                chunk = domains[i:i + 100]
                params = [("domains[]", d) for d in chunk]
                resp = await client.get(
                    ENDPOINT,
                    params=params,
                    headers={"API-OPR": settings.open_pagerank_api_key},
                )
                if resp.status_code != 200:
                    raise OpenPageRankError(f"{resp.status_code}: {resp.text[:200]}")
                data = resp.json()
                for entry in data.get("response", []) or []:
                    d = (entry.get("domain") or "").lower()
                    pr = entry.get("page_rank_decimal")
                    if d:
                        try:
                            out[d] = float(pr) if pr not in (None, "") else 0.0
                        except (TypeError, ValueError):
                            out[d] = 0.0
        for d in domains:
            out.setdefault(d, 0.0)
        return out

    return await cached(key, 60 * 60 * 24 * 7, fetch)  # weekly cache
