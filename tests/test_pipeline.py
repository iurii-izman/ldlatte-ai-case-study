from __future__ import annotations

import unittest
from pathlib import Path

from ldlatte_agent.discovery import _looks_like_aggregator, _parse_followers
from ldlatte_agent.google_sheets import google_sheet_export_url
from ldlatte_agent.models import Candidate
from ldlatte_agent.offers import deterministic_offer
from ldlatte_agent.pipeline import run_pipeline
from ldlatte_agent.scoring import score_candidate
from ldlatte_agent.xlsx_loader import load_seed_profiles, normalize_instagram

ROOT = Path(__file__).resolve().parent.parent


class InstagramNormalizationTests(unittest.TestCase):
    def test_removes_tracking(self) -> None:
        result = normalize_instagram(
            "https://www.instagram.com/Demo.Latte.Style?igsh=abc&utm_source=qr"
        )
        self.assertEqual(
            result,
            ("demo.latte.style", "https://www.instagram.com/demo.latte.style/"),
        )

    def test_rejects_post_url(self) -> None:
        self.assertIsNone(normalize_instagram("https://instagram.com/p/abc123"))

    def test_repost_aggregator_is_rejected(self) -> None:
        self.assertTrue(
            _looks_like_aggregator(
                "WOMEN STYLE | WB OZON",
                "Подписывайся чтобы не потерять. Автор видео: @first_author и @second_author",
            )
        )
        self.assertFalse(
            _looks_like_aggregator(
                "Стилист Анна",
                "Я показываю свои покупки и готовые образы с WB.",
            )
        )

    def test_parses_indexed_follower_counts(self) -> None:
        self.assertEqual(_parse_followers("136K Followers, 1,117 Following"), 136_000)
        self.assertEqual(_parse_followers("57.4K subscribers"), 57_400)

    def test_google_sheet_url_becomes_xlsx_export(self) -> None:
        self.assertEqual(
            google_sheet_export_url(
                "https://docs.google.com/spreadsheets/d/abc_DEF-123/edit#gid=987"
            ),
            "https://docs.google.com/spreadsheets/d/abc_DEF-123/export?format=xlsx&gid=987",
        )


class WorkbookTests(unittest.TestCase):
    def test_demo_workbook_is_self_contained(self) -> None:
        seeds, quality = load_seed_profiles(ROOT / "examples" / "bloggers-demo.xlsx")
        handles = {seed.handle for seed in seeds}
        self.assertEqual(len(seeds), 10)
        self.assertIn("demo.latte.style", handles)
        self.assertIn("demo.neutral.looks", handles)
        self.assertEqual(quality["sheet"], "Исходник")

    @unittest.skipUnless(
        (ROOT / "docs" / "Блогеры.xlsx").exists(),
        "Закрытая исходная таблица не входит в публичный репозиторий.",
    )
    def test_real_workbook_uses_hyperlink_target(self) -> None:
        seeds, quality = load_seed_profiles(ROOT / "docs" / "Блогеры.xlsx")
        self.assertEqual(len(seeds), 34)
        self.assertEqual(seeds[0].number, 1)
        self.assertEqual(seeds[-1].number, 38)
        self.assertGreaterEqual(quality["hyperlink_overrides"], 6)


class ScoringTests(unittest.TestCase):
    def test_missing_metric_is_not_zero(self) -> None:
        candidate = Candidate(
            handle="test",
            platform="telegram",
            url="https://t.me/test",
            title="Test",
            followers=None,
            avg_views=None,
            engagement_rate=None,
            facts=[],
            sources=[],
            features={"content_fit": 1.0, "aesthetic_fit": 1.0},
            confidence=0.8,
            risk=0.0,
            cooperation_status="unknown",
            contact="",
            offer_anchor="",
        )
        score_candidate(candidate)
        self.assertGreater(candidate.score or 0, 90)

    def test_demo_pipeline_returns_verified_candidate_snapshot(self) -> None:
        result = run_pipeline(ROOT / "examples" / "bloggers-demo.xlsx")
        seed_handles = {seed.handle for seed in result.seeds}
        self.assertEqual(len(result.candidates), 5)
        self.assertTrue(all(item.handle not in seed_handles for item in result.candidates))
        self.assertTrue(all(item.sources for item in result.candidates))
        self.assertTrue(all(len(item.offer) > 100 for item in result.candidates))

    def test_deterministic_offer_does_not_invent_sender(self) -> None:
        candidate = Candidate(
            handle="test",
            platform="telegram",
            url="https://t.me/test",
            title="Test",
            followers=None,
            avg_views=None,
            engagement_rate=None,
            facts=[],
            sources=[],
            features={},
            confidence=0.5,
            risk=0.0,
            cooperation_status="требуется уточнить",
            contact="",
            offer_anchor="вы показываете готовые образы",
        )
        offer = deterministic_offer(candidate)
        self.assertIn("из команды LD LATTE", offer)
        self.assertNotIn("Я Женя", offer)
        self.assertNotIn("я веду бренд", offer.lower())


if __name__ == "__main__":
    unittest.main()
