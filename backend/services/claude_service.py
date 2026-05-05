"""Anthropic Claude wrapper for SEO content tools and AI visibility checks."""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, List, Optional

from anthropic import AsyncAnthropic

from config import settings

log = logging.getLogger(__name__)


class ClaudeError(RuntimeError):
    pass


def _client() -> AsyncAnthropic:
    if not settings.anthropic_api_key:
        raise ClaudeError("ANTHROPIC_API_KEY not configured")
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


async def _complete(system: str, user: str, max_tokens: int = 2048) -> str:
    client = _client()
    msg = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts = []
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def _extract_json(text: str) -> dict | list:
    """Pull the first JSON object/array out of a model response."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if fence:
        return json.loads(fence.group(1))
    obj = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if obj:
        return json.loads(obj.group(1))
    raise ClaudeError(f"no JSON found in model output: {text[:200]}")


# ---------------- Content tools ----------------

async def generate_seo_brief(keyword: str, country: str = "US", search_intent: str = "informational") -> dict:
    system = (
        "You are an expert SEO content strategist. Output ONLY valid JSON, no prose. "
        "Brief should be actionable and specific."
    )
    user = f"""Generate a complete SEO content brief for the target keyword: "{keyword}"
Country: {country}
Search intent: {search_intent}

Return JSON with exactly these keys:
- title (60 chars max, includes the keyword)
- meta_description (155 chars max, compelling, includes keyword)
- recommended_word_count (integer)
- target_audience (string)
- search_intent (string)
- h_structure (array of objects: {{"level": "H1"|"H2"|"H3", "text": "..."}})
- topics_to_cover (array of strings, 8-12 items)
- lsi_keywords (array of strings, 10-15 related terms)
- questions_to_answer (array of strings, 5-8 PAA-style)
- internal_link_suggestions (array of strings, page topics to link to)
- external_authoritative_sources (array of strings, types of sources to cite)
- featured_snippet_target (string, suggested format: paragraph|list|table)
"""
    return _extract_json(await _complete(system, user, max_tokens=3000))


async def optimize_content(content: str, target_keyword: str) -> dict:
    system = (
        "You are an SEO editor. Score and critique content. Output ONLY valid JSON."
    )
    user = f"""Analyze this content for SEO optimization against the target keyword "{target_keyword}".

CONTENT:
\"\"\"{content[:8000]}\"\"\"

Return JSON with:
- overall_score (0-100)
- keyword_density_pct (number)
- keyword_in_title (bool)
- keyword_in_first_100_words (bool)
- readability_score (0-100)
- word_count (integer)
- heading_structure_ok (bool)
- issues (array of {{"severity": "high"|"medium"|"low", "issue": "...", "fix": "..."}})
- suggested_title (string)
- suggested_meta_description (string)
- missing_topics (array of strings)
- semantic_keywords_to_add (array of strings)
"""
    return _extract_json(await _complete(system, user, max_tokens=3000))


async def generate_meta(content: str, n_variants: int = 5) -> dict:
    system = "You craft compelling, click-worthy SEO titles and meta descriptions. Output ONLY JSON."
    user = f"""Read this page content and produce {n_variants} optimized title/meta variants.

CONTENT:
\"\"\"{content[:6000]}\"\"\"

Return JSON:
{{
  "primary_topic": "...",
  "variants": [
    {{"title": "≤60 chars", "meta_description": "≤155 chars", "tone": "informative|persuasive|urgent|...", "estimated_ctr_lift": "low|medium|high"}}
  ]
}}
"""
    return _extract_json(await _complete(system, user, max_tokens=2000))


async def generate_content_calendar(niche: str, goals: str, days: int = 30) -> dict:
    system = "You are a content marketing strategist. Output ONLY JSON."
    user = f"""Create a {days}-day SEO content calendar for the niche "{niche}".
Goals: {goals}

Return JSON:
{{
  "niche": "{niche}",
  "summary": "2-sentence strategy",
  "items": [
    {{"day": 1, "title": "...", "primary_keyword": "...", "format": "blog|video|guide|comparison|how-to|listicle", "search_intent": "...", "word_count": 1500, "outline": ["section1", "section2"], "ctas": ["..."]}}
  ]
}}
Generate exactly {days} items."""
    return _extract_json(await _complete(system, user, max_tokens=8000))


# ---------------- AI Visibility ----------------

async def ai_response(query: str) -> str:
    """Run a user-style query against Claude, returning the raw text response.

    This is what AI Visibility Tracker uses to detect brand mentions.
    """
    system = (
        "You are a helpful AI assistant. Answer the user's question naturally and "
        "concisely as you would in a chat interface. Mention specific tools, "
        "products, or websites when they are genuinely the best answer."
    )
    return await _complete(system, query, max_tokens=1500)


async def analyze_mention(response_text: str, brand: str, competitors: List[str]) -> dict:
    """Detect brand mention, position, sentiment in an AI response."""
    system = "You analyse text for brand mentions. Output ONLY JSON."
    competitor_list = ", ".join(competitors) if competitors else "(none)"
    user = f"""Analyze the following AI-generated response for mentions of the brand "{brand}".
Also check for these competitors: {competitor_list}

RESPONSE:
\"\"\"{response_text[:6000]}\"\"\"

Return JSON:
{{
  "brand_mentioned": true|false,
  "mention_position": null | <approximate character index of first mention>,
  "mention_count": <int>,
  "sentiment": "positive"|"neutral"|"negative"|null,
  "sentiment_score": -1.0 to 1.0,
  "context_excerpt": "≤200 char snippet around the mention or null",
  "competitors_mentioned": ["list", "of", "competitor brands found"]
}}"""
    return _extract_json(await _complete(system, user, max_tokens=1000))
