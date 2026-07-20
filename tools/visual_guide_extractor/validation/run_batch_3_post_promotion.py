"""Economical final-batch validation: 38 new guides plus 15 regressions."""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import run_antikor_42_validation as base
from app.knowledge.evidence import has_usable_evidence
from run_batch_2_post_promotion import REPRESENTATIVE, evidence_terms

ROOT = Path(os.getenv("VALIDATION_REPOSITORY_ROOT", base.ROOT))
BATCH = Path(os.getenv(
    "VALIDATION_BATCH_ROOT", ROOT / "work" / "visual_guide_extraction" / "batch_3"
))
REPORT = BATCH / "post_promotion_validation.json"


def build_dataset() -> dict:
    promotion = json.loads((BATCH / "promotion_manifest.json").read_text(encoding="utf-8"))
    inventory: list[dict] = []
    cases: list[dict] = []
    procedures = 0
    for number, item in enumerate(promotion["guides"], 1):
        path = ROOT / str(item["destination_knowledge_base_path"])
        sections = base.sections(path.read_text(encoding="utf-8"))
        relative = path.relative_to(ROOT / "knowledge_base").as_posix()
        title = str(item["title"])
        identity = f"{item['category']} bölümündeki {title}"
        usable = [
            name for name, value in sections.items()
            if name not in {"Kaynak bilgisi", "Uyarılar"} and has_usable_evidence(value)
        ]
        inventory.append({
            "title": title, "category": item["category"], "relative_path": relative,
            "source_url": item["source_url"], "available_sections": list(sections),
            "usable_evidence_sections": usable,
        })
        choices: list[tuple[str, str, str]] = []
        menu = sections.get("Menü yolu", "")
        menu_labels = re.findall(r"`([^`]+)`", menu)
        if (
            has_usable_evidence(menu) and len(menu_labels) == 1
            and title.casefold() in menu_labels[0].casefold()
        ):
            choices.append(("navigation", "Menü yolu", f"{identity} için kaynakta verilen menü yolu nedir?"))
        fields = sections.get("Alanlar", "")
        if has_usable_evidence(fields) and base.labels(fields):
            choices.append(("field_listing", "Alanlar", f"{identity} ekranında hangi alanlar bulunur?"))
        controls = sections.get("Görünür kontroller", "")
        if has_usable_evidence(controls) and re.search(r"`[^`]*\bEkle\b[^`]*`", controls, re.IGNORECASE):
            choices.append(("first_action", "Görünür kontroller", f"{identity} ekranında yeni kayıt için ilk hangi butona basmalıyım?"))
        steps = sections.get("Kullanım adımları", "")
        if procedures < 8 and has_usable_evidence(steps) and base.procedure_labels(steps):
            choices.append(("procedure", "Kullanım adımları", f"{identity} nasıl yapılandırılır?"))
        if not choices:
            choices.append(("general_information", "Kapsam", f"{identity} nedir?"))
        preference = ("navigation", "field_listing", "first_action")[number % 3]
        intent, section_name, question = next(
            (choice for choice in choices if choice[0] == preference), choices[0]
        )
        if intent == "procedure":
            procedures += 1
        section = sections.get(section_name, "")
        required = evidence_terms(intent, section, title)
        if not required:
            raise RuntimeError(f"Generated question has no evidence terms: {relative}")
        cases.append(base.make(
            f"b3-{number:02d}", question, intent, relative, section_name,
            required, [], section, "batch_3_generated",
        ))
    for cid, question, intent, relative, section_name, required, forbidden in base.CRITICAL:
        source = base.sections((ROOT / "knowledge_base" / relative).read_text(encoding="utf-8")).get(section_name, "")
        cases.append(base.make(
            cid, question, intent, relative, section_name, required, forbidden,
            source, "critical_regression",
        ))
    for cid, question, intent, relative, section_name in REPRESENTATIVE:
        path = ROOT / "knowledge_base" / relative
        source = base.sections(path.read_text(encoding="utf-8")).get(section_name, "")
        required = evidence_terms(intent, source, path.stem)
        cases.append(base.make(
            cid, question, intent, relative, section_name, required, [],
            source, "representative_regression",
        ))
    if len(cases) != 53:
        raise RuntimeError(f"Expected 53 questions, built {len(cases)}")
    if sum(case["intent"] == "procedure" for case in cases[:38]) > 8:
        raise RuntimeError("Procedure budget exceeded")
    return {
        "schema_version": 1, "generated_without_llm": True,
        "guide_count": len(inventory), "question_count": len(cases),
        "inventory": inventory, "cases": cases,
        "source_incomplete_guides": [
            item["relative_path"] for item in inventory
            if item["usable_evidence_sections"] == ["Kapsam"]
        ],
    }


