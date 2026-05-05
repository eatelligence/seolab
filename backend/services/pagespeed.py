"""Google PageSpeed Insights v5 wrapper. Returns Core Web Vitals + score."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import httpx

from config import settings
from services.cache import cached, make_key

log = logging.getLogger(__name__)

ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


class PageSpeedError(RuntimeError):
    pass


def _audit_value(audits: dict, key: str) -> Optional[float]:
    a = audits.get(key) or {}
    return a.get("numericValue")


async def analyze(url: str, strategy: str = "mobile") -> Dict:
    """strategy: 'mobile' | 'desktop'. Returns normalised metrics dict."""
    cache_key = make_key("psi", strategy, url)

    async def fetch():
        params = {"url": url, "strategy": strategy, "category": ["performance"]}
        if settings.google_pagespeed_api_key:
            params["key"] = settings.google_pagespeed_api_key
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.get(ENDPOINT, params=params)
            if resp.status_code != 200:
                raise PageSpeedError(f"PSI {resp.status_code}: {resp.text[:200]}")
            data = resp.json()

        lh = data.get("lighthouseResult") or {}
        audits = lh.get("audits") or {}
        cats = lh.get("categories") or {}
        score = ((cats.get("performance") or {}).get("score") or 0) * 100

        # Field data (real-user, when available)
        loading = data.get("loadingExperience") or {}
        metrics = (loading.get("metrics") or {})
        def field(k):
            v = metrics.get(k) or {}
            return v.get("percentile")

        return {
            "url": url,
            "strategy": strategy,
            "performance_score": int(round(score)),
            "lab": {
                "lcp_ms": _audit_value(audits, "largest-contentful-paint"),
                "cls": _audit_value(audits, "cumulative-layout-shift"),
                "tbt_ms": _audit_value(audits, "total-blocking-time"),
                "fcp_ms": _audit_value(audits, "first-contentful-paint"),
                "si_ms": _audit_value(audits, "speed-index"),
                "tti_ms": _audit_value(audits, "interactive"),
            },
            "field": {
                "lcp_ms": field("LARGEST_CONTENTFUL_PAINT_MS"),
                "fid_ms": field("FIRST_INPUT_DELAY_MS"),
                "inp_ms": field("INTERACTION_TO_NEXT_PAINT"),
                "cls": field("CUMULATIVE_LAYOUT_SHIFT_SCORE"),
            },
            "category": loading.get("overall_category"),
        }

    return await cached(cache_key, 60 * 60 * 24, fetch)
