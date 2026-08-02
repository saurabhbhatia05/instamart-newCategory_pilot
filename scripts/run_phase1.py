#!/usr/bin/env python
"""Phase 1 CLI — analyze, recommend, and train without starting the full server."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.phase1.pipeline import DiscoveryPipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Discovery Assistant — Phase 1")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("analyze", help="Analyze sample purchase history")
    sub.add_parser("recommend", help="Generate one category recommendation")
    sub.add_parser("train", help="Train and persist ML model")
    sub.add_parser("info", help="Show model metadata")

    args = parser.parse_args()
    pipeline = DiscoveryPipeline()

    if args.command == "analyze":
        report = pipeline.analyze("user_001")
        print(json.dumps(report.model_dump(), indent=2, default=str))

    elif args.command == "recommend":
        result = pipeline.recommend("user_001")
        out = result.model_dump()
        if result.recommendation:
            out["recommendation"] = {
                "category": result.recommendation.category.value,
                "score": result.recommendation.score,
                "reason_tags": result.recommendation.reason_tags,
            }
        print(json.dumps(out, indent=2, default=str))

    elif args.command == "train":
        meta = pipeline.train()
        print(json.dumps({"status": "trained", "metadata": meta}, indent=2))

    elif args.command == "info":
        print(json.dumps(pipeline.model_info(), indent=2))


if __name__ == "__main__":
    main()
