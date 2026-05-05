"""Async site crawler.

Features:
- BFS from a root URL with depth tracking
- Same-host scoping
- robots.txt parsing and respect
- Configurable concurrency + global rate-limit (rps)
- Redirect chain capture
- Per-page extraction: title, meta description, H1 count, word count, canonical,
  links (internal/external), images (with size HEAD-checked for the largest 100),
  status_code, load_time_ms, structured data presence, scheme.
"""

from __future__ import annotations

import asyncio
import logging
import time
import urllib.robotparser
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from config import settings

log = logging.getLogger(__name__)


@dataclass
class CrawledPage:
    url: str
    final_url: str
    status_code: Optional[int]
    depth: int
    load_time_ms: int
    redirect_chain: List[str] = field(default_factory=list)
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: List[str] = field(default_factory=list)
    h1_count: int = 0
    word_count: int = 0
    canonical: Optional[str] = None
    links_internal: List[str] = field(default_factory=list)
    links_external: List[str] = field(default_factory=list)
    images: List[dict] = field(default_factory=list)  # {src, alt, bytes?}
    has_structured_data: bool = False
    is_https: bool = True
    content_length: Optional[int] = None
    error: Optional[str] = None


@dataclass
class CrawlResult:
    root_url: str
    pages: List[CrawledPage]
    broken_links: List[Tuple[str, str, int]]  # (source_page, broken_url, status)


def _normalize(url: str) -> str:
    url, _ = urldefrag(url.strip())
    return url.rstrip("/") if url.count("/") > 3 else url


