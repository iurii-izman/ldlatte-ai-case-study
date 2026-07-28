from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .llm import JSONLLMClient
from .models import SeedProfile


def load_annotations(path: str | Path) -> dict[str, dict[str, Any]]:
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    return {record["handle"].lower(): record for record in records}


def build_rule_based_portrait(
    seeds: list[SeedProfile],
    annotations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    roles = Counter()
    tags = Counter()
    evidenced = 0
    for seed in seeds:
        annotation = annotations.get(seed.handle, {})
        role = annotation.get("role", "unknown")
        roles[role] += 1
        for tag in annotation.get("tags", []):
            tags[tag] += 1
        if annotation.get("facts"):
            evidenced += 1

    total = max(len(seeds), 1)
    return {
        "method": "clustered_seed_portrait_v1",
        "evidence_coverage": round(evidenced / total, 2),
        "seed_roles": dict(roles),
        "dominant_tags": [tag for tag, _ in tags.most_common(10)],
        "aesthetic_archetype": {
            "visual": [
                "чистая светлая или нейтральная картинка",
                "женственная, носибельная стилизация",
                "Pinterest-подобная композиция без перегруженности",
                "Reels/Shorts с примеркой, деталями посадки и готовым образом",
            ],
            "voice": [
                "разговорно и тепло, как рекомендация подруге",
                "конкретика: артикулы, параметры, посадка и сценарий ношения",
                "польза важнее рекламных клише",
            ],
            "content": [
                "женская одежда, fashion/beauty/lifestyle",
                "готовые образы и находки WB/Ozon",
                "UGC, распаковки и честная примерка",
            ],
        },
        "operational_fit": {
            "must_have": [
                "русскоязычная женская аудитория",
                "свежие публикации за последние 30 дней",
                "хотя бы два конкретных доказательства тематического совпадения",
                "открытый канал связи или понятный путь к контакту",
            ],
            "preferred": [
                "5–80 тыс. подписчиков либо сопоставимый органический охват",
                "опыт обзоров одежды и маркетплейсов",
                "устойчивые просмотры, а не один вирусный ролик",
                "готовность обсуждать бартер или гибридный формат",
            ],
            "exclude_or_review": [
                "бренд вместо автора",
                "нерелевантная основная тематика: ремонт, еда, спорт без fashion-связи",
                "только крупный paid-only аккаунт без признаков бартерной готовности",
                "неподтверждённые или противоречивые метрики",
                "репутационный риск — только как флаг для ручной проверки, не как вердикт",
            ],
        },
        "important_interpretation": (
            "Брендовые аккаунты считаются visual_reference, а крупные lifestyle/home "
            "аккаунты — отдельными кластерами. Они не участвуют в расчёте бартерного диапазона."
        ),
    }


def build_llm_portrait(
    seeds: list[SeedProfile],
    annotations: dict[str, dict[str, Any]],
    client: JSONLLMClient,
    prompt_path: str | Path,
) -> dict[str, Any]:
    prompt = Path(prompt_path).read_text(encoding="utf-8")
    evidence = []
    for seed in seeds:
        annotation = annotations.get(seed.handle, {})
        evidence.append(
            {
                "handle": seed.handle,
                "role_hint": annotation.get("role", "unknown"),
                "tags": annotation.get("tags", []),
                "facts": annotation.get("facts", []),
                "sources": annotation.get("sources", []),
            }
        )
    portrait = client.complete_json(
        system=prompt,
        user=json.dumps({"seed_profiles": evidence}, ensure_ascii=False),
        max_tokens=2200,
    )
    evidenced = sum(
        bool(annotation.get("facts") or annotation.get("sources"))
        for annotation in (
            annotations.get(seed.handle, {})
            for seed in seeds
        )
    )
    portrait["evidence_coverage"] = round(evidenced / max(len(seeds), 1), 2)
    return portrait
