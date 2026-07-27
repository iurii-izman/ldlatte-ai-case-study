from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SeedProfile:
    excel_row: int
    number: int | None
    display: str
    source_url: str
    handle: str
    normalized_url: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Candidate:
    handle: str
    platform: str
    url: str
    title: str
    followers: int | None
    avg_views: int | None
    engagement_rate: float | None
    facts: list[str]
    sources: list[dict[str, str]]
    features: dict[str, float]
    confidence: float
    risk: float
    cooperation_status: str
    contact: str
    offer_anchor: str
    score: float | None = None
    reason: str = ""
    offer: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Candidate:
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineResult:
    seeds: list[SeedProfile]
    data_quality: dict[str, Any]
    portrait: dict[str, Any]
    candidates: list[Candidate]
    run_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seeds": [seed.to_dict() for seed in self.seeds],
            "data_quality": self.data_quality,
            "portrait": self.portrait,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "run_meta": self.run_meta,
        }