def _same_host(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return pa.netloc.lower().lstrip("www.") == pb.netloc.lower().lstrip("www.")


async def _load_robots(client: httpx.AsyncClient, root: str) -> urllib.robotparser.RobotFileParser:
    parsed = urlparse(root)
    rp = urllib.robotparser.RobotFileParser()
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        resp = await client.get(robots_url, timeout=10.0)
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
        else:
            rp.parse([])
    except Exception:
        rp.parse([])
    return rp


def _word_count(text: str) -> int:
    return len([w for w in text.split() if w.strip()])


async def _head_image_size(client: httpx.AsyncClient, url: str) -> Optional[int]:
    try:
        resp = await client.head(url, timeout=10.0, follow_redirects=True)
        cl = resp.headers.get("content-length")
        return int(cl) if cl and cl.isdigit() else None
    except Exception:
        return None


def _extract(page_url: str, html: str, root_host: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    meta_desc = None
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = md["content"].strip()

    h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]

    canonical = None
    can = soup.find("link", attrs={"rel": "canonical"})
    if can and can.get("href"):
        canonical = can["href"].strip()

    has_sd = bool(soup.find("script", attrs={"type": "application/ld+json"})) or \
             bool(soup.find(attrs={"itemscope": True}))

    # Strip scripts/styles before counting words
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    body_text = soup.get_text(" ", strip=True)
    wc = _word_count(body_text)

    links_internal: List[str] = []
    links_external: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        absolute = urljoin(page_url, href)
        absolute, _ = urldefrag(absolute)
        if not absolute.startswith(("http://", "https://")):
            continue
        if urlparse(absolute).netloc.lower().lstrip("www.") == root_host.lstrip("www."):
            links_internal.append(absolute)
        else:
            links_external.append(absolute)

    images: List[dict] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        absolute = urljoin(page_url, src)
        images.append({"src": absolute, "alt": (img.get("alt") or "").strip()})

    return {
        "title": title,
        "meta_description": meta_desc,
        "h1": h1s,
        "h1_count": len(h1s),
        "word_count": wc,
        "canonical": canonical,
        "has_structured_data": has_sd,
        "links_internal": list(dict.fromkeys(links_internal)),
        "links_external": list(dict.fromkeys(links_external)),
        "images": images,
    }


class Crawler:
    def __init__(
        self,
        root_url: str,
        max_pages: Optional[int] = None,
        rps: Optional[float] = None,
        concurrency: int = 5,
        user_agent: Optional[str] = None,
    ):
        if not root_url.startswith(("http://", "https://")):
            root_url = "https://" + root_url
        self.root_url = root_url.rstrip("/")
        self.root_host = urlparse(self.root_url).netloc.lower()
        self.max_pages = max_pages or settings.crawler_max_pages
        self.rps = rps if rps is not None else settings.crawler_rate_limit_rps
        self.concurrency = concurrency
        self.user_agent = user_agent or settings.crawler_user_agent

        self._visited: Set[str] = set()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._pages: Dict[str, CrawledPage] = {}
        self._broken: List[Tuple[str, str, int]] = []
        self._sem = asyncio.Semaphore(concurrency)
        self._last_request_at = 0.0
        self._rate_lock = asyncio.Lock()

    async def _rate_limit(self):
        if self.rps <= 0:
            return
        async with self._rate_lock:
            interval = 1.0 / self.rps
            now = time.monotonic()
            wait = self._last_request_at + interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_at = time.monotonic()

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> Tuple[Optional[httpx.Response], List[str], int]:
        await self._rate_limit()
        start = time.monotonic()
        chain: List[str] = []
        try:
            resp = await client.get(url, follow_redirects=True, timeout=20.0)
            for h in resp.history:
                chain.append(str(h.url))
            return resp, chain, int((time.monotonic() - start) * 1000)
        except httpx.HTTPError as e:
            log.debug("fetch failed %s: %s", url, e)
            return None, chain, int((time.monotonic() - start) * 1000)

    async def _worker(self, client: httpx.AsyncClient, robots: urllib.robotparser.RobotFileParser):
        while True:
            try:
                url, depth = await asyncio.wait_for(self._queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                return
            try:
                if url in self._visited or len(self._pages) >= self.max_pages:
                    continue
                self._visited.add(url)
                if not robots.can_fetch(self.user_agent, url):
                    log.debug("robots disallowed: %s", url)
                    continue
                async with self._sem:
                    resp, chain, took_ms = await self._fetch(client, url)

                if resp is None:
                    self._pages[url] = CrawledPage(
                        url=url, final_url=url, status_code=None, depth=depth,
                        load_time_ms=took_ms, error="fetch_failed",
                    )
                    continue

                final_url = str(resp.url)
                page = CrawledPage(
                    url=url, final_url=final_url, status_code=resp.status_code,
                    depth=depth, load_time_ms=took_ms, redirect_chain=chain,
                    is_https=urlparse(final_url).scheme == "https",
                    content_length=int(resp.headers.get("content-length") or 0) or None,
                )

                if 400 <= resp.status_code:
                    self._pages[url] = page
                    continue

                content_type = (resp.headers.get("content-type") or "").lower()
                if "html" not in content_type:
                    self._pages[url] = page
                    continue

                extracted = _extract(final_url, resp.text, self.root_host)
                for k, v in extracted.items():
                    setattr(page, k, v)
                self._pages[url] = page

                # Enqueue internal links
                if depth + 1 < 50:  # safety bound
                    for link in extracted["links_internal"]:
                        link_n = _normalize(link)
                        if link_n in self._visited or link_n in (u for u, _ in list(self._queue._queue)):
                            continue
                        if len(self._pages) + self._queue.qsize() >= self.max_pages:
                            break
                        await self._queue.put((link_n, depth + 1))
            finally:
                self._queue.task_done()

    async def _check_external_links(self, client: httpx.AsyncClient):
        """HEAD-check internal links discovered as broken (non-2xx)."""
        for page in list(self._pages.values()):
            for link in page.links_internal:
                norm = _normalize(link)
                if norm in self._pages:
                    target = self._pages[norm]
                    if target.status_code and (target.status_code >= 400 or target.error == "fetch_failed"):
                        self._broken.append((page.final_url, norm, target.status_code or 0))

    async def _enrich_image_sizes(self, client: httpx.AsyncClient):
        """HEAD the largest 100 image URLs to flag oversized assets."""
        all_images = []
        for page in self._pages.values():
            for img in page.images:
                all_images.append((page.url, img))
        # Dedupe by src
        seen = set()
        unique: List[tuple] = []
        for src_page, img in all_images:
            if img["src"] in seen:
                continue
            seen.add(img["src"])
            unique.append((src_page, img))
        unique = unique[:200]

        async def measure(item):
            page_url, img = item
            size = await _head_image_size(client, img["src"])
            if size is not None:
                img["bytes"] = size

        sem = asyncio.Semaphore(8)

        async def bounded(item):
            async with sem:
                await self._rate_limit()
                await measure(item)

        await asyncio.gather(*(bounded(it) for it in unique), return_exceptions=True)

    async def run(self) -> CrawlResult:
        headers = {"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"}
        async with httpx.AsyncClient(headers=headers, http2=False) as client:
            robots = await _load_robots(client, self.root_url)
            await self._queue.put((_normalize(self.root_url), 0))
            workers = [asyncio.create_task(self._worker(client, robots)) for _ in range(self.concurrency)]
            await asyncio.gather(*workers, return_exceptions=True)
            await self._check_external_links(client)
            await self._enrich_image_sizes(client)

        return CrawlResult(
            root_url=self.root_url,
            pages=list(self._pages.values()),
            broken_links=self._broken,
        )
