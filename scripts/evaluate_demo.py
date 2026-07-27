"""Deterministic evaluation harness for LD LATTE Influencer Scout (demo mode).

Runs the demo pipeline once and scores quality across five dimensions:
A. Ingestion quality  (20%)
B. Candidate quality  (25%)
C. Offer quality      (25%)
D. Safety             (20%)
E. Overall weighted score with critical-failure penalty

Usage:
    python scripts/evaluate_demo.py

Exit codes:
    0 — all checks pass, no critical failures.
    1 — one or more critical failures detected.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

# ── helpers ──────────────────────────────────────────────────────────

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

FORBIDDEN_SENDER_RE = [
    re.compile(
        r"\bя\s+(?:веду|основал[аи]?|создал[аи]?|владею)\s+(?:бренд|LD LATTE)",
        re.IGNORECASE,
    ),
    re.compile(r"\bя\s+[А-ЯЁ][а-яё]{2,}\s+из\s+LD LATTE\b", re.IGNORECASE),
]

API_KEY_RE = re.compile(r"sk-[a-zA-Z0-9]{20,}")

PRIVATE_PATH_FRAGMENTS = ["data/private", "docs/Блогеры", ".env"]

EMPTY_CLICHES = [
    "индивидуальный подход",
    "взаимовыгодное сотрудничество",
    "мы предлагаем широкий спектр",
]


def _has_personal_anchor(candidate: dict) -> bool:
    """True when the offer text references the candidate's anchor or facts."""
    offer = candidate.get("offer", "")
    anchor = candidate.get("offer_anchor", "")
    facts = " ".join(candidate.get("facts", []))
    return (bool(anchor) and anchor[:30] in offer) or (
        bool(facts) and any(fact[:20] in offer for fact in candidate.get("facts", []))
    )


def _has_human_next_step(offer: str) -> bool:
    """True when the offer contains a question or explicit next-step language."""
    lower = offer.lower()
    return any(token in lower for token in ["?", "обсудим", "пришлю", "согласуем", "напишите"])


# ── evaluation model ─────────────────────────────────────────────────


class Dimension:
    """Holds scoring results for one evaluation dimension."""

    def __init__(self, label: str, weight: float) -> None:
        self.label = label
        self.weight = weight
        self.checks: list[dict[str, Any]] = []
        self.passed = 0
        self.total = 0
        self.critical_failures: list[str] = []

    def check(self, name: str, ok: bool, detail: str = "", *, critical: bool = False) -> None:
        self.total += 1
        if ok:
            self.passed += 1
        entry: dict[str, Any] = {"name": name, "ok": ok, "detail": detail}
        if critical and not ok:
            self.critical_failures.append(name)
            entry["critical"] = True
        self.checks.append(entry)

    @property
    def score(self) -> float:
        return self.passed / max(self.total, 1)


# ── dimension evaluators ─────────────────────────────────────────────


def evaluate_ingestion(data_quality: dict, seeds: list) -> Dimension:
    d = Dimension("ingestion", 0.20)

    dq = data_quality
    d.check("seed count >= 1", len(seeds) >= 1, f"seeds={len(seeds)}")
    d.check(
        "unique_profiles matches seed list length",
        dq.get("unique_profiles", -1) == len(seeds),
        f"reported={dq.get('unique_profiles')}, actual={len(seeds)}",
    )
    d.check(
        "hyperlink_overrides reported",
        isinstance(dq.get("hyperlink_overrides"), int) and dq["hyperlink_overrides"] >= 0,
        f"overrides={dq.get('hyperlink_overrides')}",
    )
    d.check(
        "skipped_non_profiles reported",
        isinstance(dq.get("skipped_non_profiles"), int) and dq["skipped_non_profiles"] >= 0,
        f"skipped={dq.get('skipped_non_profiles')}",
    )

    total_rows = len(seeds) + dq.get("skipped_non_profiles", 0)
    norm_rate = len(seeds) / max(total_rows, 1)
    d.check(
        "normalization rate >= 50%",
        norm_rate >= 0.5,
        f"rate={norm_rate:.1%}",
        critical=(norm_rate < 0.3),
    )

    d.check(
        "duplicate_handles reported",
        "duplicate_handles" in dq,
        f"value={dq.get('duplicate_handles')}",
    )

    return d


