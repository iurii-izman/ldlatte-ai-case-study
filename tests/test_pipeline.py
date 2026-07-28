from __future__ import annotations

import json
import os
import re
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook

from ldlatte_agent.discovery import (
    DEFAULT_QUERIES,
    _looks_like_aggregator,
    _parse_followers,
    discover_live,
)
from ldlatte_agent.enrichment import collect_seed_evidence
from ldlatte_agent.google_sheets import google_sheet_export_url
from ldlatte_agent.models import Candidate, SeedProfile
from ldlatte_agent.offers import deterministic_offer, generate_offer_with_llm
from ldlatte_agent.pipeline import run_pipeline
from ldlatte_agent.scoring import score_candidate
from ldlatte_agent.xlsx_loader import load_seed_profiles, normalize_instagram

ROOT = Path(__file__).resolve().parent.parent

ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
)


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

    def test_duplicate_handles_are_counted(self) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Исходник"
        worksheet.append(["№", "Ссылка"])
        worksheet.append([1, "https://www.instagram.com/demo.latte.style/"])
        worksheet.append(
            [2, "https://www.instagram.com/demo.latte.style/?utm_source=duplicate"]
        )
        stream = BytesIO()
        workbook.save(stream)
        stream.seek(0)

        seeds, quality = load_seed_profiles(stream)

        self.assertEqual(len(seeds), 1)
        self.assertEqual(quality["duplicate_handles"], 1)

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

    def test_live_search_failure_returns_cached_candidates(self) -> None:
        with patch(
            "ldlatte_agent.pipeline.discover_live",
            side_effect=RuntimeError("search unavailable"),
        ):
            result = run_pipeline(
                ROOT / "examples" / "bloggers-demo.xlsx",
                live_discovery=True,
                client=object(),
            )

        self.assertEqual(len(result.candidates), 5)
        self.assertEqual(
            result.data_quality["live_discovery_error_type"],
            "RuntimeError",
        )
        self.assertIn("cached snapshot", result.data_quality["live_discovery_fallback"])

    def test_offer_guardrails_preserve_sender_and_personal_anchor(self) -> None:
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

        class GenericOfferClient:
            def complete_json(self, *, system, user, max_tokens):
                return {
                    "offer": (
                        "Привет! Пишу из команды LD LATTE. Нам близок ваш формат "
                        "и хотелось бы предложить сотрудничество с брендом женской "
                        "одежды. Можно прислать несколько позиций и короткий бриф? "
                        "Формат, сроки и права на контент заранее согласуем."
                    )
                }

        guarded = generate_offer_with_llm(
            candidate,
            GenericOfferClient(),
            ROOT / "prompts" / "offer.md",
        )
        self.assertIn(candidate.offer_anchor, guarded)


