"""Economical 39-guide Batch 2 validation plus 15 regressions."""

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

ROOT = Path(os.getenv("VALIDATION_REPOSITORY_ROOT", base.ROOT))
BATCH = Path(os.getenv(
    "VALIDATION_BATCH_ROOT", ROOT / "work" / "visual_guide_extraction" / "batch_2"
))
REPORT = BATCH / "post_promotion_validation.json"

REPRESENTATIVE = (
    ("r-hotspot-open", "Hotspot İşlemleri bölümündeki Hotspot Açık Hedefler ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/hotspot-islemleri/hotspot-acik-hedefler.md", "Alanlar"),
    ("r-hotspot-settings", "Hotspot İşlemleri bölümündeki Hotspot Ayarları ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/hotspot-islemleri/hotspot-ayarlari.md", "Alanlar"),
    ("r-ethernet-live", "Anlık Gözlem bölümündeki Ethernet Bant Genişlikleri ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/anlik-gozlem/trafik-istatistikleri.md", "Alanlar"),
    ("r-ethernet-performance", "Performans bölümündeki Ethernet Bant Genişlikleri ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/performans/ethernet-bant-genislikler.md", "Alanlar"),
    ("r-domain", "DNS Denetimi bölümündeki Domain Tanımları nedir?", "general_information", "guides/antikor_v2/dns-denetimi/domain-tanimlari.md", "Kapsam"),
    ("r-lldp", "Anlık Gözlem bölümündeki LLDP Durumu ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/anlik-gozlem/lldp-durumu.md", "Alanlar"),
)


def evidence_terms(intent: str, section: str, title: str) -> list[str]:
    if intent == "navigation":
        return base.menu_terms(section, title)
    if intent == "field_listing":
        return [term for term in base.labels(section) if term != "#"][:3]
    if intent == "first_action":
        return re.findall(r"`([^`]*\bEkle\b[^`]*)`", section, re.IGNORECASE)[:1]
    if intent == "procedure":
        terms = base.procedure_labels(section)
        return list(dict.fromkeys(terms[:2] + terms[-1:]))
    return base.scope_terms(title, section)


