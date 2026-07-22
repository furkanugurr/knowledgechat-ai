"""Run the ten-question Sprint 27.7 HTTP regression gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

import httpx

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from app.retrieval.question_plan import (  # noqa: E402
    AnswerCompletenessValidator,
    QuestionPlanner,
)

OUTPUT = ROOT / "work" / "visual_guide_extraction" / "sprint27_7"
REPORT = OUTPUT / "multipart_validation.json"

CASES = (
    ("q01", "Antikor nedir ve temel olarak hangi amaçlarla kullanılır?", (".docx",), ("sunucu kapatma", "yeniden başlat")),
    ("q02", "IPS nedir, ne işe yarar ve Antikor’da nasıl kullanılır?", (".docx", "ips"), ("bilgi bulunamadı", "ipsec")),
    ("q03", "VLAN nedir ve Antikor’da VLAN yapılandırması hangi amaçla yapılır?", ("vlan",), ("bilgi bulunamadı",)),
    ("q04", "Dinamik NAT nedir ve Statik NAT’tan farkı nedir?", ("dinamik-nat", "statik-nat"), ("sdwan", "daha güvenli", "daha güvenilir", "daha iyi", "ideal", "üstün")),
    ("q05", "SSL VPN ayarları hangi menü altında bulunur ve ne amaçla kullanılır?", ("ssl-vpn-ayarlari",), ("sertifika-yonetimi", "istemcisiz")),
    ("q06", "Yeni bir güvenlik kuralı oluştururken Kaynak Adres ile Hedef Adres arasındaki fark nedir?", ("guvenlik-kurallari",), ("top-10",)),
    ("q07", "Yeni bir yönetim paneli kullanıcısı nasıl oluşturulur? Adımları sırayla açıklar mısın?", ("yonetim-paneli-kullanicilari",), ("parola değiştir", "filtre", "sertifika", "örnek kullanıcı")),
    ("q08", "Web Sunucu Güvenliği ekranında hangi alanlar bulunur ve bu alanlar ne işe yarar?", ("web-sunucu-guvenligi",), ("bilgi bulunamadı",)),
    ("q09", "Rapor Ayarları ekranına nasıl gidilir ve burada hangi ayarlar yapılabilir?", ("rapor-ayarlari",), ("log arşiv yapılandırması",)),
    ("q10", "OSPF nedir ve Antikor’da OSPF yapılandırması nasıl yapılır?", ("ospf",), ("bilgi bulunamadı", "komşu durum", "parola dökümü")),
)


def source_matches(paths: list[str], expected: tuple[str, ...]) -> bool:
    folded = [item.casefold() for item in paths]
    return bool(folded) and all(
        any(token.casefold() in path for path in folded) for token in expected
    ) and all(
        any(token.casefold() in path for token in expected) for path in folded
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--rescore-existing", action="store_true")
    args = parser.parse_args()
    if args.rescore_existing:
        payload = json.loads(REPORT.read_text(encoding="utf-8"))
        definitions = {item[0]: item for item in CASES}
        for result in payload["results"]:
            _, _, expected_sources, forbidden = definitions[result["id"]]
            paths = [item["relative_path"] for item in result["citations"]]
            plan = QuestionPlanner.plan(result["question"])
            answered = AnswerCompletenessValidator.answered_components(
                plan, result["answer"]
            )
            missing = [
                item.value for item in plan.requested_components
                if item not in answered
            ]
            forbidden_found = [
                item for item in forbidden
                if item.casefold() in result["answer"].casefold()
            ]
            source_ok = source_matches(paths, expected_sources)
            result.update({
                "answered_components": [item.value for item in answered],
                "missing_components": missing,
                "expected_source_family": list(expected_sources),
                "source_family_correct": source_ok,
                "forbidden_terms_found": forbidden_found,
                "passed": source_ok and not missing and not forbidden_found and bool(paths),
            })
        results = payload["results"]
        summary = {
            "total": len(results),
            "correct": sum(item["passed"] for item in results),
            "wrong_dominant_documents": sum(not item["source_family_correct"] for item in results),
            "missing_requested_components": sum(bool(item["missing_components"]) for item in results),
            "unrelated_source_families": sum(not item["source_family_correct"] for item in results),
            "unrelated_answer_sections": sum(bool(item["forbidden_terms_found"]) for item in results),
        }
        payload["summary"] = summary
        REPORT.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if summary["correct"] == len(results) else 1
    results = []
    selected_cases = [
        item for item in CASES if not args.case_id or item[0] in args.case_id
    ]
    with httpx.Client(timeout=args.timeout) as client:
        for case_id, question, expected_sources, forbidden in selected_cases:
            started = perf_counter()
            response = client.post(
                f"{args.base_url.rstrip('/')}/api/v1/chat",
                json={"message": question},
            )
            response.raise_for_status()
            payload = response.json()
            answer = payload["response"]
            paths = [item["relative_path"] for item in payload["sources"]]
            plan = QuestionPlanner.plan(question)
            answered = AnswerCompletenessValidator.answered_components(plan, answer)
            missing = [
                item.value for item in plan.requested_components
                if item not in answered
            ]
            forbidden_found = [item for item in forbidden if item.casefold() in answer.casefold()]
            source_ok = source_matches(paths, expected_sources)
            passed = source_ok and not missing and not forbidden_found and bool(paths)
            results.append({
                "id": case_id,
                "question": question,
                "detected_intent": plan.primary_intent.value,
                "primary_entity": plan.primary_entity,
                "requested_components": [item.value for item in plan.requested_components],
                "answered_components": [item.value for item in answered],
                "missing_components": missing,
                "expected_source_family": list(expected_sources),
                "citations": payload["sources"],
                "source_family_correct": source_ok,
                "forbidden_terms_found": forbidden_found,
                "ollama_called": True,
                "generic_no_answer": not bool(paths),
                "answer": answer,
                "duration_seconds": round(perf_counter() - started, 3),
                "passed": passed,
            })
            print(f"{case_id}: {'PASS' if passed else 'FAIL'}", flush=True)
    summary = {
        "total": len(results),
        "correct": sum(item["passed"] for item in results),
        "wrong_dominant_documents": sum(not item["source_family_correct"] for item in results),
        "missing_requested_components": sum(bool(item["missing_components"]) for item in results),
        "unrelated_source_families": sum(not item["source_family_correct"] for item in results),
        "unrelated_answer_sections": sum(bool(item["forbidden_terms_found"]) for item in results),
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if results and summary["correct"] == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
