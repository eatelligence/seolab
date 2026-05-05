"""Google Suggest async recursive expansion (free).

Uses the Firefox-style endpoint that returns plain JSON arrays.
"""

from __future__ import annotations

import asyncio
import logging
import string
from typing import Iterable, List, Set

import httpx

from services.cache import cached, make_key
from services.locations import language_code

log = logging.getLogger(__name__)

ENDPOINT = "https://suggestqueries.google.com/complete/search"
ALPHABET = list(string.ascii_lowercase) + [str(d) for d in range(10)]


async def _suggest_one(client: httpx.AsyncClient, query: str, hl: str, gl: str) -> List[str]:
    try:
        resp = await client.get(
            ENDPOINT,
            params={"client": "firefox", "q": query, "hl": hl, "gl": gl.lower()},
            timeout=10.0,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
            return [str(s) for s in data[1]]
        return []
    except Exception as e:
        log.debug("suggest failed for %r: %s", query, e)
        return []


async def expand(
    seed: str,
    country: str = "US",
    levels: int = 3,
    alphabet_breadth: bool = True,
    max_results: int = 500,
) -> List[str]:
    """Recursive Google Suggest expansion.

    - level 1: seed → suggestions and (if alphabet_breadth) "seed a", "seed b", ...
    - level 2-3: each new suggestion expanded again with rate-limit
    """
    seed = seed.strip().lower()
    if not seed:
        return []

    cache_key = make_key("suggest", country, seed, levels, alphabet_breadth, max_results)

    async def fetch():
        hl = language_code(country)
        gl = country.upper()
        seen: Set[str] = {seed}
        results: List[str] = []
        sem = asyncio.Semaphore(8)

        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0 SEOLab"}) as client:
            async def fetch_for(q: str) -> List[str]:
                async with sem:
                    base = await _suggest_one(client, q, hl, gl)
                    if alphabet_breadth:
                        # Append " a".." z" to broaden discovery (one level only).
                        async def with_letter(letter: str) -> List[str]:
                            async with sem:
                                return await _suggest_one(client, f"{q} {letter}", hl, gl)
                        more = await asyncio.gather(*(with_letter(l) for l in ALPHABET))
                        for batch in more:
                            base.extend(batch)
                    return base

            current: List[str] = [seed]
            for _ in range(levels):
                tasks = [fetch_for(q) for q in current]
                batches = await asyncio.gather(*tasks)
                next_level: List[str] = []
                for batch in batches:
                    for s in batch:
                        s_norm = s.strip().lower()
                        if s_norm and s_norm not in seen:
                            seen.add(s_norm)
                            results.append(s_norm)
                            next_level.append(s_norm)
                            if len(results) >= max_results:
                                return results
                if not next_level:
                    break
                # Cap fanout per level to avoid combinatorial explosion.
                current = next_level[:50]
                # Disable alphabet broadening past level 1 to keep request count sane.
                alphabet_breadth = False

        return results

    return await cached(cache_key, 60 * 60 * 24, fetch)