def build_dataset() -> dict:
    promotion = json.loads((BATCH / "promotion_manifest.json").read_text(encoding="utf-8"))
    inventory: list[dict] = []
    cases: list[dict] = []
    procedure_count = 0
    for number, item in enumerate(promotion["guides"], 1):
        path = ROOT / str(item["destination_knowledge_base_path"])
        available = base.sections(path.read_text(encoding="utf-8"))
        relative = path.relative_to(ROOT / "knowledge_base").as_posix()
        title = str(item["title"])
        identity = f"{item['category']} bölümündeki {title}"
        inventory.append({
            "title": title, "category": item["category"], "relative_path": relative,
            "source_url": item["source_url"], "available_sections": list(available),
            "usable_evidence_sections": [
                name for name, value in available.items()
                if name not in {"Kaynak bilgisi", "Uyarılar"} and has_usable_evidence(value)
            ],
        })
        choices: list[tuple[str, str, str]] = []
        menu = available.get("Menü yolu", "")
        menu_labels = re.findall(r"`([^`]+)`", menu)
        safe_menu = (
            len(menu_labels) == 1
            and title.casefold() in menu_labels[0].casefold()
        )
        if has_usable_evidence(menu) and safe_menu:
            choices.append(("navigation", "Menü yolu", f"{identity} için kaynakta verilen menü yolu nedir?"))
        if has_usable_evidence(available.get("Alanlar", "")) and base.labels(available["Alanlar"]):
            choices.append(("field_listing", "Alanlar", f"{identity} ekranında hangi alanlar bulunur?"))
        controls = available.get("Görünür kontroller", "")
        if has_usable_evidence(controls) and any("ekle" in x.casefold() for x in base.labels(controls)):
            choices.append(("first_action", "Görünür kontroller", f"{identity} ekranında yeni kayıt için ilk hangi butona basmalıyım?"))
        steps = available.get("Kullanım adımları", "")
        if procedure_count < 8 and has_usable_evidence(steps) and base.procedure_labels(steps):
            choices.append(("procedure", "Kullanım adımları", f"{identity} nasıl yapılandırılır?"))
        if not choices:
            choices.append(("general_information", "Kapsam", f"{identity} nedir?"))
        preference = ("navigation", "field_listing", "first_action")[number % 3]
        selected = next((choice for choice in choices if choice[0] == preference), choices[0])
        intent, section_name, question = selected
        if intent == "procedure":
            procedure_count += 1
        section = available.get(section_name, "")
        required = evidence_terms(intent, section, title)
        if not required:
            raise RuntimeError(f"Generated question has no evidence terms: {relative}")
        cases.append(base.make(
            f"b2-{number:02d}", question, intent, relative, section_name,
            required, [], section, "batch_2_generated",
        ))

    for cid, question, intent, relative, section_name, required, forbidden in base.CRITICAL:
        source = base.sections((ROOT / "knowledge_base" / relative).read_text(encoding="utf-8")).get(section_name, "")
        cases.append(base.make(cid, question, intent, relative, section_name, required, forbidden, source, "critical_regression"))
    for cid, question, intent, relative, section_name in REPRESENTATIVE:
        path = ROOT / "knowledge_base" / relative
        source = base.sections(path.read_text(encoding="utf-8")).get(section_name, "")
        required = evidence_terms(intent, source, path.stem)
        cases.append(base.make(cid, question, intent, relative, section_name, required, [], source, "batch_1_regression"))
    if len(cases) != 54:
        raise RuntimeError(f"Expected 54 validation questions, built {len(cases)}")
    if sum(case["intent"] == "procedure" for case in cases[:39]) > 8:
        raise RuntimeError("Batch 2 procedure budget exceeded")
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
    batch = [item for item in results if item["case_kind"] == "batch_2_generated"]
    regression = [item for item in results if item["case_kind"] != "batch_2_generated"]
    summary = report["summary"]
    classifications = Counter()
    for item in results:
        if item["passed"]:
            continue
        attempts = item.get("attempts", [])
        if attempts and attempts[-1].get("transient"):
            kind = "transient timeout"
        elif not item["checks"]["source_correct"]:
            kind = "retrieval issue"
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
        len(batch) == 39 and all(item["passed"] for item in batch)
        and len(regression) == 15 and all(item["passed"] for item in regression)
        and summary["wrong_source_count"] == 0
        and summary["wrong_section_count"] == 0
        and summary["false_limitation_count"] == 0
        and summary["unsupported_claim_count"] == 0
        and summary["unrelated_topic_count"] == 0
        and summary["citation_error_count"] == 0
        and summary["citation_correctness_percent"] == 100.0
    )
    report["sprint24"] = {
        "batch_2_passed": sum(item["passed"] for item in batch),
        "batch_2_failed": sum(not item["passed"] for item in batch),
        "regression_passed": sum(item["passed"] for item in regression),
        "regression_failed": sum(not item["passed"] for item in regression),
        "failure_classifications": dict(classifications),
        "batch_2_production_ready": gate,
    }
    return report


def main() -> int:
    BATCH.mkdir(parents=True, exist_ok=True)
    base.ROOT = ROOT
    base.GUIDES = ROOT / "knowledge_base" / "guides" / "antikor_v2"
    base.OUT = BATCH
    base.REPORT = REPORT
    full_data = build_dataset()
    retry_ids = set(filter(None, os.getenv("VALIDATION_ONLY_IDS", "").split(",")))
    if retry_ids:
        data = {**full_data, "cases": [case for case in full_data["cases"] if case["id"] in retry_ids]}
        data["question_count"] = len(data["cases"])
        original = json.loads(REPORT.read_text(encoding="utf-8"))
        retry_report = BATCH / "post_promotion_validation_retry.json"
        base.REPORT = retry_report
        print(f"corrected validation questions={data['question_count']}", flush=True)
        asyncio.run(base.run(data, no_resume=True, max_attempts=2))
        retry = json.loads(retry_report.read_text(encoding="utf-8"))
        replacements = {item["id"]: item for item in retry["results"]}
        combined = [replacements.get(item["id"], item) for item in original["results"]]
        runtime = dict(original["summary"]["runtime"])
        runtime["elapsed_seconds"] = round(
            runtime["elapsed_seconds"] + retry["summary"]["runtime"]["elapsed_seconds"], 3
        )
        report = {
            "summary": base.summarize(full_data, combined, runtime),
            "inventory": full_data["inventory"], "results": combined,
            "validation_question_corrections": sorted(retry_ids),
        }
    else:
        data = full_data
        print(f"dataset guides={data['guide_count']} questions={data['question_count']}", flush=True)
        asyncio.run(base.run(data, no_resume=True, max_attempts=2))
        report = json.loads(REPORT.read_text(encoding="utf-8"))
    report = classify_and_gate(report)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["sprint24"], ensure_ascii=False), flush=True)
    return 0 if report["sprint24"]["batch_2_production_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