def classify_and_gate(report: dict) -> dict:
    results = report["results"]
    batch = [item for item in results if item["case_kind"] == "batch_3_generated"]
    regression = [item for item in results if item["case_kind"] != "batch_3_generated"]
    summary = report["summary"]
    classifications: Counter[str] = Counter()
    for item in results:
        if item["passed"]:
            continue
        attempts = item.get("attempts", [])
        if attempts and attempts[-1].get("transient"):
            kind = "transient timeout"
        elif not item["checks"]["source_correct"]:
            expected_name = Path(item["expected_relative_path"]).stem.casefold()
            actual_name = Path(item.get("selected_document") or "").stem.casefold()
            kind = "duplicate-title collision" if expected_name == actual_name else "retrieval issue"
        elif not item["checks"]["section_correct"]:
            kind = "section-selection issue"
        elif not item["checks"]["intent_correct"]:
            kind = "validation question issue"
        elif not item["checks"]["citation_correct"]:
            kind = "citation issue"
        else:
            kind = "answer-generation issue"
        item["failure_classification"] = kind
        classifications[kind] += 1
    gate = (
        len(batch) == 38 and all(item["passed"] for item in batch)
        and len(regression) == 15 and all(item["passed"] for item in regression)
        and summary["wrong_source_count"] == 0
        and summary["wrong_section_count"] == 0
        and summary["false_limitation_count"] == 0
        and summary["unsupported_claim_count"] == 0
        and summary["unrelated_topic_count"] == 0
        and summary["citation_error_count"] == 0
        and summary["citation_correctness_percent"] == 100.0
    )
    report["sprint25"] = {
        "batch_3_passed": sum(item["passed"] for item in batch),
        "batch_3_failed": sum(not item["passed"] for item in batch),
        "regression_passed": sum(item["passed"] for item in regression),
        "regression_failed": sum(not item["passed"] for item in regression),
        "failure_classifications": dict(classifications),
        "batch_3_production_ready": gate,
    }
    return report


def main() -> int:
    BATCH.mkdir(parents=True, exist_ok=True)
    base.ROOT = ROOT
    base.GUIDES = ROOT / "knowledge_base" / "guides" / "antikor_v2"
    base.OUT = BATCH
    base.REPORT = REPORT
    full = build_dataset()
    only_ids = set(filter(None, os.getenv("VALIDATION_ONLY_IDS", "").split(",")))
    if only_ids:
        data = {**full, "cases": [case for case in full["cases"] if case["id"] in only_ids]}
        data["question_count"] = len(data["cases"])
        original = json.loads(REPORT.read_text(encoding="utf-8"))
        retry_path = BATCH / "post_promotion_validation_retry.json"
        base.REPORT = retry_path
        asyncio.run(base.run(data, no_resume=True, max_attempts=2))
        retry = json.loads(retry_path.read_text(encoding="utf-8"))
        replacements = {item["id"]: item for item in retry["results"]}
        combined = [replacements.get(item["id"], item) for item in original["results"]]
        runtime = dict(original["summary"]["runtime"])
        runtime["elapsed_seconds"] = round(
            runtime["elapsed_seconds"] + retry["summary"]["runtime"]["elapsed_seconds"], 3
        )
        report = {
            "summary": base.summarize(full, combined, runtime),
            "inventory": full["inventory"], "results": combined,
            "validation_question_corrections": sorted(only_ids),
        }
    else:
        print(f"dataset guides={full['guide_count']} questions={full['question_count']}", flush=True)
        asyncio.run(base.run(full, no_resume=True, max_attempts=2))
        report = json.loads(REPORT.read_text(encoding="utf-8"))
    report = classify_and_gate(report)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["sprint25"], ensure_ascii=False), flush=True)
    return 0 if report["sprint25"]["batch_3_production_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
