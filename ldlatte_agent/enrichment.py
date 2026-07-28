from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from ddgs import DDGS

from .models import SeedProfile


def collect_seed_evidence(
    seeds: list[SeedProfile],
    annotations: dict[str, dict[str, Any]],
    *,
    max_results_per_seed: int = 3,
    search_factory: Callable[[], Any] = DDGS,
    observed_at: str | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Enrich seed annotations with dated, publicly indexed evidence.

    Search snippets are treated as evidence, not as official platform metrics.
    Existing annotations remain the fallback when a profile has no indexed result.
    """
    timestamp = observed_at or datetime.now(UTC).isoformat()
    enriched = {handle: dict(record) for handle, record in annotations.items()}
    profiles_with_evidence = 0
    source_count = 0
    search_failures = 0

    with search_factory() as search:
        for seed in seeds:
            query = f'site:instagram.com "{seed.handle}"'
            sources: list[dict[str, Any]] = []
            facts: list[str] = []
            seen_urls: set[str] = set()

            try:
                results = search.text(query, max_results=max_results_per_seed)
            except Exception:
                search_failures += 1
                continue

            for item in results:
                url = str(item.get("href", "")).strip()
                title = str(item.get("title", "")).strip()
                snippet = str(item.get("body", "")).strip()
                searchable = f"{url} {title} {snippet}".lower()
                if not url or url in seen_urls or seed.handle not in searchable:
                    continue
                if not title and not snippet:
                    continue
                seen_urls.add(url)

                fact = ": ".join(part for part in (title, snippet) if part)
                if fact and fact not in facts:
                    facts.append(fact[:600])
                sources.append(
                    {
                        "url": url,
                        "observed_at": timestamp,
                        "note": snippet[:300],
                        "confidence": 0.55,
                        "source_type": "public_search_index",
                    }
                )

            if not sources:
                continue

            existing = enriched.get(seed.handle, {})
            enriched[seed.handle] = {
                **existing,
                "handle": seed.handle,
                "role": existing.get("role", "unknown"),
                "tags": existing.get("tags", []),
                "facts": facts,
                "sources": sources,
                "evidence_origin": "live_public_search",
            }
            profiles_with_evidence += 1
            source_count += len(sources)

    return enriched, {
        "seed_enrichment_method": "public_search_index",
        "seed_enrichment_observed_at": timestamp,
        "seed_enrichment_profiles_with_evidence": profiles_with_evidence,
        "seed_enrichment_profiles_without_evidence": len(seeds) - profiles_with_evidence,
        "seed_enrichment_source_count": source_count,
        "seed_enrichment_search_failures": search_failures,
    }
