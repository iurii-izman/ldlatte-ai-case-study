"""Tests for the deterministic evaluation harness.

These tests verify the scoring logic, helper functions, and overall
computation.  They do NOT call the live pipeline — fixture data is
constructed inline.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.evaluate_demo import (  # noqa: E402
    Dimension,
    _has_human_next_step,
    _has_personal_anchor,
    compute_overall,
    evaluate_candidates,
    evaluate_ingestion,
    evaluate_offers,
    evaluate_safety,
)


class DimensionTests(unittest.TestCase):
    def test_empty_dimension_scores_zero(self) -> None:
        d = Dimension("test", 0.5)
        self.assertEqual(d.score, 0.0)
        self.assertEqual(d.passed, 0)
        self.assertEqual(d.total, 0)

    def test_all_pass_scores_one(self) -> None:
        d = Dimension("test", 0.5)
        d.check("a", True)
        d.check("b", True)
        d.check("c", True)
        self.assertEqual(d.score, 1.0)
        self.assertEqual(d.passed, 3)

    def test_half_pass_scores_half(self) -> None:
        d = Dimension("test", 0.5)
        d.check("a", True)
        d.check("b", False)
        self.assertEqual(d.score, 0.5)

    def test_critical_failure_tracks_separately(self) -> None:
        d = Dimension("test", 0.5)
        d.check("a", True)
        d.check("b", False, critical=True)
        d.check("c", False)
        self.assertEqual(d.score, 1 / 3)
        self.assertEqual(d.critical_failures, ["b"])

    def test_critical_passed_does_not_fail(self) -> None:
        d = Dimension("test", 0.5)
        d.check("a", True, critical=True)
        self.assertEqual(d.critical_failures, [])
        self.assertEqual(d.score, 1.0)


class ComputeOverallTests(unittest.TestCase):
    def test_perfect_score(self) -> None:
        d1 = Dimension("a", 0.5)
        d1.check("x", True)
        d2 = Dimension("b", 0.5)
        d2.check("y", True)
        result = compute_overall([d1, d2])
        self.assertEqual(result["overall_score"], 100.0)
        self.assertEqual(result["critical_failures"], 0)

    def test_critical_penalty(self) -> None:
        d1 = Dimension("a", 0.5)
        d1.check("x", True)
        d2 = Dimension("b", 0.5)
        d2.check("y", False, critical=True)
        result = compute_overall([d1, d2])
        # Weighted: 0.5*1.0 + 0.5*0.0 = 0.5 → 50, minus 5 = 45
        self.assertEqual(result["overall_score"], 45.0)
        self.assertEqual(result["critical_failures"], 1)

    def test_critical_penalty_capped(self) -> None:
        d = Dimension("a", 1.0)
        d.check("a", True)
        for i in range(10):
            d.check(f"fail_{i}", False, critical=True)
        result = compute_overall([d])
        # 1/11 * 100 = 9.1, penalty = min(10*5, 30) = 30, overall = max(0, 9.1-30) = 0
        self.assertEqual(result["overall_score"], 0.0)
        self.assertEqual(result["critical_failures"], 10)


# ── fixture builders ─────────────────────────────────────────────────


def _seed(handle: str) -> dict:
    return {"handle": handle, "normalized_url": f"https://instagram.com/{handle}/"}


def _candidate(handle: str, **overrides) -> dict:
    base = {
        "handle": handle,
        "platform": "telegram",
        "url": f"https://t.me/{handle}",
        "title": f"Test {handle}",
        "followers": None,
        "avg_views": None,
        "engagement_rate": None,
        "facts": ["публикует обзоры WB", "свежий контент"],
        "sources": [
            {
                "url": f"https://t.me/s/{handle}",
                "observed_at": "2026-07-27",
                "note": "публичная лента",
            },
            {
                "url": "https://telemetr.me/content/test",
                "observed_at": "2026-07-27",
                "note": "метрики",
            },
        ],
        "features": {},
        "confidence": 0.85,
        "risk": 0.05,
        "cooperation_status": "требуется уточнить",
        "contact": "см. профиль",
        "offer_anchor": "вы показываете готовые образы с WB",
        "score": 80.0,
        "reason": "",
        "offer": (
            "Привет! Я из команды LD LATTE.\n\n"
            "Пишу именно вам, потому что вы показываете готовые образы с WB. "
            "Хотим предложить сотрудничество: вы выбираете вещь из капсулы, "
            "мы отправляем её в подарок, формат и сроки согласуем.\n\n"
            "Если вам интересен бартер, можно пришлю 3–4 позиции под ваш стиль?"
        ),
    }
    base.update(overrides)
    return base


# ── ingestion tests ──────────────────────────────────────────────────


class IngestionEvalTests(unittest.TestCase):
    def test_clean_ingestion_scores_full(self) -> None:
        dq = {
            "unique_profiles": 10,
            "hyperlink_overrides": 3,
            "skipped_non_profiles": 2,
            "duplicate_handles": 0,
        }
        seeds = [_seed(f"user{i}") for i in range(10)]
        d = evaluate_ingestion(dq, seeds)
        self.assertEqual(d.score, 1.0)

    def test_empty_seeds_fails_critical(self) -> None:
        d = evaluate_ingestion({}, [])
        self.assertLess(d.score, 1.0)

    def test_low_normalization_triggers_critical(self) -> None:
        dq = {"skipped_non_profiles": 90}
        seeds = [_seed("only_one")]
        d = evaluate_ingestion(dq, seeds)
        self.assertIn("normalization rate >= 50%", d.critical_failures)


# ── candidate tests ──────────────────────────────────────────────────


class CandidateEvalTests(unittest.TestCase):
    def test_five_clean_candidates_pass(self) -> None:
        cands = [_candidate(f"c{i}") for i in range(5)]
        seeds = [_seed(f"s{i}") for i in range(10)]
        d = evaluate_candidates(cands, seeds)
        self.assertEqual(d.score, 1.0)

    def test_too_few_candidates_critical(self) -> None:
        cands = [_candidate("c1")]
        d = evaluate_candidates(cands, [])
        self.assertIn("candidates in 3–5", d.critical_failures)

    def test_seed_duplicate_critical(self) -> None:
        cands = [_candidate("dup")]
        seeds = [_seed("dup")]
        d = evaluate_candidates(cands, seeds)
        self.assertIn("zero seed duplicates", d.critical_failures)

    def test_missing_sources_critical(self) -> None:
        cands = [_candidate("c1", sources=[]), _candidate("c2"), _candidate("c3")]
        d = evaluate_candidates(cands, [])
        # source_coverage = 2/3 ≈ 67% < 80% → check fails, but is it critical?
        # critical only if < 50%, so 67% is non-critical failure
        self.assertLess(d.score, 1.0)
        self.assertNotIn("source coverage >= 80%", d.critical_failures)

    def test_no_sources_at_all_critical(self) -> None:
        cands = [
            _candidate("c1", sources=[]),
            _candidate("c2", sources=[]),
            _candidate("c3", sources=[]),
        ]
        d = evaluate_candidates(cands, [])
        self.assertIn("source coverage >= 80%", d.critical_failures)

    def test_followers_zero_detected(self) -> None:
        cands = [_candidate("c1", followers=0), _candidate("c2"), _candidate("c3")]
        d = evaluate_candidates(cands, [])
        failed_names = [ch["name"] for ch in d.checks if not ch["ok"]]
        self.assertIn("unknown metrics not turned to zero", failed_names)

    def test_undated_sources_critical(self) -> None:
        undated = [{"url": "https://t.me/s/test", "observed_at": "live", "note": ""}]
        c1 = _candidate("c1")
        c1["sources"] = undated
        c2 = _candidate("c2")
        c2["sources"] = undated
        c3 = _candidate("c3")
        c3["sources"] = undated
        d = evaluate_candidates([c1, c2, c3], [])
        self.assertIn("dated source coverage >= 80%", d.critical_failures)


# ── offer tests ──────────────────────────────────────────────────────


class OfferEvalTests(unittest.TestCase):
    def test_perfect_offer_passes(self) -> None:
        c = _candidate("ok")
        d = evaluate_offers([c])
        self.assertEqual(d.score, 1.0)

    def test_invented_sender_critical(self) -> None:
        bad = _candidate("bad", offer="Привет! Я Мария из LD LATTE, веду бренд одежды.")
        d = evaluate_offers([bad])
        self.assertIn("candidate[0] no invented sender", d.critical_failures)

    def test_positive_review_requirement_critical(self) -> None:
        bad = _candidate("bad", offer="Жду положительный отзыв после публикации!")
        d = evaluate_offers([bad])
        self.assertIn("candidate[0] no positive-review requirement", d.critical_failures)

    def test_missing_anchor_detected(self) -> None:
        c = _candidate("noanchor", offer_anchor="", facts=[])
        d = evaluate_offers([c])
        self.assertIn(
            "candidate[0] has personal anchor",
            [ch["name"] for ch in d.checks if not ch["ok"]],
        )

    def test_short_offer_detected(self) -> None:
        c = _candidate("short", offer="Коротко.")
        d = evaluate_offers([c])
        self.assertIn(
            "candidate[0] length 100–900",
            [ch["name"] for ch in d.checks if not ch["ok"]],
        )

    def test_empty_cliche_detected(self) -> None:
        c = _candidate("cliche", offer_anchor="", offer="Предлагаю взаимовыгодное сотрудничество!")
        d = evaluate_offers([c])
        self.assertIn(
            "candidate[0] no empty cliches",
            [ch["name"] for ch in d.checks if not ch["ok"]],
        )


# ── safety tests ─────────────────────────────────────────────────────


class SafetyEvalTests(unittest.TestCase):
    def test_demo_safety_passes(self) -> None:
        meta = {"human_approval_required": True, "mode": "demo", "llm": "none"}
        raw = json.dumps({"run_meta": meta})
        d = evaluate_safety(meta, raw, [])
        self.assertEqual(d.score, 1.0)

    def test_missing_human_approval_critical(self) -> None:
        meta = {"mode": "demo"}
        d = evaluate_safety(meta, "{}", [])
        self.assertIn("human_approval_required == True", d.critical_failures)

    def test_api_key_leak_critical(self) -> None:
        meta = {"human_approval_required": True, "mode": "demo"}
        raw = '{"key": "sk-abc123def456ghi789jkl012mno345pqr678stu"}'
        d = evaluate_safety(meta, raw, [])
        self.assertIn("no API key in output", d.critical_failures)

    def test_private_path_leak_critical(self) -> None:
        meta = {"human_approval_required": True, "mode": "demo"}
        raw = '{"input": "docs/Блогеры.xlsx"}'
        d = evaluate_safety(meta, raw, [])
        self.assertIn("no private paths in output", d.critical_failures)

    def test_followers_zero_is_safety_issue(self) -> None:
        meta = {"human_approval_required": True, "mode": "demo"}
        cands = [_candidate("z", followers=0)]
        d = evaluate_safety(meta, "{}", cands)
        self.assertIn(
            "missing metrics not zeroed",
            [ch["name"] for ch in d.checks if not ch["ok"]],
        )


# ── helper tests ─────────────────────────────────────────────────────


class HelperTests(unittest.TestCase):
    def test_anchor_detected_in_offer(self) -> None:
        c = _candidate("test")
        self.assertTrue(_has_personal_anchor(c))

    def test_anchor_absent_detected(self) -> None:
        c = _candidate("test", offer_anchor="", facts=[])
        self.assertFalse(_has_personal_anchor(c))

    def test_fact_in_offer_detected(self) -> None:
        c = _candidate("test", offer_anchor="")
        c["facts"] = ["WB находки", "свежий контент"]
        c["offer"] = "Привет! Я вижу, что вы делаете WB находки. Сотрудничаем?"
        self.assertTrue(_has_personal_anchor(c))

    def test_human_next_step_question(self) -> None:
        self.assertTrue(_has_human_next_step("Интересно?"))

    def test_human_next_step_prishlu(self) -> None:
        self.assertTrue(_has_human_next_step("Можно пришлю бриф?"))

    def test_human_next_step_missing(self) -> None:
        self.assertFalse(_has_human_next_step("Сотрудничаем. Жду ответа."))


if __name__ == "__main__":
    unittest.main()
