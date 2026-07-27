from __future__ import annotations

from .models import Candidate

WEIGHTS = {
    "content_fit": 0.20,
    "aesthetic_fit": 0.20,
    "marketplace_fit": 0.15,
    "engagement_quality": 0.15,
    "audience_fit": 0.10,
    "activity": 0.10,
    "barter_likelihood": 0.10,
}


def score_candidate(candidate: Candidate) -> Candidate:
    observed = {
        key: max(0.0, min(1.0, candidate.features[key]))
        for key in WEIGHTS
        if key in candidate.features
    }
    if not observed:
        candidate.score = 0.0
        candidate.reason = "Нет наблюдаемых признаков для оценки."
        return candidate

    # Missing is not zero: normalize only over observed dimensions.
    observed_weight = sum(WEIGHTS[key] for key in observed)
    raw = sum(observed[key] * WEIGHTS[key] for key in observed) / observed_weight
    confidence_factor = 0.85 + 0.15 * max(0.0, min(1.0, candidate.confidence))
    risk_penalty = 0.15 * max(0.0, min(1.0, candidate.risk))
    candidate.score = round(max(0.0, min(1.0, raw * confidence_factor - risk_penalty)) * 100, 1)

    strongest = sorted(
        observed.items(),
        key=lambda item: item[1] * WEIGHTS[item[0]],
        reverse=True,
    )[:3]
    labels = {
        "content_fit": "совпадение тематики",
        "aesthetic_fit": "визуальное совпадение",
        "marketplace_fit": "опыт WB/Ozon",
        "engagement_quality": "качество вовлечения",
        "audience_fit": "совпадение аудитории",
        "activity": "свежесть",
        "barter_likelihood": "вероятность бартера",
    }
    candidate.reason = (
        "; ".join(f"{labels[key]} {value:.0%}" for key, value in strongest)
        + f". Уверенность данных: {candidate.confidence:.0%}."
    )
    return candidate


def rank_candidates(candidates: list[Candidate], limit: int = 5) -> list[Candidate]:
    scored = [score_candidate(candidate) for candidate in candidates]
    return sorted(scored, key=lambda item: item.score or 0.0, reverse=True)[:limit]
