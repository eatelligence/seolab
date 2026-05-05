"""Fetch a page and extract its main text content (used by content optimizer)."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from config import settings

log = logging.getLogger(__name__)


async def fetch_text(url: str, max_chars: int = 12000) -> Tuple[str, Optional[str], Optional[str]]:
    """Returns (visible_text, title, meta_description)."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    async with httpx.AsyncClient(headers={"User-Agent": settings.crawler_user_agent}, timeout=20.0) as client:
        resp = await client.get(url, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    md = soup.find("meta", attrs={"name": "description"})
    meta = md["content"].strip() if md and md.get("content") else None

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(" ", strip=True)
    if len(text) > max_chars:
        text = text[:max_chars]
    return text, title, meta
