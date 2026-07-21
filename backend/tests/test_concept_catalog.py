"""Tests for corpus-derived concept alias resolution."""

from app.retrieval.concept_catalog import ConceptCatalog


def test_resolves_only_exact_indexed_concepts() -> None:
    catalog = ConceptCatalog([
        {
            "alias": "ips", "display_term": "IPS",
            "relative_paths": "Antikor.docx|guides/ips.md", "acronym": "true",
        },
        {
            "alias": "antispam", "display_term": "Antispam",
            "relative_paths": "guides/antispam.md", "acronym": "false",
        },
    ])

    ips = catalog.resolve("IPS nedir?")
    assert ips is not None
    assert ips.acronym
    assert ips.relative_paths == ("Antikor.docx", "guides/ips.md")
    assert catalog.resolve("hamburger nedir?") is None
    assert catalog.resolve("ABCXYZ nedir?") is None


def test_does_not_treat_operational_question_as_definition() -> None:
    catalog = ConceptCatalog([{
        "alias": "nat", "display_term": "NAT",
        "relative_paths": "guides/nat.md", "acronym": "true",
    }])
    assert catalog.resolve("Dinamik NAT nasıl oluşturulur?") is None