class LiveDiscoveryHardeningTests(unittest.TestCase):
    def test_discovery_uses_portrait_queries_and_context(self) -> None:
        queries: list[str] = []

        class FakeSearch:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def text(self, query, max_results):
                queries.append(query)
                return []

        class FakeClient:
            def complete_json(self, *, system, user, max_tokens):
                payload = json.loads(user)
                self.portrait = payload["ideal_blogger_portrait"]
                return {"candidates": []}

        client = FakeClient()
        portrait = {
            "summary": "Носибельные женственные образы",
            "search_queries": ['site:t.me/s "капсула WB" стилист'],
        }

        with patch("ldlatte_agent.discovery.DDGS", FakeSearch):
            candidates = discover_live(
                seed_handles=set(),
                portrait=portrait,
                client=client,
                prompt_path=ROOT / "prompts" / "discovery.md",
            )

        self.assertEqual(candidates, [])
        self.assertEqual(queries[0], portrait["search_queries"][0])
        self.assertTrue(all(query in queries for query in DEFAULT_QUERIES))
        self.assertEqual(client.portrait, portrait)

    def test_iso8601_regex_accepts_valid_dates(self) -> None:
        """P0-06: iso8601 regex used for validation must accept real timestamps."""
        valid = [
            "2026-07-27T14:30:00+00:00",
            "2026-07-27T14:30:00Z",
            "2026-07-27T14:30:00.123456+00:00",
            "2026-07-27",
        ]
        for ts in valid:
            self.assertTrue(
                ISO8601_RE.match(ts),
                f"'{ts}' should match ISO-8601 regex",
            )

    def test_iso8601_regex_rejects_literal_live(self) -> None:
        """P0-06: 'live' must not pass as an ISO-8601 date."""
        self.assertIsNone(ISO8601_RE.match("live"))
        self.assertIsNone(ISO8601_RE.match(""))

    @unittest.skipUnless(
        os.getenv("DEEPSEEK_API_KEY") and (ROOT / "docs" / "Блогеры.xlsx").exists(),
        "Live API key and private workbook required.",
    )
    def test_live_discovery_produces_iso8601_dates(self) -> None:
        """P0-06 integration: every live source must carry an ISO-8601 observed_at."""
        from dotenv import load_dotenv

        load_dotenv(override=False)
        result = run_pipeline(
            ROOT / "docs" / "Блогеры.xlsx",
            live_llm=True,
            live_discovery=True,
        )
        for candidate in result.candidates:
            for source in candidate.sources:
                oat = source.get("observed_at", "")
                self.assertNotEqual(
                    oat,
                    "live",
                    f"observed_at='live' for candidate {candidate.handle}",
                )
                self.assertTrue(
                    ISO8601_RE.match(oat),
                    f"observed_at='{oat}' is not ISO-8601 for {candidate.handle}",
                )


class SeedEnrichmentTests(unittest.TestCase):
    def test_collects_dated_public_evidence_without_inventing_metrics(self) -> None:
        seed = SeedProfile(
            excel_row=2,
            number=1,
            display="@demo.latte.style",
            source_url="https://www.instagram.com/demo.latte.style/",
            handle="demo.latte.style",
            normalized_url="https://www.instagram.com/demo.latte.style/",
        )
        missing_seed = SeedProfile(
            excel_row=3,
            number=2,
            display="@demo.no.index",
            source_url="https://www.instagram.com/demo.no.index/",
            handle="demo.no.index",
            normalized_url="https://www.instagram.com/demo.no.index/",
        )

        class FakeSearch:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def text(self, query, max_results):
                self.query = query
                self.max_results = max_results
                if "demo.no.index" in query:
                    raise RuntimeError("search unavailable")
                return [
                    {
                        "href": "https://www.instagram.com/demo.latte.style/",
                        "title": "Demo Latte Style",
                        "body": "Женственные образы и примерки одежды.",
                    },
                    {
                        "href": "https://example.com/unrelated",
                        "title": "Другой профиль",
                        "body": "Нерелевантный результат.",
                    },
                ]

        annotations, quality = collect_seed_evidence(
            [seed, missing_seed],
            {},
            search_factory=FakeSearch,
            observed_at="2026-07-28T10:00:00+00:00",
        )

        record = annotations[seed.handle]
        self.assertEqual(record["role"], "unknown")
        self.assertEqual(record["evidence_origin"], "live_public_search")
        self.assertEqual(len(record["facts"]), 1)
        self.assertEqual(len(record["sources"]), 1)
        self.assertEqual(
            record["sources"][0]["observed_at"],
            "2026-07-28T10:00:00+00:00",
        )
        self.assertNotIn("followers", record)
        self.assertNotIn(missing_seed.handle, annotations)
        self.assertEqual(quality["seed_enrichment_profiles_with_evidence"], 1)
        self.assertEqual(quality["seed_enrichment_profiles_without_evidence"], 1)
        self.assertEqual(quality["seed_enrichment_search_failures"], 1)


if __name__ == "__main__":
    unittest.main()
