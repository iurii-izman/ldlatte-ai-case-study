from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .discovery import discover_live
from .enrichment import collect_seed_evidence
from .google_sheets import download_google_sheet
from .llm import DeepSeekClient, JSONLLMClient
from .models import Candidate, PipelineResult
from .offers import deterministic_offer, generate_offer_with_llm
from .portrait import build_llm_portrait, build_rule_based_portrait, load_annotations
from .scoring import rank_candidates
from .xlsx_loader import load_seed_profiles

ROOT = Path(__file__).resolve().parent.parent


def load_cached_candidates(path: str | Path = ROOT / "data" / "candidates.json") -> list[Candidate]:
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Candidate.from_dict(record) for record in records]


def run_pipeline(
    input_path: str | Path,
    *,
    annotations_path: str | Path = ROOT / "examples" / "seed_annotations.json",
    live_llm: bool = False,
    live_seed_enrichment: bool = False,
    live_discovery: bool = False,
    client: JSONLLMClient | None = None,
    limit: int = 5,
) -> PipelineResult:
    resolved_input = (
        download_google_sheet(str(input_path))
        if str(input_path).startswith(("https://docs.google.com/", "http://docs.google.com/"))
        else input_path
    )
    seeds, quality = load_seed_profiles(resolved_input)
    annotations = load_annotations(annotations_path)
    llm_client = client or (
        DeepSeekClient()
        if live_llm or live_seed_enrichment or live_discovery
        else None
    )

    if live_seed_enrichment:
        try:
            annotations, enrichment_quality = collect_seed_evidence(seeds, annotations)
            quality.update(enrichment_quality)
        except Exception as exc:
            quality["seed_enrichment_fallback"] = (
                "Автоматический сбор seed-evidence недоступен; использованы "
                f"сохранённые аннотации ({type(exc).__name__})."
            )

    if (live_llm or live_seed_enrichment) and llm_client:
        portrait = build_llm_portrait(
            seeds,
            annotations,
            llm_client,
            ROOT / "prompts" / "portrait.md",
        )
    else:
        portrait = build_rule_based_portrait(seeds, annotations)

    if live_discovery and llm_client:
        try:
            candidates = discover_live(
                seed_handles={seed.handle for seed in seeds},
                portrait=portrait,
                client=llm_client,
                prompt_path=ROOT / "prompts" / "discovery.md",
            )
        except Exception as exc:
            candidates = []
            quality["live_discovery_error_type"] = type(exc).__name__
        if len(candidates) < 3:
            quality["live_discovery_fallback"] = (
                "Live-поиск недоступен или дал меньше трёх валидных URL; "
                "добавлен воспроизводимый cached snapshot."
            )
            existing = {candidate.handle for candidate in candidates}
            candidates.extend(
                item for item in load_cached_candidates() if item.handle not in existing
            )
    else:
        candidates = load_cached_candidates()

    ranked = rank_candidates(candidates, limit=limit)
    for candidate in ranked:
        if (live_llm or live_seed_enrichment) and llm_client:
            candidate.offer = generate_offer_with_llm(
                candidate,
                llm_client,
                ROOT / "prompts" / "offer.md",
            )
        else:
            candidate.offer = deterministic_offer(candidate)

    return PipelineResult(
        seeds=seeds,
        data_quality=quality,
        portrait=portrait,
        candidates=ranked,
        run_meta={
            "generated_at": datetime.now(UTC).isoformat(),
            "mode": (
                "live"
                if live_llm or live_seed_enrichment or live_discovery
                else "demo"
            ),
            "llm": (
                getattr(llm_client, "model", "custom")
                if live_llm or live_seed_enrichment or live_discovery
                else "none"
            ),
            "seed_enrichment": "live" if live_seed_enrichment else "saved",
            "human_approval_required": True,
        },
    )
