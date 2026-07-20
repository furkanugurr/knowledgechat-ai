"""Build and run the resumable, live 165-guide Antikor validation gate."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import run_antikor_42_validation as base
from app.knowledge.evidence import has_usable_evidence, is_placeholder_line
from app.core.config import get_settings
from app.embedding.ollama_embedding import OllamaEmbeddingProvider
from app.prompt.prompt_builder import PromptBuilder
from app.providers.ollama_provider import OllamaProvider
from app.retrieval.turkish_lexical import TurkishLexicalNormalizer
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_provider import ChromaVectorStoreProvider

ROOT = Path(os.getenv("VALIDATION_REPOSITORY_ROOT", base.ROOT))
GUIDES = ROOT / "knowledge_base" / "guides" / "antikor_v2"
DATASET = HERE / "antikor_165_validation_dataset.json"
OUTPUT = ROOT / "work" / "visual_guide_extraction" / "final_165"
INVENTORY = OUTPUT / "guide_inventory.json"
PROGRESS = OUTPUT / "progress.json"
LOG = OUTPUT / "run.log"
FAILED = OUTPUT / "failed_cases.json"
REPORT = OUTPUT / "final_validation.json"
SUMMARY = OUTPUT / "validation_summary.md"
NAVIGATION_AUDIT = OUTPUT / "navigation_failure_audit.json"

FAST_PATH_INTENTS = {"navigation", "first_action", "field_listing", "field_purpose"}
SOURCE = re.compile(r"^-\s+Sayfa:\s+(\S+)", re.MULTILINE)

# Nine original critical cases are owned by the established validator.
CRITICAL = base.CRITICAL

# The six collision/placeholder regressions retained from Batch 1.
BATCH_1_REGRESSIONS = (
    ("b1r-hotspot-open", "Hotspot İşlemleri bölümündeki Hotspot Açık Hedefler ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/hotspot-islemleri/hotspot-acik-hedefler.md", "Alanlar"),
    ("b1r-hotspot-settings", "Hotspot İşlemleri bölümündeki Hotspot Ayarları ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/hotspot-islemleri/hotspot-ayarlari.md", "Alanlar"),
    ("b1r-ethernet-live", "Anlık Gözlem bölümündeki Ethernet Bant Genişlikleri ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/anlik-gozlem/trafik-istatistikleri.md", "Alanlar"),
    ("b1r-ethernet-performance", "Performans bölümündeki Ethernet Bant Genişlikleri ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/performans/ethernet-bant-genislikler.md", "Alanlar"),
    ("b1r-dynamic-nat", "Dinamik NAT nasıl oluşturulur?", "procedure", "guides/antikor_v2/nat/dinamik-nat.md", "Kullanım adımları"),
    ("b1r-nat-first", "Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?", "first_action", "guides/antikor_v2/nat/dinamik-nat.md", "Görünür kontroller"),
)

# Six representative cases from the second and third promoted batches.
BATCH_23_REGRESSIONS = (
    ("b23r-antispam", "Eposta Güvenliği bölümündeki Antispam Ayarları ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/eposta-guvenligi/antispam-ayarlari.md", "Alanlar"),
    ("b23r-announcement", "Duyuru ve Form Yönetimi bölümündeki Duyuru Girişi ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/duyuru-ve-form-yonetimi/duyuru-girisi.md", "Alanlar"),
    ("b23r-antivirus", "Web Filtreleme bölümündeki Antivirüs Ayarları ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/web-filtreleme/antivirus-ayarlari.md", "Alanlar"),
    ("b23r-dns", "Sistem Ayarları bölümündeki DNS Ayarları ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/sistem-ayarlari/dns-ayarlari.md", "Alanlar"),
    ("b23r-report", "Raporlar bölümündeki Rapor Ayarları ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/raporlar/rapor-ayarlari.md", "Alanlar"),
    ("b23r-service", "Tanımlar bölümündeki Servis Tanımları ekranında yeni kayıt için ilk hangi butona basmalıyım?", "first_action", "guides/antikor_v2/tanimlar/servis-tanimlari.md", "Görünür kontroller"),
)


def atomic_json(path: Path, value: Any) -> None:
    """Persist JSON atomically so Ctrl+C never leaves a partial progress file."""
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


def evidence_terms(intent: str, section: str, title: str) -> list[str]:
    if intent == "navigation":
        return base.menu_terms(section, title)
    if intent == "first_action":
        additions = [item for item in base.labels(section) if "ekle" in item.casefold()]
        return additions[:1] or base.labels(section)[:1]
    if intent == "field_listing":
        return [item for item in base.labels(section) if item != "#"][:3]
    if intent == "field_purpose":
        return [item for item in base.labels(section) if item != "#"][:1]
    if intent == "procedure":
        values = base.procedure_labels(section)
        return list(dict.fromkeys(values[:2] + values[-1:]))
    return base.scope_terms(title, section)


def supported_navigation_paths(section: str) -> list[str]:
    """Return exact breadcrumbs or short screen labels supported by the source."""
    values = re.findall(r"`([^`]+)`", section) or base.LIST.findall(section)
    paths: list[str] = []
    for value in values:
        cleaned = value.strip().strip("`")
        if not cleaned or "->" in cleaned or is_placeholder_line(cleaned):
            continue
        if " > " in cleaned or (
            len(cleaned) <= 100 and not cleaned.endswith(".")
            and " tıkl" not in cleaned.casefold()
        ):
            if cleaned not in paths:
                paths.append(cleaned)
    return paths


def attach_navigation_expectations(
    case: dict[str, Any], section: str,
) -> dict[str, Any]:
    if case["intent"] == "navigation":
        paths = supported_navigation_paths(section)
        if not paths:
            raise RuntimeError(f"Navigation case has no supported path: {case['id']}")
        case["accepted_navigation_paths"] = paths
    return case


def inspect_guides() -> list[dict[str, Any]]:
    """Validate all promoted documents and return their deterministic inventory."""
    paths = sorted(GUIDES.rglob("*.md"))
    if len(paths) != 165:
        raise RuntimeError(f"Expected 165 Markdown guides, found {len(paths)}")
    relative_paths: set[str] = set()
    slugs: set[str] = set()
    inventory: list[dict[str, Any]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        title_match = base.TITLE.search(text)
        source_match = SOURCE.search(text)
        relative = path.relative_to(ROOT / "knowledge_base").as_posix()
        slug = path.stem.casefold()
        if not title_match:
            raise RuntimeError(f"Missing title: {relative}")
        if not source_match:
            raise RuntimeError(f"Missing source URL: {relative}")
        if relative in relative_paths:
            raise RuntimeError(f"Duplicate relative path: {relative}")
        if slug in slugs:
            raise RuntimeError(f"Duplicate slug: {slug}")
        if any(is_placeholder_line(line) for line in text.splitlines()):
            raise RuntimeError(f"Placeholder evidence remains: {relative}")
        sections = base.sections(text)
        usable = [
            name for name, value in sections.items()
            if name not in {"Kaynak bilgisi", "Uyarılar"} and has_usable_evidence(value)
        ]
        if not usable:
            raise RuntimeError(f"No usable evidence section: {relative}")
        relative_paths.add(relative)
        slugs.add(slug)
        inventory.append({
            "title": title_match.group(1).strip(),
            "category": path.relative_to(GUIDES).parts[0],
            "slug": path.stem,
            "relative_path": relative,
            "source_url": source_match.group(1),
            "available_sections": list(sections),
            "usable_evidence_sections": usable,
        })
    return inventory


def generated_case(number: int, item: dict[str, Any], title_counts: Counter[str]) -> dict[str, Any]:
    path = ROOT / "knowledge_base" / item["relative_path"]
    sections = base.sections(path.read_text(encoding="utf-8"))
    title = item["title"]
    identity = f"{item['category']} bölümündeki {title}" if title_counts[title.casefold()] > 1 else title
    choices: list[tuple[str, str, str]] = []
    menu = sections.get("Menü yolu", "")
    if has_usable_evidence(menu) and supported_navigation_paths(menu):
        choices.append(("navigation", "Menü yolu", f"{identity} için kaynakta verilen menü yolu nedir?"))
    controls = sections.get("Görünür kontroller", "")
    if has_usable_evidence(controls) and any("ekle" in label.casefold() for label in base.labels(controls)):
        choices.append(("first_action", "Görünür kontroller", f"{identity} ekranında yeni kayıt için ilk hangi butona basmalıyım?"))
    fields = sections.get("Alanlar", "")
    field_labels = [label for label in base.labels(fields) if label != "#"]
    if has_usable_evidence(fields) and field_labels:
        choices.append(("field_listing", "Alanlar", f"{identity} ekranında hangi alanlar bulunur?"))
        choices.append(("field_purpose", "Alanlar", f"{identity} ekranındaki {field_labels[0]} alanı ne işe yarar?"))
    steps = sections.get("Kullanım adımları", "")
    if has_usable_evidence(steps) and base.procedure_labels(steps):
        choices.append(("procedure", "Kullanım adımları", f"{identity} nasıl yapılandırılır?"))
    scope = sections.get("Kapsam", "")
    if has_usable_evidence(scope):
        choices.append(("general_information", "Kapsam", f"{identity} nedir?"))
    order = ("navigation", "first_action", "field_listing", "field_purpose", "procedure", "general_information")
    selected = next((choice for intent in order for choice in choices if choice[0] == intent), None)
    if selected is None:
        raise RuntimeError(f"Cannot build evidence-based case: {item['relative_path']}")
    intent, section_name, question = selected
    section = sections[section_name]
    required = evidence_terms(intent, section, title)
    if not required:
        raise RuntimeError(f"No supported key terms for: {item['relative_path']}")
    case = base.make(
        f"g165-{number:03d}", question, intent, item["relative_path"], section_name,
        required, [], section, "generated",
    )
    return attach_navigation_expectations(case, section)


def regression_case(definition: tuple[str, str, str, str, str], kind: str) -> dict[str, Any]:
    case_id, question, intent, relative, section_name = definition
    path = ROOT / "knowledge_base" / relative
    sections = base.sections(path.read_text(encoding="utf-8"))
    source = sections.get(section_name, "")
    required = evidence_terms(intent, source, path.stem)
    if not required:
        raise RuntimeError(f"Regression has no evidence terms: {case_id}")
    case = base.make(case_id, question, intent, relative, section_name, required, [], source, kind)
    return attach_navigation_expectations(case, source)


def build_dataset() -> dict[str, Any]:
    inventory = inspect_guides()
    counts = Counter(item["title"].casefold() for item in inventory)
    generated = [generated_case(number, item, counts) for number, item in enumerate(inventory, 1)]
    critical = []
    for case_id, question, intent, relative, section_name, required, forbidden in CRITICAL:
        source = base.sections((ROOT / "knowledge_base" / relative).read_text(encoding="utf-8")).get(section_name, "")
        case = base.make(case_id, question, intent, relative, section_name, required, forbidden, source, "critical_regression")
        critical.append(attach_navigation_expectations(case, source))
    cases = generated + critical
    cases.extend(regression_case(item, "batch_1_regression") for item in BATCH_1_REGRESSIONS)
    cases.extend(regression_case(item, "batch_2_3_regression") for item in BATCH_23_REGRESSIONS)
    if len(cases) != 186 or len({case["id"] for case in cases}) != 186:
        raise RuntimeError(f"Expected 186 unique cases, built {len(cases)}")
    data = {
        "schema_version": 2,
        "generated_without_llm": True,
        "guide_count": len(inventory),
        "question_count": len(cases),
        "regression_count": 21,
        "inventory": inventory,
        "cases": cases,
        "source_incomplete_guides": [],
    }
    atomic_json(INVENTORY, {"guide_count": len(inventory), "guides": inventory})
    atomic_json(DATASET, data)
    return data


def evaluate_case(
    test: dict[str, Any], response: Any, trace: Any, duration: float,
) -> dict[str, Any]:
    """Apply the established checks plus alternative-path navigation scoring."""
    result = base.evaluate(test, response, trace, duration)
    if test["intent"] != "navigation":
        return result
    normalizer = TurkishLexicalNormalizer()
    normalized_answer = normalizer.phrase(result["generated_answer"])
    accepted = test.get("accepted_navigation_paths", [])
    supported = [
        path for path in accepted
        if normalizer.phrase(path) in normalized_answer
    ]
    answer_breadcrumbs = [
        line.strip(" -*`") for line in result["generated_answer"].splitlines()
        if " > " in line
    ]
    unsupported_paths = [
        path for path in answer_breadcrumbs
        if not any(normalizer.phrase(path) == normalizer.phrase(item) for item in accepted)
    ]
    result["checks"]["accepted_navigation_path"] = supported[:1]
    result["checks"]["unsupported_navigation_paths"] = unsupported_paths
    result["checks"]["required_terms_missing"] = [] if supported else accepted
    result["checks"]["unsupported_claim"] = bool(
        result["checks"]["unsupported_claim"] or unsupported_paths
    )
    checks = result["checks"]
    result["passed"] = bool(
        checks["source_correct"] and checks["section_correct"]
        and checks["intent_correct"] and supported and not unsupported_paths
        and not checks["forbidden_terms_found"] and not checks["false_limitation"]
        and not checks["unsupported_claim"] and not checks["unrelated_topic"]
    )
    if result["passed"]:
        result["root_cause_classification"] = None
        result["recommended_fix_type"] = None
    return result


def load_results() -> dict[str, dict[str, Any]]:
    if not REPORT.exists():
        return {}
    try:
        return {
            item["id"]: item
            for item in json.loads(REPORT.read_text(encoding="utf-8")).get("results", [])
        }
    except (OSError, ValueError, KeyError):
        return {}


def write_navigation_audit(data: dict[str, Any]) -> dict[str, Any]:
    """Classify the original failed navigation cases against source evidence."""
    if not REPORT.exists():
        return {"navigation_cases_audited": 0, "cases": []}
    previous = json.loads(REPORT.read_text(encoding="utf-8"))
    failed_navigation = [
        item for item in previous.get("results", [])
        if not item.get("passed") and item.get("intent") == "navigation"
    ]
    if not failed_navigation and NAVIGATION_AUDIT.exists():
        return json.loads(NAVIGATION_AUDIT.read_text(encoding="utf-8-sig"))
    cases_by_id = {case["id"]: case for case in data["cases"]}
    normalizer = TurkishLexicalNormalizer()
    audited: list[dict[str, Any]] = []
    for result in failed_navigation:
        current = cases_by_id[result["id"]]
        accepted = current.get("accepted_navigation_paths", [])
        normalized_answer = normalizer.phrase(result.get("generated_answer", ""))
        supported = [
            path for path in accepted
            if normalizer.phrase(path) in normalized_answer
        ]
        if not result.get("checks", {}).get("source_correct", False) or not result.get("checks", {}).get("section_correct", False):
            classification = "D. actual retrieval or section-selection error"
            production_change = True
        elif supported:
            classification = "A. validation expectation too strict"
            production_change = False
        elif accepted:
            classification = "B. navigation fast-path incomplete"
            production_change = True
        else:
            classification = "C. source Markdown incomplete"
            production_change = False
        audited.append({
            "case_id": result["id"], "question": result["question"],
            "expected_guide": result["expected_relative_path"],
            "expected_section": result["expected_section"],
            "source_supported_menu_paths": accepted,
            "previous_required_terms": result.get("required_terms", []),
            "actual_answer": result.get("generated_answer", ""),
            "citations": result.get("returned_citations", []),
            "classification": classification,
            "corrected_expectation": {
                "accept_any_exact_source_supported_path": accepted,
                "reject_unsupported_breadcrumbs": True,
            },
            "production_code_must_change": production_change,
        })
    counts = Counter(item["classification"].split(".", 1)[0] for item in audited)
    report = {
        "navigation_cases_audited": len(audited),
        "classification_counts": dict(counts), "cases": audited,
    }
    atomic_json(NAVIGATION_AUDIT, report)
    return report


def sprint26_target_ids(data: dict[str, Any]) -> set[str]:
    """Return failed cases plus bounded passing navigation/collision controls."""
    previous = json.loads(REPORT.read_text(encoding="utf-8"))
    failed = {item["id"] for item in previous["results"] if not item["passed"]}
    passing_navigation = [
        item["id"] for item in previous["results"]
        if item["passed"] and item["intent"] == "navigation"
    ][:5]
    collision_paths = {
        "guides/antikor_v2/raporlar/rapor-gecmisi.md",
        "guides/antikor_v2/raporlar/rapor-sablonu-yonetimi.md",
    }
    collision_controls = {
        case["id"] for case in data["cases"]
        if case["expected_relative_path"] in collision_paths
        and case["case_kind"] == "generated"
    }
    return failed | set(passing_navigation) | collision_controls


def summary_for(data: dict[str, Any], results: list[dict[str, Any]], runtime: dict[str, Any]) -> dict[str, Any]:
    summary = base.summarize(data, results, runtime)
    generated = [item for item in results if item["case_kind"] == "generated"]
    all_cases_done = len(results) == data["question_count"]
    summary["final_165_ready"] = bool(
        all_cases_done
        and len(generated) == 165
        and summary["passed_questions"] == data["question_count"]
        and summary["wrong_source_count"] == 0
        and summary["wrong_section_count"] == 0
        and summary["false_limitation_count"] == 0
        and summary["unsupported_claim_count"] == 0
        and summary["unrelated_topic_count"] == 0
        and summary["citation_error_count"] == 0
        and summary["citation_correctness_percent"] == 100.0
    )
    return summary


def write_state(data: dict[str, Any], completed: dict[str, dict[str, Any]], started: float,
                current: dict[str, Any] | None, settings: Any) -> None:
    ordered = [completed[case["id"]] for case in data["cases"] if case["id"] in completed]
    elapsed = perf_counter() - started
    durations = [item.get("response_duration_seconds", 0.0) for item in ordered]
    average = sum(durations) / len(durations) if durations else 0.0
    remaining = max(data["question_count"] - len(ordered), 0)
    runtime = {
        "chat_model": settings.chat_model,
        "embedding_model": settings.embedding_model,
        "vector_collection_name": settings.vector_collection_name,
        "vector_db_path": str(settings.vector_db_path),
        "candidate_k": settings.retrieval_candidate_k,
        "context_max_chunks": settings.chat_context_max_chunks,
        "elapsed_seconds": round(elapsed, 3),
    }
    summary = summary_for(data, ordered, runtime)
    progress = {
        "total": data["question_count"],
        "completed": len(ordered),
        "passed": sum(item["passed"] for item in ordered),
        "failed": sum(not item["passed"] for item in ordered),
        "current_case": current["id"] if current else None,
        "current_guide": current["expected_relative_path"] if current else None,
        "answer_mode": completed.get(current["id"], {}).get("diagnostics", {}).get("answer_mode") if current else None,
        "fast_path_count": sum(item.get("diagnostics", {}).get("answer_mode") == "deterministic_fast_path" for item in ordered),
        "llm_count": sum(bool(item.get("diagnostics", {}).get("ollama_called")) for item in ordered),
        "retry_count": sum(max(item.get("attempt_count", 1) - 1, 0) for item in ordered),
        "timeout_count": sum(sum(attempt.get("error_type") == "LLMProviderTimeoutError" for attempt in item.get("attempts", [])) for item in ordered),
        "average_duration_seconds": round(average, 3),
        "elapsed_seconds": round(elapsed, 3),
        "estimated_remaining_seconds": round(average * remaining, 3),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    atomic_json(PROGRESS, progress)
    atomic_json(FAILED, {"failed_count": progress["failed"], "cases": [item for item in ordered if not item["passed"]]})
    atomic_json(REPORT, {"summary": summary, "inventory": data["inventory"], "results": ordered})
    lines = ["# Final 165-Guide Validation", ""] + [
        f"- {key}: {value}" for key, value in summary.items() if key != "runtime"
    ]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def run_live(data: dict[str, Any], args: argparse.Namespace) -> int:
    settings = get_settings()
    llm = OllamaProvider(settings.ollama_host, settings.chat_model, settings.request_timeout, settings.chat_max_tokens)
    embedding = OllamaEmbeddingProvider(settings.ollama_host, settings.embedding_model, settings.request_timeout)
    await llm.start()
    await embedding.start()
    vector = ChromaVectorStoreProvider(settings.vector_db_path, settings.vector_collection_name)
    retrieval = RetrievalService(EmbeddingService(embedding), vector, settings.retrieval_candidate_k, settings.chat_context_max_chunks, settings.retrieval_min_similarity)
    trace = base.Trace(retrieval)
    chat = ChatService(llm, PromptBuilder.from_defaults(), retrieval, settings.retrieval_min_similarity)
    timing = base.StageTiming(chat)
    completed = load_results() if (args.resume or args.retry_failed or args.case_id) else {}
    cases = list(data["cases"])
    if args.sprint26_targeted:
        cases = [case for case in cases if case["id"] in args.target_ids]
    if args.start_index:
        cases = cases[args.start_index - 1:]
    if args.case_id:
        cases = [case for case in cases if case["id"] == args.case_id]
        if not cases:
            raise RuntimeError(f"Unknown case id: {args.case_id}")
    if args.retry_failed:
        failed_ids = {case_id for case_id, result in completed.items() if not result["passed"]}
        cases = [case for case in cases if case["id"] in failed_ids]
    elif args.resume:
        cases = [case for case in cases if case["id"] not in completed or not completed[case["id"]]["passed"]]
    if args.max_cases is not None:
        cases = cases[:args.max_cases]
    started = perf_counter()
    write_state(data, completed, started, None, settings)
    try:
        for position, test in enumerate(cases, 1):
            attempts: list[dict[str, Any]] = []
            result: dict[str, Any] | None = None
            log(f"[{position}/{len(cases)}] START {test['id']} {test['question']}")
            write_state(data, completed, started, test, settings)
            for attempt_number in range(1, 4):
                trace.reset()
                timing.reset()
                tick = perf_counter()
                try:
                    response = await chat.generate_response(test["question"])
                    duration = perf_counter() - tick
                    result = evaluate_case(test, response, trace, duration)
                    result["diagnostics"] = dict(chat.last_diagnostics)
                    fast_path_violation = bool(
                        test["intent"] in FAST_PATH_INTENTS
                        and chat.last_diagnostics.get("evidence_sufficient")
                        and chat.last_diagnostics.get("ollama_called")
                    )
                    result["checks"]["fast_path_without_ollama"] = not fast_path_violation
                    if fast_path_violation:
                        result["passed"] = False
                        result["root_cause_classification"] = "D. Fast-path regression"
                        result["recommended_fix_type"] = "deterministic-answer review"
                    attempts.append({
                        "attempt": attempt_number, "error_type": None,
                        "duration_seconds": round(duration, 3), "passed": result["passed"],
                        **timing.snapshot(duration), **chat.last_diagnostics,
                    })
                    break
                except Exception as exc:  # noqa: BLE001 - diagnostics must persist every runtime failure
                    duration = perf_counter() - tick
                    transient = base.transient_error(exc)
                    attempts.append({
                        "attempt": attempt_number, "error_type": type(exc).__name__,
                        "error": str(exc), "duration_seconds": round(duration, 3),
                        "transient": transient, "passed": False,
                        "retrieved_sources": [base.chunk(item) for item in trace.initial],
                        **timing.snapshot(duration), **chat.last_diagnostics,
                    })
                    if not transient or attempt_number == 3:
                        break
                    log(f"RETRY {test['id']} attempt={attempt_number + 1} error={type(exc).__name__}")
                    await asyncio.sleep(1.0)
            if result is None:
                last = attempts[-1]
                checks = {
                    "source_correct": False, "section_correct": False, "intent_correct": False,
                    "required_terms_missing": test["required_terms"], "forbidden_terms_found": [],
                    "false_limitation": False, "unsupported_claim": False, "unknown_ui_labels": [],
                    "unrelated_topic": False, "procedure_order_correct": False,
                    "citation_correct": False, "fast_path_without_ollama": False,
                }
                result = {
                    **test, "detected_intent": None, "initial_semantic_candidates": last.get("retrieved_sources", []),
                    "reranked_candidates": [], "selected_document": None, "selected_sections": [],
                    "generated_answer": "", "returned_citations": [],
                    "response_duration_seconds": last["duration_seconds"], "checks": checks,
                    "passed": False, "root_cause_classification": "F. Runtime failure",
                    "recommended_fix_type": "runtime review", "error": f"{last['error_type']}: {last.get('error', '')}",
                    "diagnostics": {key: last.get(key) for key in ("answer_mode", "evidence_sufficient", "ollama_called")},
                }
            result["attempt_count"] = len(attempts)
            result["attempts"] = attempts
            result["final_result"] = "passed" if result["passed"] else "failed"
            completed[test["id"]] = result
            write_state(data, completed, started, test, settings)
            log(f"[{position}/{len(cases)}] {'PASS' if result['passed'] else 'FAIL'} {test['id']} {result['response_duration_seconds']}s")
            if args.stop_on_failure and not result["passed"]:
                break
    except KeyboardInterrupt:
        log("Interrupted safely; use --resume to continue.")
    finally:
        write_state(data, completed, started, None, settings)
        await embedding.close()
        await llm.close()
    final = json.loads(REPORT.read_text(encoding="utf-8"))["summary"]
    return 0 if final.get("final_165_ready") else 1


def validate_dataset(data: dict[str, Any]) -> None:
    if data["guide_count"] != 165 or data["question_count"] != 186:
        raise RuntimeError("Dataset size gate failed")
    generated = [case for case in data["cases"] if case["case_kind"] == "generated"]
    if len(generated) != 165 or len({case["expected_relative_path"] for case in generated}) != 165:
        raise RuntimeError("Every guide must have exactly one generated validation case")
    for case in data["cases"]:
        if not case["required_terms"] or not (ROOT / "knowledge_base" / case["expected_relative_path"]).exists():
            raise RuntimeError(f"Invalid validation case: {case['id']}")


def initialize_output_files(data: dict[str, Any]) -> None:
    """Create non-authoritative not-started files without replacing live progress."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    initial_progress = {
        "total": data["question_count"], "completed": 0, "passed": 0, "failed": 0,
        "current_case": None, "current_guide": None, "answer_mode": None,
        "fast_path_count": 0, "llm_count": 0, "retry_count": 0, "timeout_count": 0,
        "average_duration_seconds": 0.0, "elapsed_seconds": 0.0,
        "estimated_remaining_seconds": None, "status": "not_started",
        "updated_at": datetime.now(UTC).isoformat(),
    }
    initial_summary = {
        "total_guides": 165, "total_questions": data["question_count"],
        "passed_questions": 0, "failed_questions": 0,
        "citation_correctness_percent": 0.0, "final_165_ready": False,
        "status": "not_started",
    }
    if not PROGRESS.exists():
        atomic_json(PROGRESS, initial_progress)
    if not FAILED.exists():
        atomic_json(FAILED, {"failed_count": 0, "cases": []})
    if not REPORT.exists():
        atomic_json(REPORT, {"summary": initial_summary, "inventory": data["inventory"], "results": []})
    if not SUMMARY.exists():
        SUMMARY.write_text(
            "# Final 165-Guide Validation\n\n- status: not_started\n- final_165_ready: false\n",
            encoding="utf-8",
        )
    if not LOG.exists():
        LOG.write_text("", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the resumable live validation gate for all 165 Antikor guides.")
    parser.add_argument("--resume", action="store_true", help="Continue and skip completed successful cases.")
    parser.add_argument("--start-index", type=int, default=1, help="Start from this one-based dataset index.")
    parser.add_argument("--case-id", help="Run one validation case by id.")
    parser.add_argument("--retry-failed", action="store_true", help="Run only cases currently recorded as failed.")
    parser.add_argument("--dry-run", action="store_true", help="Build and validate files without connecting to runtime services.")
    parser.add_argument("--max-cases", type=int, help="Limit selected cases (useful for a smoke test).")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop safely after the first scored failure.")
    parser.add_argument("--sprint26-targeted", action="store_true", help="Run the Sprint 26 affected and control cases only.")
    return parser.parse_args()


def main() -> int:
    global REPORT, PROGRESS, FAILED, SUMMARY, LOG
    args = parse_args()
    data = build_dataset()
    validate_dataset(data)
    audit = write_navigation_audit(data)
    if args.sprint26_targeted:
        args.target_ids = sprint26_target_ids(data)
        REPORT = OUTPUT / "sprint26_targeted_validation.json"
        PROGRESS = OUTPUT / "sprint26_targeted_progress.json"
        FAILED = OUTPUT / "sprint26_targeted_failures.json"
        SUMMARY = OUTPUT / "sprint26_targeted_summary.md"
        LOG = OUTPUT / "sprint26_targeted.log"
    if args.dry_run:
        initialize_output_files(data)
        print(f"DRY RUN OK guides={data['guide_count']} cases={data['question_count']} regressions={data['regression_count']} audited={audit['navigation_cases_audited']}")
        return 0
    return asyncio.run(run_live(data, args))


if __name__ == "__main__":
    raise SystemExit(main())
