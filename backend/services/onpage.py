"""Single-URL on-page SEO check.

Fetches one page, runs all per-page SEO checks (title/meta/H1/word count/
canonical/structured data/HTTPS/redirects/images/load time), optionally
calls PageSpeed Insights for Core Web Vitals, scores 0-100. Same severity
weights as the crawler-based audit so results are directly comparable."""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config import settings
from services import pagespeed
from services.crawler import _extract  # reuse parser

log = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {"high": 5, "medium": 2, "low": 1}
THIN_CONTENT_WORDS = 300
LARGE_IMAGE_BYTES = 500 * 1024
SLOW_PAGE_MS = 3000


def _add(issues: List[dict], issue_type: str, severity: str, **details):
    issues.append({"issue_type": issue_type, "severity": severity, "details": details})


async def _fetch(url: str) -> Dict:
    headers = {"User-Agent": settings.crawler_user_agent, "Accept": "text/html,application/xhtml+xml"}
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        start = time.monotonic()
        resp = await client.get(url, follow_redirects=True)
        took_ms = int((time.monotonic() - start) * 1000)
        chain = [str(h.url) for h in resp.history]
        return {
            "status_code": resp.status_code,
            "final_url": str(resp.url),
            "redirect_chain": chain,
            "load_time_ms": took_ms,
            "content_type": resp.headers.get("content-type", "").lower(),
            "content_length": int(resp.headers.get("content-length") or 0) or len(resp.content),
            "text": resp.text if "html" in resp.headers.get("content-type", "").lower() else "",
        }


async def _measure_image(client: httpx.AsyncClient, src: str) -> Optional[int]:
    try:
        resp = await client.head(src, timeout=10.0, follow_redirects=True)
        cl = resp.headers.get("content-length")
        return int(cl) if cl and cl.isdigit() else None
    except Exception:
        return None


async def analyze_url(url: str, run_pagespeed: bool = True) -> Dict:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    fetched = await _fetch(url)
    final_url = fetched["final_url"]
    is_https = urlparse(final_url).scheme == "https"

    page = {
        "url": url,
        "final_url": final_url,
        "status_code": fetched["status_code"],
        "load_time_ms": fetched["load_time_ms"],
        "redirect_chain": fetched["redirect_chain"],
        "is_https": is_https,
        "content_length": fetched["content_length"],
    }

    issues: List[dict] = []

    # Status checks
    if fetched["status_code"] >= 500:
        _add(issues, "server_error", "high", status=fetched["status_code"])
    elif fetched["status_code"] >= 400:
        _add(issues, "client_error", "high", status=fetched["status_code"])

    if not is_https:
        _add(issues, "not_https", "high")
    if len(fetched["redirect_chain"]) >= 2:
        _add(issues, "redirect_chain", "medium",
             chain=fetched["redirect_chain"] + [final_url],
             length=len(fetched["redirect_chain"]) + 1)
    if fetched["load_time_ms"] > SLOW_PAGE_MS:
        _add(issues, "slow_page", "medium", load_time_ms=fetched["load_time_ms"])

    # HTML extraction
    extracted = {}
    images: List[dict] = []
    if "html" in fetched["content_type"] and fetched["text"]:
        host = urlparse(final_url).netloc.lower().lstrip("www.")
        extracted = _extract(final_url, fetched["text"], host)
        images = list(extracted.get("images") or [])

        # Title
        title = extracted.get("title")
        if not title:
            _add(issues, "missing_title", "high")
        elif len(title) > 60:
            _add(issues, "long_title", "low", length=len(title))
        elif len(title) < 20:
            _add(issues, "short_title", "low", length=len(title))

        # Meta description
        meta = extracted.get("meta_description")
        if not meta:
            _add(issues, "missing_meta_description", "medium")
        elif len(meta) > 160:
            _add(issues, "long_meta_description", "low", length=len(meta))

        # H1
        h1_count = extracted.get("h1_count", 0)
        if h1_count == 0:
            _add(issues, "missing_h1", "high")
        elif h1_count > 1:
            _add(issues, "multiple_h1", "medium", count=h1_count)

        # Words / canonical / structured data
        wc = extracted.get("word_count", 0)
        if wc < THIN_CONTENT_WORDS:
            _add(issues, "thin_content", "medium", words=wc)
        if not extracted.get("canonical"):
            _add(issues, "missing_canonical", "low")
        if not extracted.get("has_structured_data"):
            _add(issues, "missing_structured_data", "low")

        # Image checks (size HEAD-fetched in parallel for the first 30)
        if images:
            async with httpx.AsyncClient(headers={"User-Agent": settings.crawler_user_agent}) as client:
                import asyncio as _aio
                async def _m(img):
                    if img.get("bytes"):
                        return
                    img["bytes"] = await _measure_image(client, img["src"])
                await _aio.gather(*[_m(i) for i in images[:30]], return_exceptions=True)

            for img in images:
                if not img.get("alt"):
                    _add(issues, "image_missing_alt", "low", src=img["src"])
                if img.get("bytes") and img["bytes"] > LARGE_IMAGE_BYTES:
                    _add(issues, "large_image", "medium", src=img["src"], bytes=img["bytes"])
    else:
        _add(issues, "non_html", "high", content_type=fetched["content_type"])

    # PageSpeed
    psi = None
    if run_pagespeed and fetched["status_code"] < 400 and "html" in fetched["content_type"]:
        try:
            psi = await pagespeed.analyze(final_url, strategy="mobile")
            lab = psi.get("lab", {}) if psi else {}
            field = psi.get("field", {}) if psi else {}
            score = (psi or {}).get("performance_score")
            lcp = field.get("lcp_ms") or lab.get("lcp_ms")
            cls = field.get("cls") or lab.get("cls")
            inp = field.get("inp_ms")

            if score is not None and score < 50:
                _add(issues, "low_performance_score", "high", score=score)
            elif score is not None and score < 70:
                _add(issues, "mediocre_performance_score", "medium", score=score)
            if lcp and lcp > 2500:
                _add(issues, "cwv_lcp_fail", "high" if lcp > 4000 else "medium", lcp_ms=int(lcp))
            if cls is not None and cls > 0.1:
                _add(issues, "cwv_cls_fail", "high" if cls > 0.25 else "medium", cls=cls)
            if inp and inp > 200:
                _add(issues, "cwv_inp_fail", "high" if inp > 500 else "medium", inp_ms=int(inp))
        except Exception as e:
            log.warning("PSI failed for %s: %s", final_url, e)

    penalty = sum(SEVERITY_WEIGHTS.get(i["severity"], 1) for i in issues)
    score = max(0, int(round(100 - min(70, penalty * 4))))

    return {
        **page,
        "title": extracted.get("title"),
        "meta_description": extracted.get("meta_description"),
        "h1": extracted.get("h1") or [],
        "h1_count": extracted.get("h1_count", 0),
        "word_count": extracted.get("word_count", 0),
        "canonical": extracted.get("canonical"),
        "has_structured_data": extracted.get("has_structured_data", False),
        "links_internal_count": len(extracted.get("links_internal") or []),
        "links_external_count": len(extracted.get("links_external") or []),
        "images_total": len(images),
        "images_missing_alt": sum(1 for i in images if not i.get("alt")),
        "images_oversized": sum(1 for i in images if (i.get("bytes") or 0) > LARGE_IMAGE_BYTES),
        "issues": issues,
        "score": score,
        "pagespeed": psi,
    }
