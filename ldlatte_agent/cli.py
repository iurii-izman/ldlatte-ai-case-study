from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import ROOT, run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="LD LATTE Influencer Scout")
    parser.add_argument(
        "--input",
        required=True,
        help="Путь к XLSX или URL публичной Google Sheets",
    )
    parser.add_argument("--output", required=True, help="Путь к JSON-результату")
    parser.add_argument(
        "--annotations",
        default=str(ROOT / "examples" / "seed_annotations.json"),
        help="Путь к JSON-аннотациям seed-профилей",
    )
    parser.add_argument("--live-llm", action="store_true")
    parser.add_argument(
        "--live-seed-enrichment",
        action="store_true",
        help="Собрать публичные web-evidence по seed-профилям перед портретом",
    )
    parser.add_argument("--live-discovery", action="store_true")
    parser.add_argument("--limit", type=int, default=5, choices=range(3, 6))
    args = parser.parse_args()

    result = run_pipeline(
        args.input,
        annotations_path=args.annotations,
        live_llm=args.live_llm,
        live_seed_enrichment=args.live_seed_enrichment,
        live_discovery=args.live_discovery,
        limit=args.limit,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Готово: {output} | seeds={len(result.seeds)} candidates={len(result.candidates)}")


if __name__ == "__main__":
    main()
