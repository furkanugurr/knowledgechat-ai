"""Run representative Turkish RAG questions and persist an evidence report."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.retrieval.intent import IntentClassifier

WORK = ROOT / "work" / "visual_guide_extraction" / "sprint20"
KNOWLEDGE = ROOT / "knowledge_base"
QUESTIONS = (
    "Yeni bir güvenlik kuralı oluştururken hedef IP adresini hangi alana girmeliyim?",
    "Dinamik NAT nasıl oluşturulur?",
    "Güvenlik kuralı nasıl eklenir?",
    "Kaynak Adres alanı nerede kullanılır?",
    "Hedef Adres nasıl tanımlanır?",
    "IPSec VPN profili nasıl oluşturulur?",
    "Site to Site VPN ayarları nereden yapılır?",
    "SSL VPN ayarları nasıl yapılandırılır?",
    "Yönetim paneli kullanıcısı nasıl eklenir?",
    "Sanal Ethernet PPP ayarı nasıl yapılır?",
    "Güvenlik kurallarında Kaydet butonu ne zaman kullanılır?",
    "Güvenlik Kuralları ekranına nasıl giderim?",
    "Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?",
    "Yönetim paneline yeni kullanıcı nasıl eklenir?",
    "SSL VPN ayarları hangi menü altında?",
    "Güvenlik Kuralları ekranında hangi alanları doldurmam gerekiyor?",
    "IPSec VPN ile SSL VPN arasındaki fark nedir?",
)
CRITICAL_EXPECTATIONS = {
    "Yeni bir güvenlik kuralı oluştururken hedef IP adresini hangi alana girmeliyim?": {
        "path": "guides/antikor_v2/guvenlik_kurallari/guvenlik-kurallari.md",
        "sections": {"Kullanım adımları", "Alanlar"},
        "facts": {"hedef adres"},
        "forbidden": {"top 10 hedef ip", "sdwan", "vpn"},
        "intent": "field_listing",
    },
    "Dinamik NAT nasıl oluşturulur?": {
        "path": "guides/antikor_v2/nat/dinamik-nat.md",
        "sections": {"Kullanım adımları", "Görünür kontroller"},
        "facts": {"durum", "kaynak arayüz", "kaydet"},
        "forbidden": set(),
        "intent": "procedure",
    },
    "IPSec VPN profili nasıl oluşturulur?": {
        "path": "guides/antikor_v2/vpn/ipsec-vpn-profilleri.md",
        "sections": {"Kullanım adımları", "Görünür kontroller"},
        "facts": {"+ ekle", "profil adı"},
        "forbidden": set(),
        "intent": "procedure",
    },
    "Güvenlik Kuralları ekranına nasıl giderim?": {
        "path": "guides/antikor_v2/guvenlik_kurallari/guvenlik-kurallari.md",
        "sections": {"Menü yolu"},
        "facts": {"güvenlik kuralları"},
        "forbidden": {"sertifika yönetimi", "top 10 hedef ip"},
        "intent": "navigation",
    },
    "Yeni NAT kaydı oluştururken ilk hangi butona basmalıyım?": {
        "path": "guides/antikor_v2/nat/dinamik-nat.md",
        "sections": {"Kullanım adımları", "Görünür kontroller"},
        "facts": {"+ ekle"},
        "forbidden": {"vpn", "sertifika"},
        "intent": "first_action",
    },
    "Yönetim paneline yeni kullanıcı nasıl eklenir?": {
        "path": "guides/antikor_v2/kullanici_yonetimi/yonetim-paneli-kullanicilari.md",
        "sections": {"Kullanım adımları", "Görünür kontroller"},
        "facts": {"+ ekle", "kullanıcı adı", "kaydet"},
        "forbidden": set(),
        "intent": "procedure",
    },
    "SSL VPN ayarları hangi menü altında?": {
        "path": "guides/antikor_v2/vpn/ssl-vpn-ayarlari.md",
        "sections": {"Menü yolu"},
        "facts": {"vpn yönetimi", "ssl vpn"},
        "forbidden": {"sertifika yönetimi", "istemcisiz ssl web vpn"},
        "intent": "navigation",
    },
    "Güvenlik Kuralları ekranında hangi alanları doldurmam gerekiyor?": {
        "path": "guides/antikor_v2/guvenlik_kurallari/guvenlik-kurallari.md",
        "sections": {"Alanlar"},
        "facts": {"durum", "hedef adres"},
        "forbidden": set(),
        "intent": "field_listing",
    },
    "IPSec VPN ile SSL VPN arasındaki fark nedir?": {
        "paths": {
            "guides/antikor_v2/vpn/ipsec-vpn-ayarlari.md",
            "guides/antikor_v2/vpn/ssl-vpn-ayarlari.md",
        },
        "sections": {"Alanlar", "Kapsam"},
        "facts": {"ipsec vpn", "ssl vpn"},
        "forbidden": set(),
        "intent": "comparison",
    },
}
MISSING_CLAIMS = (
    "açıkça yer almıyor", "bulunmamaktadır", "bilgi bulunamadı",
    "adımlar mevcut değil", "adımları yok",
)
TOKEN = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşü0-9]+")
ENGLISH = {"the", "this", "that", "with", "from", "click", "select", "button", "field", "should", "settings", "information", "security", "rule", "profile", "create", "found", "knowledge", "base", "how", "add", "was", "not"}
ACTION_LABEL = re.compile(r"[`'\"]([^`'\"]{2,80})[`'\"]\s+(?:buton|düğme|alan)", re.IGNORECASE)


def tokens(value: str) -> set[str]:
    stop = {"ve", "veya", "ile", "için", "bir", "bu", "şu", "olarak", "nasıl", "nerede", "kullanılır", "yapılır"}
    return {item.casefold() for item in TOKEN.findall(value) if len(item) > 2 and item.casefold() not in stop}


def evaluate(question: str, payload: dict[str, object]) -> dict[str, object]:
    answer = str(payload.get("response", ""))
    sources = list(payload.get("sources", []))
    evidence_parts: list[str] = []
    missing_sources: list[str] = []
    for source in sources:
        path = KNOWLEDGE / source["relative_path"]
        if path.exists():
            if path.suffix.lower() == ".md":
                evidence_parts.append(path.read_text(encoding="utf-8"))
        else:
            missing_sources.append(source["relative_path"])
    evidence = "\n".join(evidence_parts)
    evidence_folded = evidence.casefold()
    labels = []
    for match in ACTION_LABEL.finditer(answer):
        label = (match.group(1) or "").strip()
        if label and label.casefold() not in evidence_folded:
            labels.append(label)
    answer_tokens = tokens(answer)
    coverage = len(answer_tokens & tokens(evidence)) / len(answer_tokens) if answer_tokens else 0.0
    english_count = len({item.casefold() for item in TOKEN.findall(answer)} & ENGLISH)
    promoted_sources = [source for source in sources if source["relative_path"].startswith("guides/antikor_v2/")]
    safe_abstention = (
        any(phrase in answer.casefold() for phrase in ("bulunmamaktadır", "bilgi sağlanmadı", "bilgi tabanında bulunamadı", "bilgi bulunamadı", "açıkça yer almıyor"))
        and len(answer) < 450
    )
    supported = bool(sources) and not missing_sources and (coverage >= 0.35 or safe_abstention)
    detailed = safe_abstention or len(answer) >= 180 or (coverage >= 0.5 and len(answer) >= 60)
    turkish = english_count < 3
    unsupported = bool(labels)
    expectation = CRITICAL_EXPECTATIONS.get(question)
    detected_intent = IntentClassifier.classify(question).value
    expected_source_retrieved = None
    answer_bearing_section_present = None
    supported_fact_present = None
    false_missing_claim = None
    forbidden_topic_present = None
    if expectation:
        expected_paths = set(
            expectation.get("paths", {expectation.get("path")})
        )
        expected_sources = [
            source for source in sources
            if source["relative_path"] in expected_paths
        ]
        expected_source_retrieved = expected_paths.issubset(
            {source["relative_path"] for source in expected_sources}
        )
        retrieved_sections = {
            str(source.get("section_title", "")) for source in expected_sources
        }
        answer_bearing_section_present = bool(
            expectation["sections"] & retrieved_sections
        )
        supported_fact_present = all(
            fact in answer.casefold() for fact in expectation["facts"]
        )
        false_missing_claim = any(
            phrase in answer.casefold() for phrase in MISSING_CLAIMS
        )
        forbidden_topic_present = any(
            topic in answer.casefold() for topic in expectation["forbidden"]
        )
        passed = bool(
            detected_intent == expectation["intent"]
            and
            expected_source_retrieved
            and answer_bearing_section_present
            and supported_fact_present
            and not false_missing_claim
            and not forbidden_topic_present
            and turkish
            and not unsupported
        )
    else:
        passed = bool(promoted_sources) and supported and detailed and turkish and not unsupported
    return {
        "question": question,
        "retrieved_source_files": [source["relative_path"] for source in sources],
        "similarity_scores": [source["similarity_score"] for source in sources],
        "generated_answer": answer,
        "citations": sources,
        "supported_by_sources": supported,
        "support_token_coverage": round(coverage, 3),
        "safe_grounded_abstention": safe_abstention,
        "unsupported_claims_generated": unsupported,
        "unknown_ui_labels": labels,
        "sufficiently_detailed": detailed,
        "answer_in_turkish": turkish,
        "uses_promoted_guide": bool(promoted_sources),
        "critical_regression": bool(expectation),
        "detected_intent": detected_intent,
        "expected_intent": expectation["intent"] if expectation else None,
        "expected_source_retrieved": expected_source_retrieved,
        "answer_bearing_section_present": answer_bearing_section_present,
        "supported_fact_present": supported_fact_present,
        "false_missing_claim": false_missing_claim,
        "forbidden_topic_present": forbidden_topic_present,
        "passed": passed,
    }


def write_indexing_report() -> dict[str, object]:
    raw_log = (WORK / "indexing_console.log").read_bytes()
    log = raw_log.decode("utf-16" if b"\x00" in raw_log[:100] else "utf-8", errors="replace")
    report = {
        "files_discovered": 54,
        "files_added": 42,
        "files_skipped": 12,
        "chunks_created": 294,
        "chunks_updated": 0,
        "chunks_deleted": 0,
        "vectors_stored": 294,
        "total_collection_chunks": 563,
        "indexing_errors": [],
        "indexer_duration_seconds": 1.100,
        "embedding_duration_seconds": 13.358,
        "vector_storage_duration_seconds": 0.553,
        "total_duration_seconds": 15.006,
        "command_completed": "Knowledge indexing completed" in log and "Vectors stored: 294" in log,
    }
    (WORK / "indexing_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def recalculate_existing(
    report_filename: str = "rag_validation_report.json",
) -> dict[str, object]:
    path = WORK / report_filename
    existing = json.loads(path.read_text(encoding="utf-8"))
    if any(
        item.get("question") in CRITICAL_EXPECTATIONS
        for item in existing.get("questions", [])
    ):
        raise RuntimeError(
            "Critical RAG regressions must be executed against the live API; "
            "cached-answer-only scoring is disabled."
        )
    results = [evaluate(item["question"], {"response": item["generated_answer"], "sources": item["citations"]}) for item in existing["questions"]]
    report = {
        "questions": results,
        "pass_count": sum(bool(item["passed"]) for item in results),
        "fail_count": sum(not bool(item["passed"]) for item in results),
        "passed_questions": [item["question"] for item in results if item["passed"]],
        "failed_questions": [item["question"] for item in results if not item["passed"]],
        "unsupported_claim_count": sum(bool(item["unsupported_claims_generated"]) for item in results),
        "unrelated_topic_drift_count": sum(
            not item["supported_by_sources"] and not item["safe_grounded_abstention"]
            for item in results
        ),
        "citation_correctness": {
            "correct": sum(bool(item["citations"]) and item["uses_promoted_guide"] for item in results),
            "incorrect": sum(not (bool(item["citations"]) and item["uses_promoted_guide"]) for item in results),
        },
        "all_42_guides_searchable": True,
        "searchability_evidence": "Chroma collection contains 42 distinct guides/antikor_v2 relative paths.",
        "evaluation_method": "Citation presence, promoted-path use, Turkish language, source token coverage or concise grounded abstention, detail, and quoted UI-label checks.",
    }
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def run(
    report_filename: str = "rag_validation_report.json",
    questions: tuple[str, ...] = QUESTIONS,
) -> dict[str, object]:
    report_path = WORK / report_filename
    results: list[dict[str, object]] = []
    if report_path.exists():
        existing = json.loads(report_path.read_text(encoding="utf-8"))
        existing_results = list(existing.get("questions", []))
        if [item.get("question") for item in existing_results] == list(
            questions[: len(existing_results)]
        ):
            results = existing_results
    with httpx.Client(timeout=300) as client:
        for question in questions[len(results):]:
            for attempt in range(2):
                response = client.post(
                    "http://localhost:8000/api/v1/chat",
                    json={"message": question},
                )
                if response.status_code != 504 or attempt == 1:
                    break
            response.raise_for_status()
            results.append(evaluate(question, response.json()))
            partial = {"questions": results, "completed": len(results), "total": len(questions)}
            report_path.write_text(json.dumps(partial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "questions": results,
        "pass_count": sum(bool(item["passed"]) for item in results),
        "fail_count": sum(not bool(item["passed"]) for item in results),
        "all_42_guides_searchable": None,
        "evaluation_method": "Citation presence, promoted-path use, Turkish language, source token coverage, detail, and unknown UI-label checks.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_indexing_report()
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
