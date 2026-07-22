"""Run the eight-question Sprint 27.8 live HTTP quality gate."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import httpx

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "work/visual_guide_extraction/sprint27_8/product_field_validation.json"

CASES = (
    ("q01", "Antikor nedir ve temel olarak hangi amaçlarla kullanılır?", "product", ("güvenlik", "antikor")),
    ("q02", "Antikor ne işe yarar?", "product", ("güvenlik", "kor")),
    ("q03", "Antikor’un temel güvenlik özellikleri nelerdir?", "product", ("güvenlik",)),
    ("q04", "Antikor SD-WAN nedir?", "sdwan", ("sd-wan",)),
    ("q05", "Web Sunucu Güvenliği ekranında hangi alanlar bulunur ve bu alanlar ne işe yarar?", "web-sunucu-guvenligi", ("gövde", "sqli", "protokol", "itibar", "veri sızınt")),
    ("q06", "Web Sunucu Güvenliği ekranındaki saldırı koruma seçenekleri nelerdir?", "web-sunucu-guvenligi", ("sqli", "xss")),
    ("q07", "Rapor Ayarları ekranında hangi alanlar bulunur ve ne işe yarar?", "rapor-ayarlari", ("imza", "yedek")),
    ("q08", "Güvenlik Kuralları ekranındaki temel alanlar nelerdir?", "guvenlik-kurallari", ("adres",)),
)


def main() -> int:
    results = []
    with httpx.Client(timeout=300.0) as client:
        for case_id, question, family, terms in CASES:
            started = perf_counter()
            response = client.post("http://localhost:8000/api/v1/chat", json={"message": question})
            response.raise_for_status()
            payload = response.json()
            answer = payload["response"]
            folded = answer.casefold()
            paths = [item["relative_path"].replace("\\", "/").casefold() for item in payload["sources"]]
            if family == "product":
                source_ok = bool(paths) and all(path.endswith(".docx") for path in paths)
            elif family == "sdwan":
                source_ok = bool(paths) and all(
                    "sd-wan" in path or "sdwan" in path for path in paths
                )
            else:
                source_ok = bool(paths) and all(family in path for path in paths)
            present = [term for term in terms if term.casefold() in folded]
            capability_markers = {
                "firewall": ("firewall", "güvenlik duvar"),
                "ids_ips": ("ids", "ips", "saldırı tespit"),
                "vpn": ("vpn", "uzaktan erişim"),
                "web_application": ("uygulama kontrol", "web", "ssl inceleme"),
                "logging": ("log", "rapor"),
                "central_management": ("merkezi yönetim",),
            }
            represented_capabilities = [
                category for category, markers in capability_markers.items()
                if any(marker in folded for marker in markers)
            ] if case_id in {"q01", "q02", "q03"} else []
            irrelevant_groups = (
                ["body_limits"]
                if case_id == "q06" and any(
                    marker in folded for marker in ("gövde boyutu", "yanıt gövdesi")
                ) else []
            )
            passed = (
                source_ok and len(present) == len(terms)
                and (len(represented_capabilities) >= 3 if case_id in {"q01", "q02", "q03"} else True)
                and not irrelevant_groups
            )
            results.append({
                "id": case_id, "question": question, "answer": answer,
                "citations": payload["sources"], "source_family_correct": source_ok,
                "required_terms": list(terms), "present_terms": present,
                "represented_capability_categories": represented_capabilities,
                "irrelevant_answer_groups": irrelevant_groups,
                "answer_length": len(answer), "duration_seconds": round(perf_counter() - started, 3),
                "passed": passed,
            })
            print(f"{case_id}: {'PASS' if passed else 'FAIL'}", flush=True)
    summary = {"total": len(results), "passed": sum(item["passed"] for item in results)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
