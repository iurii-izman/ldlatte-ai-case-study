from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from ddgs import DDGS

from .llm import JSONLLMClient
from .models import Candidate
from .xlsx_loader import normalize_instagram

DEFAULT_QUERIES = [
    'site:t.me/s ("стилист" OR "обзоры") ("Wildberries" OR "WB") "девочки"',
    'site:t.me/s "женственные образы" ("WB" OR "Ozon")',
    'site:instagram.com ("находки WB" OR "обзоры Wildberries") стиль',
]


def _candidate_handle(url: str) -> tuple[str, str] | None:
    instagram = normalize_instagram(url)
    if instagram:
        return instagram
    parsed = urlparse(url)
    if parsed.netloc.lower() in {"t.me", "www.t.me"}:
        parts = [part for part in parsed.path.split("/") if part and part != "s"]
        if parts:
            handle = parts[0].lower()
            return handle, f"https://t.me/{handle}"
    return None


def _looks_like_aggregator(title: str, snippet: str) -> bool:
    text = f"{title} {snippet}".lower()
    credited_handles = re.findall(r"@[a-z0-9._]{3,}", text)
    return (
        ("автор видео:" in text and len(set(credited_handles)) >= 2)
        or ("подписывайся чтобы не потерять" in text and "автор видео:" in text)
    )


def _parse_followers(text: str) -> int | None:
    patterns = [
        r"(\d+(?:[.,]\d+)?)\s*([kкmм]?)\s+followers",
        r"(\d+(?:[.,]\d+)?)\s*([kкmм])\s+(?:подписчик|subscriber)",
    ]
    lowered = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if not match:
            continue
        value = float(match.group(1).replace(",", "."))
        suffix = match.group(2).lower()
        multiplier = 1_000 if suffix in {"k", "к"} else 1_000_000 if suffix in {"m", "м"} else 1
        return int(value * multiplier)
    return None


def discover_live(
    *,
    seed_handles: set[str],
    client: JSONLLMClient,
    prompt_path: str | Path,
    max_results_per_query: int = 8,
) -> list[Candidate]:
    raw_results: list[dict[str, str]] = []
    with DDGS() as search:
        for query in DEFAULT_QUERIES:
            for item in search.text(query, max_results=max_results_per_query):
                url = item.get("href", "")
                identity = _candidate_handle(url)
                if not identity:
                    continue
                handle, canonical = identity
                if handle in seed_handles:
                    continue
                raw_results.append(
                    {
                        "title": item.get("title", ""),
                        "url": canonical,
                        "source_url": url,
                        "snippet": item.get("body", ""),
                    }
                )

    # Exact-URL allow-list: the LLM can select and classify, never invent a profile.
    by_url = {item["url"]: item for item in raw_results}
    prompt = Path(prompt_path).read_text(encoding="utf-8")
    result = client.complete_json(
        system=prompt,
        user=json.dumps({"search_results": list(by_url.values())}, ensure_ascii=False),
        max_tokens=2400,
    )
    candidates: list[Candidate] = []
    for item in result.get("candidates", []):
        url = item.get("url", "")
        if url not in by_url:
            continue
        if item.get("profile_type") not in {None, "personal_creator"}:
            continue
        identity = _candidate_handle(url)
        if not identity or identity[0] in seed_handles:
            continue
        evidence = by_url[url]
        if _looks_like_aggregator(evidence["title"], evidence["snippet"]):
            continue
        features = {
            key: float(value)
            for key, value in item.get("features", {}).items()
            if isinstance(value, (int, float))
        }
        followers = item.get("followers")
        if not isinstance(followers, (int, float)):
            followers = _parse_followers(f"{evidence['title']} {evidence['snippet']}")
        avg_views = item.get("avg_views")
        engagement_rate = item.get("engagement_rate")
        if avg_views is None and engagement_rate is None:
            features.pop("engagement_quality", None)
        if isinstance(followers, (int, float)):
            if followers > 80_000:
                features["barter_likelihood"] = min(
                    features.get("barter_likelihood", 0.4), 0.4
                )
            elif followers >= 30_000:
                features["barter_likelihood"] = min(
                    features.get("barter_likelihood", 0.6), 0.6
                )
        candidates.append(
            Candidate(
                handle=identity[0],
                platform=item.get("platform", "web"),
                url=url,
                title=item.get("title") or evidence["title"],
                followers=followers,
                avg_views=avg_views,
                engagement_rate=engagement_rate,
                facts=item.get("facts", [evidence["snippet"]]),
                sources=[
                    {
                        "url": evidence["source_url"],
                        "observed_at": "live",
                        "note": evidence["snippet"][:300],
                    }
                ],
                features=features,
                confidence=float(item.get("confidence", 0.55)),
                risk=float(item.get("risk", 0.1)),
                cooperation_status=item.get("cooperation_status", "требуется уточнить"),
                contact=item.get("contact", "см. профиль"),
                offer_anchor=item.get(
                    "offer_anchor",
                    "в публичном описании профиля есть релевантные fashion/WB-сигналы",
                ),
            )
        )
    return candidates
