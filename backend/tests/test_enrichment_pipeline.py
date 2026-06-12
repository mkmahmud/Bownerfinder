from app.core.config import get_settings
from app.services.ai import _rank_deterministically
from app.services.search import discover_website


def test_rank_deterministically_prefers_founder_titles() -> None:
    candidate = _rank_deterministically(
        "Acme Services",
        "Acme Services",
        [
            {"name": "Jane Smith", "title": "Director"},
            {"name": "John Smith", "title": "Founder"},
        ],
    )

    assert candidate.name == "John Smith"
    assert candidate.title == "Founder"
    assert candidate.confidence >= 90


def test_discover_website_handles_network_failure() -> None:
    discovery = discover_website("Acme Services", "Acme Services", timeout_seconds=0.01)

    assert discovery.website is None or discovery.website.startswith("http")