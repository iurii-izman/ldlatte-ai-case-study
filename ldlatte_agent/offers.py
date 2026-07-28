from __future__ import annotations

import json
import re
from pathlib import Path

from .llm import JSONLLMClient
from .models import Candidate


def deterministic_offer(candidate: Candidate) -> str:
    return (
        f"Привет! Я из команды LD LATTE — мы создаём женскую одежду с нуля и продаём "
        f"её на Wildberries и Ozon.\n\n"
        f"Пишу именно вам, потому что {candidate.offer_anchor}. Нам близок такой формат: "
        f"не просто показать вещь, а встроить её в понятный и носибельный образ.\n\n"
        f"Хотим предложить сотрудничество: вы выбираете подходящую вещь из актуальной "
        f"капсулы LD LATTE, мы отправляем её в подарок, а формат публикации и сроки заранее "
        f"согласуем без требования «положительного отзыва». Права на повторное использование "
        f"контента обсуждаем отдельно.\n\n"
        f"Если вам в целом интересен бартер или гибридный формат, можно пришлю 3–4 позиции "
        f"под ваш стиль и короткий бриф?"
    )


def _has_personal_anchor(candidate: Candidate, offer: str) -> bool:
    if candidate.offer_anchor and candidate.offer_anchor[:30] in offer:
        return True
    return any(fact[:20] in offer for fact in candidate.facts if fact)


def generate_offer_with_llm(
    candidate: Candidate,
    client: JSONLLMClient,
    prompt_path: str | Path,
) -> str:
    prompt = Path(prompt_path).read_text(encoding="utf-8")
    payload = {
        "brand": {
            "name": "LD LATTE",
            "category": "женская одежда",
            "channels": ["Wildberries", "Ozon"],
            "tone": "тёпло, конкретно, на ты",
        },
        "candidate": candidate.to_dict(),
    }
    result = client.complete_json(
        system=prompt,
        user=json.dumps(payload, ensure_ascii=False),
        max_tokens=900,
    )
    offer = result.get("offer")
    if not isinstance(offer, str) or len(offer.strip()) < 80:
        raise RuntimeError("LLM не вернул пригодный текст оффера.")
    cleaned = offer.strip()
    forbidden_patterns = [
        r"\bя\s+(?:веду|основал[аи]?|создал[аи]?|владею)\s+(?:бренд|LD LATTE)",
        r"\bя\s+[А-ЯЁ][а-яё]{2,}\s+из\s+LD LATTE\b",
    ]
    if any(re.search(pattern, cleaned, flags=re.IGNORECASE) for pattern in forbidden_patterns):
        # Safe fallback is better than a polished hallucination.
        return deterministic_offer(candidate)
    if not _has_personal_anchor(candidate, cleaned):
        return deterministic_offer(candidate)
    return cleaned
