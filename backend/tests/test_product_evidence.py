from app.retrieval.models import RetrievedChunk
from app.retrieval.product_evidence import ProductEvidenceBalancer


def _chunk(name: str, text: str, index: int = 0) -> RetrievedChunk:
    return RetrievedChunk(
        document_name=name,
        relative_path=f"docs/{name}.docx",
        section_title="Genel Bakış",
        chunk_index=index,
        chunk_text=text,
        similarity_score=0.9,
        language="tr",
        source_type="product_document",
        definition_evidence=index == 0,
    )


def test_general_overview_keeps_core_and_limits_sub_products():
    chunks = [
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "Antikor yeni nesil güvenlik duvarıdır."),
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "IPS saldırı tespiti sağlar.", 1),
        _chunk("Antikor Kriptolu Dual Layer SDWAN", "SD-WAN bağlantıları yönetir."),
        _chunk("Antikor CTNM SDWAN Merkezi Yönetim", "SD-WAN merkezi yönetim sağlar."),
    ]
    result = ProductEvidenceBalancer.select(chunks, 4)
    assert result.core_overview_present
    assert result.sub_product_ratio <= 0.5
    assert sum("SDWAN" in item.document_name for item in result.chunks) <= 1


def test_product_answer_validator_requires_breadth():
    result = ProductEvidenceBalancer.select([
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "Antikor firewall ürünüdür."),
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "IPS ve VPN özellikleri sunar.", 1),
    ], 4)
    missing = ProductEvidenceBalancer.missing_answer_requirements(
        "Antikor bir güvenlik duvarıdır.", result
    )
    assert "multiple_capability_categories" in missing


def test_marketing_chunks_do_not_replace_core_capabilities():
    chunks = [
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "Antikor yeni nesil güvenlik duvarıdır."),
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "%100 yerli ve millî üretim sağlar.", 1),
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "IDS/IPS saldırı tespit ve önleme sunar.", 2),
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "VPN güvenli uzaktan erişim sağlar.", 3),
        _chunk("1. Antikor NGFW Yeni Nesil Güvenlik Duvarı Tanıtım", "Merkezi log ve raporlama sunar.", 4),
    ]
    result = ProductEvidenceBalancer.select(chunks, 4)
    assert result.marketing_chunk_ratio == 0
    assert len(set(result.selected_categories) - {"general_product"}) >= 3
