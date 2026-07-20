"""Economical live validation for promoted Batch 1 guides plus regressions."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import run_antikor_42_validation as base
from app.knowledge.evidence import has_usable_evidence


ROOT = Path(os.getenv("VALIDATION_REPOSITORY_ROOT", base.ROOT))
BATCH = Path(os.getenv(
    "VALIDATION_BATCH_ROOT",
    ROOT / "work" / "visual_guide_extraction" / "batch_1",
))
REPORT = BATCH / "post_promotion_validation.json"


def targeted_dataset() -> dict:
    """Build the bounded collision, NAT, and material-placeholder gate."""
    definitions = (
        ("t-hotspot-open", "Hotspot Açık Hedefler ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/hotspot-islemleri/hotspot-acik-hedefler.md", "Alanlar"),
        ("t-hotspot-settings", "Hotspot Ayarları ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/hotspot-islemleri/hotspot-ayarlari.md", "Alanlar"),
        ("t-ethernet-live", "Anlık Gözlem bölümündeki Ethernet Bant Genişlikleri ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/anlik-gozlem/trafik-istatistikleri.md", "Alanlar"),
        ("t-ethernet-performance", "Performans bölümündeki Ethernet Bant Genişlikleri ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/performans/ethernet-bant-genislikler.md", "Alanlar"),
        ("t-dynamic", "Dinamik NAT nasıl oluşturulur?", "procedure", "guides/antikor_v2/nat/dinamik-nat.md", "Kullanım adımları"),
        ("t-nat-first", "Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?", "first_action", "guides/antikor_v2/nat/dinamik-nat.md", "Görünür kontroller"),
        ("t-static", "Statik NAT nasıl oluşturulur?", "procedure", "guides/antikor_v2/nat/statik-nat.md", "Kullanım adımları"),
        ("t-domain", "Domain Tanımları nedir?", "general_information", "guides/antikor_v2/dns-denetimi/domain-tanimlari.md", "Kapsam"),
        ("t-lldp", "LLDP Durumu ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/anlik-gozlem/lldp-durumu.md", "Alanlar"),
        ("t-interface", "Network Arayüzleri Bant Genişiliği Monitörü ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/anlik-gozlem/network-arayuzleri-bant-genisligi-monitoru.md", "Alanlar"),
        ("t-dhcp", "DHCP İstatistikleri ekranında hangi alanlar bulunur?", "field_listing", "guides/antikor_v2/anlik-gozlem/dhcp-istatistikleri.md", "Alanlar"),
    )
    cases = []
    inventory = []
    for case_id, question, intent, relative_path, section in definitions:
        path = ROOT / "knowledge_base" / relative_path
        available = base.sections(path.read_text(encoding="utf-8"))
        source = available[section]
        required = (
            ["Durum", "Kaynak Arayüz", "Kaydet"] if case_id == "t-dynamic" else
            ["+ Ekle"] if case_id == "t-nat-first" else
            base.procedure_labels(source)[:2] + base.procedure_labels(source)[-1:]
            if intent == "procedure" else
            [term for term in base.labels(source) if term != "#"][:3]
            if intent == "field_listing" else base.scope_terms(path.stem, source)
        )
        cases.append(base.make(case_id, question, intent, relative_path, section,
                               list(dict.fromkeys(required)), [], source, "targeted"))
        inventory.append({"title": path.stem, "relative_path": relative_path,
                          "available_sections": list(available),
                          "usable_evidence_sections": [name for name, value in available.items()
                                                       if has_usable_evidence(value)]})
    return {"schema_version": 1, "generated_without_llm": True,
            "guide_count": len(inventory), "question_count": len(cases),
            "inventory": inventory, "cases": cases, "source_incomplete_guides": []}


def build_dataset() -> dict:
    manifest = json.loads((BATCH / "promotion_manifest.json").read_text(encoding="utf-8"))
    inventory: list[dict] = []
    cases: list[dict] = []
    procedure_budget = 8
    title_counts: dict[str, int] = {}
    for item in manifest["guides"]:
        key = str(item["title"]).casefold()
        title_counts[key] = title_counts.get(key, 0) + 1
    for number, item in enumerate(manifest["guides"], 1):
        path = ROOT / item["destination_knowledge_base_path"]
        text = path.read_text(encoding="utf-8")
        sections = base.sections(text)
        relative_path = path.relative_to(ROOT / "knowledge_base").as_posix()
        title = item["title"]
        identity = (
            f"{item['category']} bölümündeki {title}"
            if title_counts[title.casefold()] > 1 else title
        )
        inventory.append({
            "title": title, "relative_path": relative_path, "category": item["category"],
            "available_sections": list(sections), "source_url": item["source_url"],
            "usable_evidence_sections": [name for name, value in sections.items()
                                         if name not in {"Kaynak bilgisi", "Uyarılar"} and has_usable_evidence(value)],
        })
        choices: list[tuple[str, str, str, list[str]]] = []
        menu = sections.get("Menü yolu", "")
        if has_usable_evidence(menu):
            choices.append(("navigation", "Menü yolu",
                            f"{identity} için kaynakta verilen menü yolu nedir?",
                            base.menu_terms(menu, title)))
        fields = sections.get("Alanlar", "")
        field_terms = [term for term in base.labels(fields) if term != "#"][:3]
        if field_terms and has_usable_evidence(fields):
            choices.append(("field_listing", "Alanlar",
                            f"{identity} ekranında hangi alanlar bulunur?", field_terms))
        controls = sections.get("Görünür kontroller", "")
        control_terms = base.labels(controls)[:2]
        creation_terms = [term for term in control_terms if "ekle" in term.casefold()]
        if creation_terms and has_usable_evidence(controls):
            choices.append(("first_action", "Görünür kontroller",
                            f"{identity} ekranında yeni kayıt için ilk hangi butona basmalıyım?", creation_terms[:1]))
        steps = sections.get("Kullanım adımları", "")
        step_terms = base.procedure_labels(steps)
        if has_usable_evidence(steps) and step_terms and procedure_budget:
            choices.append(("procedure", "Kullanım adımları",
                            f"{identity} nasıl yapılandırılır?", list(dict.fromkeys(step_terms[:2] + step_terms[-1:]))))
        if not choices:
            scope = sections.get("Kapsam", "")
            choices.append(("general_information", "Kapsam", f"{title} nedir?",
                            base.scope_terms(title, scope)))
        preferred = ("navigation", "field_listing", "first_action", "procedure")[number % 4]
        selected = next((choice for choice in choices if choice[0] == preferred), choices[0])
        if selected[0] == "procedure":
            procedure_budget -= 1
        intent, section, question, required = selected
        cases.append(base.make(f"b1-{number:02d}", question, intent, relative_path,
                               section, required, [], sections.get(section, ""), "generated"))

    for cid, question, intent, path, section, required, forbidden in base.CRITICAL:
        source = base.sections((ROOT / "knowledge_base" / path).read_text(encoding="utf-8")).get(section, "")
        cases.append(base.make(cid, question, intent, path, section, required, forbidden,
                               source, "critical_regression"))
    return {
        "schema_version": 1, "generated_without_llm": True,
        "guide_count": len(inventory), "question_count": len(cases),
        "inventory": inventory, "cases": cases,
        "source_incomplete_guides": [x["relative_path"] for x in inventory
                                     if x["usable_evidence_sections"] == ["Kapsam"]],
    }


def main() -> int:
    BATCH.mkdir(parents=True, exist_ok=True)
    base.ROOT = ROOT
    base.GUIDES = ROOT / "knowledge_base" / "guides" / "antikor_v2"
    base.OUT = BATCH
    targeted = os.getenv("VALIDATION_MODE") == "targeted"
    retry_ids = set(filter(None, os.getenv("VALIDATION_RETRY_IDS", "").split(",")))
    base.REPORT = (
        BATCH / "final_retry_validation.json" if retry_ids else
        BATCH / "targeted_validation.json" if targeted else REPORT
    )
    data = targeted_dataset() if targeted else build_dataset()
    if retry_ids:
        data["cases"] = [item for item in data["cases"] if item["id"] in retry_ids]
        data["question_count"] = len(data["cases"])
    print(f"dataset guides={data['guide_count']} questions={data['question_count']}", flush=True)
    asyncio.run(base.run(data, no_resume=True, max_attempts=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
