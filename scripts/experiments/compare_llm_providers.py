#!/usr/bin/env python3
"""Compare Ollama and vLLM chat APIs without changing application state."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def post_json(
    url: str,
    payload: dict[str, Any],
    timeout: float,
) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body, time.perf_counter() - started


def run_provider(name: str, args: argparse.Namespace) -> dict[str, Any]:
    if name == "ollama":
        url = f"{args.ollama_url.rstrip('/')}/api/generate"
        payload = {
            "model": args.ollama_model,
            "prompt": args.prompt,
            "stream": False,
            "options": {"temperature": 0, "num_predict": args.max_tokens},
        }
        extractor = lambda body: body.get("response")
        model = args.ollama_model
    else:
        url = f"{args.vllm_url.rstrip('/')}/v1/chat/completions"
        payload = {
            "model": args.vllm_model,
            "messages": [{"role": "user", "content": args.prompt}],
            "stream": False,
            "temperature": 0,
            "max_tokens": args.max_tokens,
        }
        extractor = (
            lambda body: body.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
        model = args.vllm_model

    try:
        body, duration = post_json(url, payload, args.timeout)
        answer = extractor(body)
        return {
            "provider": name,
            "model": model,
            "success": isinstance(answer, str) and bool(answer.strip()),
            "duration_seconds": round(duration, 6),
            "answer": answer,
            "error": None,
        }
    except (OSError, ValueError, urllib.error.HTTPError) as exc:
        return {
            "provider": name,
            "model": model,
            "success": False,
            "duration_seconds": None,
            "answer": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one identical prompt against Ollama and vLLM."
    )
    parser.add_argument("--prompt", default="VLAN kavramını iki cümlede açıkla.")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--ollama-model", default="gemma3:12b")
    parser.add_argument("--vllm-url", default="http://localhost:8001")
    parser.add_argument("--vllm-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = {
        "prompt": args.prompt,
        "results": [
            run_provider("ollama", args),
            run_provider("vllm", args),
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if all(item["success"] for item in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
