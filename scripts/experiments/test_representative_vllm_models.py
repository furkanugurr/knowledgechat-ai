#!/usr/bin/env python3
"""Record structural live-RAG results for one representative vLLM model."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from test_live_vllm_rag import (
    DEFAULT_CASES,
    call_chat,
    evaluate_case,
    load_cases,
)

ADDITIONAL_COMPLEX_CASE = {
    "id": "complex_grounded",
    "kind": "in_domain",
    "question": (
        "Web Sunucu Güvenliği ekranındaki saldırı koruma seçenekleri "
        "nelerdir ve ne amaçla kullanılır?"
    ),
    "expected_path_fragments": [
        "guvenlik_ayarlari/web-sunucu-guvenligi.md"
    ],
}


def model_slug(model: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", model.casefold()).strip("-")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test one vLLM model through the real KnowledgeChat API."
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--questions", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=240)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        cases = load_cases(args.questions)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    if args.questions is None:
        cases = [
            *DEFAULT_CASES[:5],
            ADDITIONAL_COMPLEX_CASE,
            *DEFAULT_CASES[5:],
        ]

    endpoint = f"{args.base_url.rstrip('/')}/api/v1/chat"
    results = []
    for case in cases:
        status, payload, duration, error = call_chat(
            endpoint, case["question"], args.timeout
        )
        result = evaluate_case(case, status, payload, duration, error)
        result["candidate_model"] = args.model
        results.append(result)
        print(
            f"{result['id']}: status={status} passed={result['passed']} "
            f"duration={result['duration_seconds']}s "
            f"sources={result['source_count']}"
        )

    output = args.output or Path(
        "work/experiments/lmcache/sprint_3_6",
        model_slug(args.model),
        "results.json",
    )
    report = {
        "candidate_model": args.model,
        "base_url": args.base_url,
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "in_domain_total": sum(
            item["kind"] == "in_domain" for item in results
        ),
        "in_domain_passed": sum(
            item["kind"] == "in_domain" and item["passed"]
            for item in results
        ),
        "out_of_domain_total": sum(
            item["kind"] == "out_of_domain" for item in results
        ),
        "out_of_domain_passed": sum(
            item["kind"] == "out_of_domain" and item["passed"]
            for item in results
        ),
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved: {output}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
