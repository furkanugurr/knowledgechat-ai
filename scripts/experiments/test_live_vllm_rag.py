#!/usr/bin/env python3
"""Run non-mutating live RAG checks through the KnowledgeChat HTTP API."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CASES = [
    {
        "id": "concept_definition",
        "kind": "in_domain",
        "question": "VLAN nedir?",
        "expected_path_fragments": ["ag_yapilandirmasi"],
    },
    {
        "id": "navigation",
        "kind": "in_domain",
        "question": "SSL VPN ayarları hangi menü altında?",
        "expected_path_fragments": ["vpn/ssl-vpn-ayarlari.md"],
    },
    {
        "id": "multipart",
        "kind": "in_domain",
        "question": (
            "OSPF nedir ve Antikor'da OSPF yapılandırması nasıl yapılır?"
        ),
        "expected_path_fragments": ["yonlendirme-yonetimi/ospf"],
    },
    {
        "id": "comparison",
        "kind": "in_domain",
        "question": "IPSec VPN ile SSL VPN arasındaki fark nedir?",
        "expected_path_fragments": ["vpn/"],
    },
    {
        "id": "multi_chunk",
        "kind": "in_domain",
        "question": (
            "Raporlar bölümündeki Rapor Ayarları ekranında hangi alanlar "
            "bulunur?"
        ),
        "expected_path_fragments": ["raporlar/rapor-ayarlari.md"],
    },
    {
        "id": "out_of_domain_food",
        "kind": "out_of_domain",
        "question": "hamburger faydalı mı?",
        "expected_path_fragments": [],
    },
    {
        "id": "out_of_domain_weather",
        "kind": "out_of_domain",
        "question": "Yarın İstanbul'da hava nasıl olacak?",
        "expected_path_fragments": [],
    },
]


def load_cases(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return DEFAULT_CASES
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_cases = payload.get("cases", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Question file must contain a non-empty list or cases list")
    cases: list[dict[str, Any]] = []
    for index, item in enumerate(raw_cases, start=1):
        if isinstance(item, str):
            cases.append(
                {
                    "id": f"custom_{index}",
                    "kind": "in_domain",
                    "question": item,
                    "expected_path_fragments": [],
                }
            )
        elif isinstance(item, dict) and isinstance(item.get("question"), str):
            cases.append(item)
        else:
            raise ValueError(f"Invalid question entry at position {index}")
    return cases


def call_chat(
    endpoint: str,
    question: str,
    timeout: float,
) -> tuple[int | None, dict[str, Any] | None, float, str | None]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({"message": question}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload, time.perf_counter() - started, None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, None, time.perf_counter() - started, body
    except (OSError, ValueError) as exc:
        return (
            None,
            None,
            time.perf_counter() - started,
            f"{type(exc).__name__}: {exc}",
        )


def evaluate_case(
    case: dict[str, Any],
    status: int | None,
    payload: dict[str, Any] | None,
    duration: float,
    error: str | None,
) -> dict[str, Any]:
    answer = payload.get("response") if isinstance(payload, dict) else None
    sources = payload.get("sources") if isinstance(payload, dict) else None
    valid_sources = sources if isinstance(sources, list) else []
    source_paths = [
        item.get("relative_path")
        for item in valid_sources
        if isinstance(item, dict) and isinstance(item.get("relative_path"), str)
    ]
    expected = case.get("expected_path_fragments", [])
    expected_family = (
        not expected
        or any(
            fragment in path
            for fragment in expected
            for path in source_paths
        )
    )
    is_out_of_domain = case.get("kind") == "out_of_domain"
    passed = (
        status == 200
        and isinstance(answer, str)
        and bool(answer.strip())
        and isinstance(sources, list)
        and (
            len(valid_sources) == 0
            if is_out_of_domain
            else len(valid_sources) > 0 and expected_family
        )
    )
    return {
        "id": case.get("id"),
        "kind": case.get("kind", "in_domain"),
        "question": case["question"],
        "http_status": status,
        "duration_seconds": round(duration, 6),
        "response": answer,
        "response_length": len(answer) if isinstance(answer, str) else 0,
        "source_count": len(valid_sources),
        "source_names": [
            item.get("document_name")
            for item in valid_sources
            if isinstance(item, dict)
        ],
        "source_paths": source_paths,
        "sources": valid_sources,
        "expected_source_family_present": expected_family,
        "answer_non_empty": isinstance(answer, str) and bool(answer.strip()),
        "citations_present": bool(valid_sources),
        "passed": passed,
        "error": error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the real KnowledgeChat HTTP RAG pipeline."
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--questions", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "work/experiments/lmcache/sprint_3_5/"
            "live_vllm_rag_results.json"
        ),
    )
    parser.add_argument("--timeout", type=float, default=180)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        cases = load_cases(args.questions)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2

    endpoint = f"{args.base_url.rstrip('/')}/api/v1/chat"
    results = []
    for case in cases:
        status, payload, duration, error = call_chat(
            endpoint, case["question"], args.timeout
        )
        result = evaluate_case(case, status, payload, duration, error)
        results.append(result)
        print(
            f"{result['id']}: status={status} passed={result['passed']} "
            f"duration={result['duration_seconds']}s "
            f"sources={result['source_count']}"
        )

    report = {
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved: {args.output}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
