"""Manual live validation for the deterministic out-of-domain gate."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import run_antikor_42_validation as validation_base
from app.core.config import get_settings
from app.embedding.ollama_embedding import OllamaEmbeddingProvider
from app.prompt.prompt_builder import PromptBuilder
from app.providers.ollama_provider import OllamaProvider
from app.retrieval.domain_relevance import DomainRelevanceGate
from app.services.chat_service import ChatService, NO_RELEVANT_CONTEXT_RESPONSE
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_provider import ChromaVectorStoreProvider

ROOT = Path(os.getenv("VALIDATION_REPOSITORY_ROOT", validation_base.ROOT))
DATASET = HERE / "out_of_domain_validation_dataset.json"
REGRESSION_DATASET = HERE / "antikor_165_validation_dataset.json"
OUTPUT = ROOT / "work" / "visual_guide_extraction" / "out_of_domain"
PROGRESS = OUTPUT / "progress.json"
LOG = OUTPUT / "run.log"
FAILED = OUTPUT / "failed_cases.json"
REPORT = OUTPUT / "final_validation.json"
SUMMARY = OUTPUT / "validation_summary.md"
FALSE_REJECTION_AUDIT = OUTPUT / "false_rejection_audit.json"

UNRELATED_QUESTIONS = (
    "hamburger faydalı mı",
    "yarın hava nasıl",
    "matematik sınavına nasıl çalışılır",
    "futbol maçı kaç kaç bitti",
    "bana yemek tarifi ver",
    "İstanbul'da gezilecek yerler nereler",
    "telefonumun şarjı neden çabuk bitiyor",
    "kahve nasıl hazırlanır",
    "hangi filmi izlemeliyim",
    "borsada hangi hisseyi almalıyım",
    "bugün dolar kaç lira",
    "sağlıklı uyku kaç saat olmalı",
    "arabama hangi motor yağı uygun",
    "İngilizce öğrenmenin en kolay yolu nedir",
    "kedim neden sürekli miyavlıyor",
)
FAST_PATH_INTENTS = {"navigation", "first_action", "field_listing"}


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def log(message: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(UTC).isoformat()} {message}"
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(message, flush=True)


def build_dataset() -> dict[str, Any]:
    regression = json.loads(REGRESSION_DATASET.read_text(encoding="utf-8"))
    regression_cases = [
        case for case in regression["cases"] if case["case_kind"] != "generated"
    ]
    if len(regression_cases) != 21:
        raise RuntimeError(f"Expected 21 regressions, found {len(regression_cases)}")
    cases: list[dict[str, Any]] = []
    for number, question in enumerate(UNRELATED_QUESTIONS, 1):
        cases.append({
            "id": f"ood-{number:02d}", "question": question,
            "case_kind": "out_of_domain", "expected_domain_relevant": False,
            "expected_sources": "empty", "expected_llm_called": False,
            "expected_no_answer": True, "expected_relative_path": None,
            "expected_section": None,
        })
    for case in regression_cases:
        cases.append({
            "id": f"reg-{case['id']}", "question": case["question"],
            "case_kind": "in_domain_regression", "intent": case["intent"],
            "expected_domain_relevant": True, "expected_sources": "supporting_guide",
            "expected_llm_called": case["intent"] not in FAST_PATH_INTENTS,
            "expected_no_answer": False,
            "expected_relative_path": case["expected_relative_path"],
            "expected_section": case["expected_section"],
        })
    data = {
        "schema_version": 1, "generated_without_llm": True,
        "out_of_domain_count": len(UNRELATED_QUESTIONS),
        "in_domain_regression_count": len(regression_cases),
        "case_count": len(cases), "cases": cases,
    }
    atomic_json(DATASET, data)
    return data


def validate_dataset(data: dict[str, Any]) -> None:
    if data["out_of_domain_count"] < 15:
        raise RuntimeError("At least 15 unrelated questions are required")
    if data["in_domain_regression_count"] != 21 or data["case_count"] != 36:
        raise RuntimeError("Expected 15 unrelated plus 21 regression cases")
    if len({case["id"] for case in data["cases"]}) != data["case_count"]:
        raise RuntimeError("Case ids must be unique")
    for case in data["cases"]:
        if case["expected_domain_relevant"]:
            path = ROOT / "knowledge_base" / case["expected_relative_path"]
            if not path.exists() or not case["expected_section"]:
                raise RuntimeError(f"Invalid regression evidence: {case['id']}")


def load_results() -> dict[str, dict[str, Any]]:
    if not REPORT.exists():
        return {}
    try:
        payload = json.loads(REPORT.read_text(encoding="utf-8"))
        return {item["id"]: item for item in payload.get("results", [])}
    except (OSError, ValueError, KeyError):
        return {}


def summarize(data: dict[str, Any], results: list[dict[str, Any]], elapsed: float) -> dict[str, Any]:
    passed = sum(item["passed"] for item in results)
    unrelated = [item for item in results if item["case_kind"] == "out_of_domain"]
    regression = [item for item in results if item["case_kind"] == "in_domain_regression"]
    complete = len(results) == data["case_count"]
    return {
        "total_cases": data["case_count"], "completed_cases": len(results),
        "passed_cases": passed, "failed_cases": len(results) - passed,
        "out_of_domain_passed": sum(item["passed"] for item in unrelated),
        "in_domain_regressions_passed": sum(item["passed"] for item in regression),
        "false_accept_count": sum(
            item["actual_domain_relevant"] for item in unrelated
        ),
        "false_rejection_count": sum(
            not item["actual_domain_relevant"] for item in regression
        ),
        "unrelated_llm_call_count": sum(
            item["ollama_called"] for item in unrelated
        ),
        "unrelated_citation_count": sum(
            len(item["citations"]) for item in unrelated
        ),
        "elapsed_seconds": round(elapsed, 3),
        "out_of_domain_ready": bool(complete and passed == data["case_count"]),
    }


def persist(data: dict[str, Any], completed: dict[str, dict[str, Any]],
            started: float, current: dict[str, Any] | None) -> None:
    ordered = [completed[case["id"]] for case in data["cases"] if case["id"] in completed]
    elapsed = perf_counter() - started
    summary = summarize(data, ordered, elapsed)
    durations = [item["duration_seconds"] for item in ordered]
    progress = {
        "total": data["case_count"], "completed": len(ordered),
        "passed": summary["passed_cases"], "failed": summary["failed_cases"],
        "current_case": current["id"] if current else None,
        "current_question": current["question"] if current else None,
        "average_duration_seconds": round(sum(durations) / max(len(durations), 1), 3),
        "elapsed_seconds": round(elapsed, 3),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    atomic_json(PROGRESS, progress)
    atomic_json(FAILED, {
        "failed_count": summary["failed_cases"],
        "cases": [item for item in ordered if not item["passed"]],
    })
    atomic_json(REPORT, {"summary": summary, "results": ordered})
    SUMMARY.write_text(
        "# Out-of-Domain Validation\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in summary.items())
        + "\n", encoding="utf-8",
    )


def evaluate(case: dict[str, Any], response: Any, diagnostics: dict[str, Any],
             duration: float) -> dict[str, Any]:
    citations = [source.model_dump() for source in response.sources]
    paths = {item["relative_path"] for item in citations}
    sections = {item["section_title"] for item in citations}
    domain_relevant = bool(diagnostics.get("domain_relevant"))
    ollama_called = bool(diagnostics.get("ollama_called"))
    no_answer = response.response == NO_RELEVANT_CONTEXT_RESPONSE
    source_ok = (
        not citations if case["expected_sources"] == "empty"
        else case["expected_relative_path"] in paths
    )
    section_ok = (
        True if case["expected_section"] is None
        else case["expected_section"] in sections
    )
    checks = {
        "domain_relevance_correct": domain_relevant == case["expected_domain_relevant"],
        "source_behavior_correct": source_ok,
        "section_correct": section_ok,
        "llm_behavior_correct": ollama_called == case["expected_llm_called"],
        "no_answer_behavior_correct": no_answer == case["expected_no_answer"],
    }
    return {
        **case, "actual_domain_relevant": domain_relevant,
        "no_answer_reason": diagnostics.get("no_answer_reason"),
        "top_similarity": diagnostics.get("top_similarity"),
        "lexical_overlap": diagnostics.get("lexical_overlap"),
        "guide_confidence": diagnostics.get("guide_confidence"),
        "confidence_tier": diagnostics.get("confidence_tier"),
        "entity_signal": diagnostics.get("entity_signal"),
        "ui_label_signal": diagnostics.get("ui_label_signal"),
        "category_signal": diagnostics.get("category_signal"),
        "lexical_signal": diagnostics.get("lexical_signal"),
        "semantic_signal": diagnostics.get("semantic_signal"),
        "guide_agreement_signal": diagnostics.get("guide_agreement_signal"),
        "final_decision_reason": diagnostics.get("final_decision_reason"),
        "detected_guide_entity": diagnostics.get("resolved_guide"),
        "selected_source_before_rejection": diagnostics.get("dominant_path"),
        "selected_guide": diagnostics.get("selected_guide"),
        "selected_sections": diagnostics.get("selected_sections", []),
        "answer": response.response, "citations": citations,
        "answer_mode": diagnostics.get("answer_mode"),
        "ollama_called": ollama_called, "duration_seconds": round(duration, 3),
        "checks": checks, "passed": all(checks.values()),
    }


async def write_false_rejection_audit(
    retrieval: RetrievalService,
    settings: Any,
    prior_results: dict[str, dict[str, Any]],
) -> None:
    """Capture retrieval signals omitted from the initial failed report."""
    failed = [
        item for item in prior_results.values()
        if item.get("case_kind") == "in_domain_regression"
        and not item.get("actual_domain_relevant", True)
    ]
    if not failed:
        # After recovery, retain the original audit population: accepted
        # regressions that the former unconditional semantic veto rejected.
        failed = [
            item for item in prior_results.values()
            if item.get("case_kind") == "in_domain_regression"
            and item.get("actual_domain_relevant")
            and float(item.get("top_similarity") or 0.0)
            < settings.out_of_domain_min_similarity
        ]
    if not failed:
        return
    gate = DomainRelevanceGate(
        settings.out_of_domain_min_similarity,
        settings.out_of_domain_min_lexical_overlap,
        settings.out_of_domain_min_guide_confidence,
    )
    audited: list[dict[str, Any]] = []
    for item in failed:
        result = await retrieval.retrieve(item["question"])
        focused = ChatService._focus_context(item["question"], result.chunks)
        diagnostics = retrieval.last_diagnostics
        decision = gate.evaluate(item["question"], focused, diagnostics)
        if decision.entity_signal:
            group = "strong exact entity but low semantic score"
        elif decision.ui_label_signal:
            group = "strong UI-label match but low semantic score"
        elif decision.category_signal and decision.lexical_signal:
            group = "strong category/domain vocabulary but low semantic score"
        elif decision.guide_agreement_signal:
            group = "correct dominant guide selected but threshold rejected"
        else:
            group = "genuinely weak/ambiguous question"
        audited.append({
            "id": item["id"], "question": item["question"],
            "expected_guide": item.get("expected_relative_path"),
            "detected_guide_entity": diagnostics.get("resolved_guide"),
            "category_match": decision.category_signal,
            "ui_label_match": decision.ui_label_signal,
            "lexical_overlap": decision.lexical_overlap,
            "top_similarity": decision.top_similarity,
            "guide_confidence": decision.guide_confidence,
            "selected_source_before_rejection": diagnostics.get("dominant_path"),
            "no_answer_reason": (
                item.get("no_answer_reason")
                or "semantic_similarity_below_threshold"
            ),
            "classification": group,
        })
    groups: dict[str, int] = {}
    for item in audited:
        groups[item["classification"]] = groups.get(item["classification"], 0) + 1
    atomic_json(FALSE_REJECTION_AUDIT, {
        "audited_case_count": len(audited), "groups": groups, "cases": audited,
    })


async def run(data: dict[str, Any], args: argparse.Namespace) -> int:
    settings = get_settings()
    llm = OllamaProvider(settings.ollama_host, settings.chat_model, settings.request_timeout, settings.chat_max_tokens)
    embedding = OllamaEmbeddingProvider(settings.ollama_host, settings.embedding_model, settings.request_timeout)
    await llm.start()
    await embedding.start()
    vector = ChromaVectorStoreProvider(settings.vector_db_path, settings.vector_collection_name)
    retrieval = RetrievalService(
        EmbeddingService(embedding), vector, settings.retrieval_candidate_k,
        settings.chat_context_max_chunks, settings.retrieval_min_similarity,
    )
    chat = ChatService(
        llm, PromptBuilder.from_defaults(), retrieval,
        settings.retrieval_min_similarity,
        settings.out_of_domain_min_similarity,
        settings.out_of_domain_min_lexical_overlap,
        settings.out_of_domain_min_guide_confidence,
        domain_gate_enabled=True,
    )
    prior_results = load_results()
    await write_false_rejection_audit(retrieval, settings, prior_results)
    completed = prior_results if (args.resume or args.retry_failed or args.case_id) else {}
    cases = list(data["cases"])
    if args.case_id:
        cases = [case for case in cases if case["id"] == args.case_id]
        if not cases:
            raise RuntimeError(f"Unknown case id: {args.case_id}")
    elif args.retry_failed:
        failed_ids = {case_id for case_id, item in completed.items() if not item["passed"]}
        cases = [case for case in cases if case["id"] in failed_ids]
    elif args.resume:
        cases = [case for case in cases if case["id"] not in completed]
    if args.max_cases is not None:
        cases = cases[:args.max_cases]
    started = perf_counter()
    persist(data, completed, started, None)
    try:
        for position, case in enumerate(cases, 1):
            log(f"[{position}/{len(cases)}] START {case['id']} {case['question']}")
            persist(data, completed, started, case)
            tick = perf_counter()
            try:
                response = await chat.generate_response(case["question"])
                result = evaluate(case, response, chat.last_diagnostics, perf_counter() - tick)
            except Exception as exc:  # noqa: BLE001 - persist every live failure
                result = {
                    **case, "actual_domain_relevant": False,
                    "no_answer_reason": "runtime_error", "top_similarity": None,
                    "lexical_overlap": None, "guide_confidence": None,
                    "selected_guide": None, "selected_sections": [], "answer": "",
                    "citations": [], "answer_mode": None, "ollama_called": False,
                    "duration_seconds": round(perf_counter() - tick, 3),
                    "checks": {}, "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            completed[case["id"]] = result
            persist(data, completed, started, case)
            log(f"[{position}/{len(cases)}] {'PASS' if result['passed'] else 'FAIL'} {case['id']} {result['duration_seconds']}s")
    except KeyboardInterrupt:
        log("Interrupted safely; use --resume to continue.")
    finally:
        persist(data, completed, started, None)
        await embedding.close()
        await llm.close()
    selected_failed = [completed[case["id"]] for case in cases if case["id"] in completed and not completed[case["id"]]["passed"]]
    return 0 if not selected_failed else 1


def initialize(data: dict[str, Any]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not PROGRESS.exists():
        atomic_json(PROGRESS, {"total": data["case_count"], "completed": 0, "passed": 0, "failed": 0, "status": "not_started"})
    if not FAILED.exists():
        atomic_json(FAILED, {"failed_count": 0, "cases": []})
    if not REPORT.exists():
        atomic_json(REPORT, {"summary": {"out_of_domain_ready": False, "status": "not_started"}, "results": []})
    if not SUMMARY.exists():
        SUMMARY.write_text("# Out-of-Domain Validation\n\n- status: not_started\n", encoding="utf-8")
    if not LOG.exists():
        LOG.write_text("", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live out-of-domain and in-domain regression validation.")
    parser.add_argument("--resume", action="store_true", help="Continue after completed cases.")
    parser.add_argument("--case-id", help="Run one case by id.")
    parser.add_argument("--retry-failed", action="store_true", help="Run only recorded failed cases.")
    parser.add_argument("--dry-run", action="store_true", help="Validate files without runtime calls.")
    parser.add_argument("--max-cases", type=int, help="Limit selected cases.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = build_dataset()
    validate_dataset(data)
    if args.dry_run:
        initialize(data)
        print(f"DRY RUN OK cases={data['case_count']} unrelated={data['out_of_domain_count']} regressions={data['in_domain_regression_count']}")
        return 0
    return asyncio.run(run(data, args))


if __name__ == "__main__":
    raise SystemExit(main())
