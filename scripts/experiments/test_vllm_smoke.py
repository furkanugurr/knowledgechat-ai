from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_URL = "http://localhost:8001"
TIMEOUT_SECONDS = 120
OUTPUT_PATH = (
    Path(__file__).resolve().parents[2]
    / "work"
    / "experiments"
    / "lmcache"
    / "sprint_2"
    / "vllm_smoke_results.json"
)
REQUESTS = [
    "Merhaba. Tek kelimeyle yanıt ver.",
    "Antikor bir ağ güvenliği ürünü müdür? Tek cümleyle cevapla.",
    "Antikor bir ağ güvenliği ürünü müdür? Tek cümleyle cevapla.",
]


def request_json(
    path: str,
    *,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any], float]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = json.loads(response.read().decode("utf-8"))
        return response.status, body, time.perf_counter() - started


def main() -> int:
    results: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "success": False,
        "models_endpoint": {},
        "requests": [],
    }

    try:
        status, models_body, models_duration = request_json("/v1/models")
        model_entries = models_body.get("data", [])
        if status != 200 or not model_entries:
            raise RuntimeError("/v1/models did not return a usable model")
        model_name = str(model_entries[0]["id"])
        results["models_endpoint"] = {
            "http_status": status,
            "duration_seconds": round(models_duration, 6),
            "model_name": model_name,
        }

        for index, prompt in enumerate(REQUESTS, start=1):
            status, body, duration = request_json(
                "/v1/chat/completions",
                payload={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 64,
                    "temperature": 0.0,
                },
            )
            text = str(body["choices"][0]["message"]["content"])
            if status != 200 or not text.strip():
                raise RuntimeError(f"request {index} returned an empty response")
            results["requests"].append(
                {
                    "index": index,
                    "http_status": status,
                    "duration_seconds": round(duration, 6),
                    "response_text_length": len(text),
                    "model_name": model_name,
                    "response_text": text,
                }
            )

        results["success"] = True
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        return_code = 0
    except (
        KeyError,
        RuntimeError,
        TimeoutError,
        urllib.error.HTTPError,
        urllib.error.URLError,
        json.JSONDecodeError,
    ) as exc:
        results["error"] = f"{type(exc).__name__}: {exc}"
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        return_code = 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Results: {OUTPUT_PATH}")
    return return_code


if __name__ == "__main__":
    sys.exit(main())