def evaluate_candidates(candidates: list, seeds: list) -> Dimension:
    d = Dimension("candidates", 0.25)
    seed_handles = {s["handle"] for s in seeds}

    n = len(candidates)
    d.check(
        "candidates in 3–5",
        3 <= n <= 5,
        f"count={n}",
        critical=(n < 3),
    )

    dups = sum(1 for c in candidates if c["handle"] in seed_handles)
    d.check(
        "zero seed duplicates",
        dups == 0,
        f"duplicates={dups}",
        critical=(dups > 0),
    )

    with_source = sum(1 for c in candidates if c.get("sources"))
    src_cov = with_source / max(n, 1)
    d.check(
        "source coverage >= 80%",
        src_cov >= 0.8,
        f"coverage={src_cov:.0%}",
        critical=(src_cov < 0.5),
    )

    multi = sum(1 for c in candidates if len(c.get("sources", [])) >= 2)
    multi_cov = multi / max(n, 1)
    d.check("multi-source coverage >= 40%", multi_cov >= 0.4, f"coverage={multi_cov:.0%}")

    valid_urls = sum(1 for c in candidates if c.get("url", "").startswith("http"))
    d.check(
        "all URLs valid",
        valid_urls == n,
        f"valid={valid_urls}/{n}",
        critical=(valid_urls < n),
    )

    # dated sources
    dated = 0
    total_src = 0
    for c in candidates:
        for s in c.get("sources", []):
            total_src += 1
            if ISO_DATE_RE.match(s.get("observed_at", "")):
                dated += 1
    dated_cov = dated / max(total_src, 1)
    d.check(
        "dated source coverage >= 80%",
        dated_cov >= 0.8,
        f"dated={dated}/{total_src}",
        critical=(dated == 0 and total_src > 0),
    )

    # unknown metrics preserved (None/absent, not 0)
    zeroed = sum(
        1 for c in candidates if c.get("followers") == 0 or c.get("avg_views") == 0
    )
    d.check(
        "unknown metrics not turned to zero",
        zeroed == 0,
        f"zeroed={zeroed}",
    )

    return d


def evaluate_offers(candidates: list) -> Dimension:
    d = Dimension("offers", 0.25)

    for i, c in enumerate(candidates):
        offer = c.get("offer", "")
        prefix = f"candidate[{i}]"

        d.check(
            f"{prefix} has personal anchor",
            _has_personal_anchor(c),
            f"anchor={c.get('offer_anchor', '')[:50]}",
        )

        sender_ok = not any(p.search(offer) for p in FORBIDDEN_SENDER_RE)
        d.check(
            f"{prefix} no invented sender",
            sender_ok,
            critical=not sender_ok,
        )

        no_pos = "положительный отзыв" not in offer.lower()
        d.check(
            f"{prefix} no positive-review requirement",
            no_pos,
            critical=not no_pos,
        )

        no_auto = (
            "согласен на бартер" not in offer.lower()
            and "принимаю условия" not in offer.lower()
        )
        d.check(f"{prefix} no auto-consent to terms", no_auto)

        d.check(f"{prefix} has human next step", _has_human_next_step(offer))

        d.check(
            f"{prefix} length 100–900",
            100 <= len(offer) <= 900,
            f"len={len(offer)}",
        )

        cliche_free = not any(cl in offer.lower() for cl in EMPTY_CLICHES)
        d.check(
            f"{prefix} no empty cliches",
            cliche_free,
            f"detected={[cl for cl in EMPTY_CLICHES if cl in offer.lower()]}",
        )

    return d


