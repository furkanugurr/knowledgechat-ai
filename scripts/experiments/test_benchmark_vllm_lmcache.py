import io
import json
import time

from benchmark_vllm_lmcache import parse_sse, summarize


def test_parse_sse_records_ttft_usage_and_text():
    started = time.perf_counter()
    lines = [
        b'data: {"choices":[{"delta":{"content":"Merhaba"}}]}\n',
        b'data: {"choices":[{"delta":{"content":" dunya"}}]}\n',
        b'data: {"choices":[],"usage":{"prompt_tokens":12,"completion_tokens":2,"prompt_tokens_details":{"cached_tokens":8}}}\n',
        b"data: [DONE]\n",
    ]
    result = parse_sse(lines, started)
    assert result["text"] == "Merhaba dunya"
    assert result["ttft_seconds"] is not None
    assert result["usage"]["prompt_tokens_details"]["cached_tokens"] == 8


def test_parse_sse_ignores_malformed_events():
    result = parse_sse([b"event: message\n", b"data: not-json\n", b"data: [DONE]\n"], time.perf_counter())
    assert result == {"text": "", "ttft_seconds": None, "usage": {}}


def test_summary_separates_warm_results():
    report = summarize(
        [
            {"passed": True, "duration_seconds": 2.0, "ttft_seconds": 1.0, "temperature": "cold"},
            {"passed": True, "duration_seconds": 1.0, "ttft_seconds": 0.5, "temperature": "warm"},
            {"passed": False, "duration_seconds": None, "ttft_seconds": None, "temperature": "warm"},
        ]
    )
    assert report["requests"] == 3
    assert report["successful"] == 2
    assert report["failed"] == 1
    assert report["warm_average_duration_seconds"] == 1.0


def test_json_schema_contains_no_secret_fields():
    payload = {
        "schema_version": 1,
        "mode": "baseline",
        "endpoint": "direct",
        "results": [],
        "summary": {},
    }
    serialized = json.dumps(payload)
    assert "api_key" not in serialized
    assert "authorization" not in serialized.casefold()
