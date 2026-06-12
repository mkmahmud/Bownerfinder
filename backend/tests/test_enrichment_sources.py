from app.services.crawler import _extract_mailto_emails, _extract_tel_numbers
from app.services.search import SearchResult, discover_people_candidates


def test_discover_people_candidates_parses_profile_titles(monkeypatch) -> None:
    def fake_search(query: str, timeout_seconds: float, max_results: int = 5):
        return [
            SearchResult(
                title="John Smith - Founder - Acme Services | LinkedIn",
                url="https://www.linkedin.com/in/john-smith/",
                snippet="Founder at Acme Services",
                score=95,
            )
        ]

    monkeypatch.setattr("app.services.search.search_public_web", fake_search)

    candidates = discover_people_candidates("Acme Services", "Acme Services", timeout_seconds=1.0)

    assert candidates == [{"name": "John Smith", "title": "Founder"}]


def test_extract_mailto_emails_and_tel_numbers() -> None:
    raw_html = '<a href="mailto:hello@acme.test">Email</a><a href="tel:+1-555-0100">Call</a>'

    assert _extract_mailto_emails(raw_html) == {"hello@acme.test"}
    assert _extract_tel_numbers(raw_html) == {"+15550100"}