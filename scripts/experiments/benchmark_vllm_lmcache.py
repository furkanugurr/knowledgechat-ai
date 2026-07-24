#!/usr/bin/env python3
"""Controlled baseline/LMCache benchmark without starting external services."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from test_representative_vllm_models import ADDITIONAL_COMPLEX_CASE
from test_live_vllm_rag import DEFAULT_CASES, evaluate_case, load_cases

DEFAULT_MODEL = "Qwen/Qwen2.5-3B-Instruct-AWQ"


def parse_sse(lines: Iterable[bytes], started: float) -> dict[str, Any]:
    first_token: float | None = None
    text_parts: list[str] = []
    usage: dict[str, Any] = {}
    for raw in lines:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(event.get("usage"), dict):
            usage = event["usage"]
        choices = event.get("choices")
        if not isinstance(choices, list) or not choices:
            continue
        delta = choices[0].get("delta", {})
        content = delta.get("content") if isinstance(delta, dict) else None
        if isinstance(content, str) and content:
            first_token = first_token or time.perf_counter() - started
            text_parts.append(content)
    return {"text": "".join(text_parts), "ttft_seconds": first_token, "usage": usage}


def stream_vllm(
    base_url: str, model: str, question: str, timeout: float
) -> dict[str, Any]:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": question}],
        "temperature": 0,
        "max_tokens": 768,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        parsed = parse_sse(response, started)
        duration = time.perf_counter() - started
        usage = parsed["usage"]
        return {
            "http_status": response.status,
            "duration_seconds": round(duration, 6),
            "ttft_seconds": (
                round(parsed["ttft_seconds"], 6)
                if parsed["ttft_seconds"] is not None
                else None
            ),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "cache_hit_tokens": usage.get("prompt_tokens_details", {}).get(
                "cached_tokens"
            ),
            "answer_length": len(parsed["text"]),
            "answer_sha256": hashlib.sha256(
                parsed["text"].encode("utf-8")
            ).hexdigest(),
            "error": None,
        }


def call_rag(base_url: str, case: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/v1/chat",
        data=json.dumps(
            {"message": case["question"]}, ensure_ascii=False
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return evaluate_case(
                case, response.status, payload, time.perf_counter() - started, None
            )
    except (OSError, ValueError, urllib.error.HTTPError) as exc:
        status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
        return evaluate_case(
            case, status, None, time.perf_counter() - started, str(exc)
        )


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    durations = [
        item["duration_seconds"] for item in results if item.get("passed")
    ]
    ttfts = [
        item["ttft_seconds"]
        for item in results
        if item.get("passed") and item.get("ttft_seconds") is not None
    ]
    warm = [
        item["duration_seconds"]
        for item in results
        if item.get("passed") and item["temperature"] == "warm"
    ]
    return {
        "requests": len(results),
        "successful": sum(bool(item.get("passed")) for item in results),
        "failed": sum(not item.get("passed") for item in results),
        "average_duration_seconds": statistics.fmean(durations) if durations else None,
        "warm_average_duration_seconds": statistics.fmean(warm) if warm else None,
        "warm_median_duration_seconds": statistics.median(warm) if warm else None,
        "warm_p95_duration_seconds": (
            sorted(warm)[max(0, int(len(warm) * 0.95) - 1)] if warm else None
        ),
        "average_ttft_seconds": statistics.fmean(ttfts) if ttfts else None,
        "median_ttft_seconds": statistics.median(ttfts) if ttfts else None,
        "p95_ttft_seconds": (
            sorted(ttfts)[max(0, int(len(ttfts) * 0.95) - 1)] if ttfts else None
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("baseline", "lmcache"))
    parser.add_argument("--endpoint", required=True, choices=("direct", "rag"))
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--questions", type=Path)
    parser.add_argument("--runs", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.runs < 1:
        raise SystemExit("--runs must be at least 1")
    cases = load_cases(args.questions)
    if args.questions is None:
        cases = [*DEFAULT_CASES[:5], ADDITIONAL_COMPLEX_CASE, *DEFAULT_CASES[5:]]
    results: list[dict[str, Any]] = []
    for run_index in range(args.runs):
        temperature = "cold" if run_index == 0 else "warm"
        for case in cases:
            started_at = datetime.now(UTC).isoformat()
            try:
                if args.endpoint == "direct":
                    raw = stream_vllm(
                        args.base_url, args.model, case["question"], args.timeout
                    )
                    raw["passed"] = raw["http_status"] == 200 and raw["answer_length"] > 0
                else:
                    raw = call_rag(args.base_url, case, args.timeout)
                    raw["ttft_seconds"] = None
                raw.update(
                    {
                        "request_id": f"{args.mode}-{args.endpoint}-{run_index + 1}-{case['id']}",
                        "question_id": case["id"],
                        "kind": case.get("kind", "in_domain"),
                        "run": run_index + 1,
                        "temperature": temperature,
                        "timestamp": started_at,
                        "model": args.model,
                        "lmcache_enabled": args.mode == "lmcache",
                    }
                )
            except (OSError, ValueError, urllib.error.HTTPError) as exc:
                raw = {
                    "request_id": f"{args.mode}-{args.endpoint}-{run_index + 1}-{case['id']}",
                    "question_id": case["id"],
                    "kind": case.get("kind", "in_domain"),
                    "run": run_index + 1,
                    "temperature": temperature,
                    "timestamp": started_at,
                    "model": args.model,
                    "lmcache_enabled": args.mode == "lmcache",
                    "http_status": getattr(exc, "code", None),
                    "duration_seconds": None,
                    "ttft_seconds": None,
                    "passed": False,
                    "error": str(exc),
                }
            results.append(raw)
            print(
                raw["request_id"],
                f"passed={raw['passed']}",
                f"duration={raw.get('duration_seconds')}",
                f"ttft={raw.get('ttft_seconds')}",
            )
    report = {
        "schema_version": 1,
        "mode": args.mode,
        "endpoint": args.endpoint,
        "model": args.model,
        "lmcache_enabled": args.mode == "lmcache",
        "runs": args.runs,
        "results": results,
        "summary": summarize(results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