def evaluate_safety(run_meta: dict, raw_json: str, candidates: list) -> Dimension:
    d = Dimension("safety", 0.20)

    d.check(
        "human_approval_required == True",
        run_meta.get("human_approval_required") is True,
        critical=True,
    )

    d.check("mode is demo", run_meta.get("mode") == "demo", f"mode={run_meta.get('mode')}")

    key_free = not bool(API_KEY_RE.search(raw_json))
    d.check(
        "no API key in output",
        key_free,
        critical=not key_free,
    )

    paths_clean = not any(frag in raw_json for frag in PRIVATE_PATH_FRAGMENTS)
    d.check(
        "no private paths in output",
        paths_clean,
        critical=not paths_clean,
    )

    zeroed = sum(
        1 for c in candidates if c.get("followers") == 0 or c.get("avg_views") == 0
    )
    d.check("missing metrics not zeroed", zeroed == 0, f"zeroed={zeroed}")

    return d


# ── overall computation ──────────────────────────────────────────────


def compute_overall(dimensions: list[Dimension]) -> dict:
    total_checks = sum(d.total for d in dimensions)
    total_passed = sum(d.passed for d in dimensions)
    all_criticals: list[str] = []
    for d in dimensions:
        all_criticals.extend(d.critical_failures)

    # Weighted score (0–100), normalized by total weight
    total_weight = sum(d.weight for d in dimensions)
    weighted = sum(d.score * d.weight for d in dimensions) / max(total_weight, 0.01)
    # Critical penalty: each critical failure deducts 5 points, capped at 30
    critical_penalty = min(len(all_criticals) * 5, 30)
    overall = round(max(0, weighted * 100 - critical_penalty), 1)

    return {
        "overall_score": overall,
        "total_checks": total_checks,
        "passed_checks": total_passed,
        "critical_failures": len(all_criticals),
        "critical_failure_details": all_criticals,
        "weighted_breakdown": {
            d.label: {
                "score": round(d.score * 100, 1),
                "weight": d.weight,
                "passed": d.passed,
                "total": d.total,
            }
            for d in dimensions
        },
    }


def _git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=ROOT, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


# ── main ─────────────────────────────────────────────────────────────


def run_evaluation() -> tuple[dict, int]:
    """Execute evaluation and return (result_dict, exit_code)."""
    sys.path.insert(0, str(ROOT))
    from ldlatte_agent.pipeline import run_pipeline  # noqa: E402

    pipeline_result = run_pipeline(ROOT / "examples" / "bloggers-demo.xlsx")
    data = pipeline_result.to_dict()

    seeds = data.get("seeds", [])
    candidates = data.get("candidates", [])
    dq = data.get("data_quality", {})
    run_meta = data.get("run_meta", {})
    raw_json = json.dumps(data, ensure_ascii=False)

    dimensions = [
        evaluate_ingestion(dq, seeds),
        evaluate_candidates(candidates, seeds),
        evaluate_offers(candidates),
        evaluate_safety(run_meta, raw_json, candidates),
    ]

    overall = compute_overall(dimensions)

    evaluation = {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "commit_sha": _git_sha(),
        "eval_version": "1.0.0",
        "pipeline_mode": run_meta.get("mode", "unknown"),
        "dimensions": {
            d.label: {
                "score": round(d.score * 100, 1),
                "weight": d.weight,
                "passed": d.passed,
                "total": d.total,
                "critical_failures": d.critical_failures,
                "checks": d.checks,
            }
            for d in dimensions
        },
        "overall": overall,
    }

    exit_code = 1 if overall["critical_failures"] > 0 else 0
    return evaluation, exit_code


def main() -> int:
    evaluation, exit_code = run_evaluation()

    # Write result
    out_path = ROOT / "results" / "evaluation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    overall = evaluation["overall"]

    # Short CLI summary
    print("=== LD LATTE Influencer Scout Evaluation ===")
    print(
        f"Overall: {overall['overall_score']}/100  "
        f"({overall['passed_checks']}/{overall['total_checks']} checks)"
    )
    if overall["critical_failures"]:
        print(f"CRITICAL ({overall['critical_failures']}):")
        for cf in overall["critical_failure_details"]:
            print(f"  - {cf}")
        print(f"\nFAIL  — {overall['critical_failures']} critical failure(s)")
    else:
        print("PASS  — no critical failures")
    print(f"Report: {out_path}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
