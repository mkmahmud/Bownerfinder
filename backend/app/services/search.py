from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import re
from urllib.parse import parse_qs, unquote, urlparse

import httpx


BLOCKED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "maps.google.com",
    "youtube.com",
    "yelp.com",
    "crunchbase.com",
    "wikipedia.org",
    "glassdoor.com",
}


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str | None = None
    score: float = 0.0


@dataclass(frozen=True)
class WebsiteDiscovery:
    website: str | None
    confidence: int
    evidence: list[SearchResult]


DECISION_TITLES = ("founder", "owner", "ceo", "president", "managing director", "director", "co-founder", "partner")
PROFILE_DOMAINS = ("linkedin.com/in", "linkedin.com/company", "facebook.com", "instagram.com")


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[dict[str, str]] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = {key: value or "" for key, value in attrs}
        href = attributes.get("href")
        if href:
            self._current_href = href
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._current_href is None:
            return
        text = " ".join(part.strip() for part in self._current_text if part.strip()).strip()
        self.anchors.append({"href": self._current_href, "text": text})
        self._current_href = None
        self._current_text = []


def search_public_web(query: str, timeout_seconds: float, max_results: int = 5) -> list[SearchResult]:
    try:
        response = httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (compatible; Bownerfinder/1.0)"},
            timeout=timeout_seconds,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return []

    parser = _AnchorParser()
    parser.feed(response.text)

    results: list[SearchResult] = []
    for anchor in parser.anchors:
        href = anchor["href"]
        title = anchor["text"].strip()
        if not title:
            continue
        url = _normalize_search_url(href)
        if not url:
            continue
        score = _score_search_result(query, url, title)
        results.append(SearchResult(title=title, url=url, score=score))

    results.sort(key=lambda item: item.score, reverse=True)
    return results[:max_results]


def discover_website(company_name: str, normalized_name: str, timeout_seconds: float) -> WebsiteDiscovery:
    queries = [
        f'"{normalized_name or company_name}" official website',
        f'"{normalized_name or company_name}" homepage',
        f'"{normalized_name or company_name}" contact us',
    ]
    results: list[SearchResult] = []
    for query in queries:
        results.extend(search_public_web(query, timeout_seconds=timeout_seconds, max_results=5))
    filtered = [result for result in _deduplicate_results(results) if not _is_blocked_domain(result.url)]
    if not filtered:
        return WebsiteDiscovery(website=None, confidence=0, evidence=[])

    best = max(filtered, key=lambda result: result.score)
    confidence = min(95, max(20, int(best.score)))
    return WebsiteDiscovery(website=best.url, confidence=confidence, evidence=filtered[:3])


def discover_company_profiles(company_name: str, normalized_name: str, timeout_seconds: float) -> list[SearchResult]:
    queries = [
        f'"{normalized_name or company_name}" site:linkedin.com/company',
        f'"{normalized_name or company_name}" site:facebook.com',
        f'"{normalized_name or company_name}" site:instagram.com',
    ]
    results: list[SearchResult] = []
    for query in queries:
        results.extend(search_public_web(query, timeout_seconds=timeout_seconds, max_results=5))
    return [result for result in _deduplicate_results(results) if _is_profile_url(result.url)]


def discover_people_candidates(company_name: str, normalized_name: str, timeout_seconds: float) -> list[dict[str, str]]:
    queries = []
    base = normalized_name or company_name
    for title in DECISION_TITLES:
        queries.append(f'"{base}" {title}')
        queries.append(f'site:linkedin.com/in "{base}" {title}')
    candidates: list[dict[str, str]] = []
    for query in queries:
        for result in search_public_web(query, timeout_seconds=timeout_seconds, max_results=5):
            candidate = _candidate_from_search_result(result, base)
            if candidate is not None:
                candidates.append(candidate)
    return _deduplicate_candidate_dicts(candidates)


def _normalize_search_url(raw_url: str) -> str | None:
    parsed = urlparse(raw_url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg")
        if uddg:
            return unquote(uddg[0])
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return raw_url
    if raw_url.startswith("//"):
        return f"https:{raw_url}"
    return None


def _is_blocked_domain(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in BLOCKED_DOMAINS)


def _score_search_result(query: str, url: str, title: str) -> float:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    score = 50.0
    if domain.startswith("www."):
        score += 4
    query_terms = [term for term in query.lower().replace('"', "").split() if len(term) > 2]
    searchable = f"{domain} {title.lower()}"
    for term in query_terms:
        if term in searchable:
            score += 3
    if any(token in title.lower() for token in ("official", "home", "homepage")):
        score += 8
    if domain.endswith(".com") or domain.endswith(".co"):
        score += 2
    if _is_blocked_domain(url):
        score -= 100
    return score


def _is_profile_url(url: str) -> bool:
    return any(domain in url.lower() for domain in PROFILE_DOMAINS)


def _candidate_from_search_result(result: SearchResult, company_name: str) -> dict[str, str] | None:
    text = f"{result.title} {result.snippet or ''}".strip()
    match = _parse_candidate_text(text)
    if match is None:
        return None
    name, title = match
    normalized_text = text.lower()
    if company_name.lower() not in normalized_text and "linkedin.com/in" not in result.url.lower() and "linkedin.com/company" not in result.url.lower():
        return None
    return {"name": name, "title": title}


def _parse_candidate_text(text: str) -> tuple[str, str] | None:
    patterns = (
        r"(?P<name>[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){1,3})\s*(?:-|–|\||,|·|·\s*)\s*(?P<title>Founder|Owner|CEO|Chief Executive Officer|President|Managing Director|Director|Co-Founder|Partner)",
        r"(?P<title>Founder|Owner|CEO|Chief Executive Officer|President|Managing Director|Director|Co-Founder|Partner)\s*(?:at|of|for|\-|–|\||,|·|·\s*)\s*(?P<name>[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){1,3})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            name = match.group("name").strip()
            title = _normalize_title(match.group("title").strip())
            if len(name.split()) >= 2:
                return name, title
    return None


def _deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    deduplicated: list[SearchResult] = []
    for result in results:
        key = result.url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(result)
    return deduplicated


def _deduplicate_candidate_dicts(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduplicated: list[dict[str, str]] = []
    for candidate in candidates:
        key = (candidate["name"].lower(), candidate["title"].lower())
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(candidate)
    return deduplicated


def _normalize_title(title: str) -> str:
    lowered = title.lower()
    if lowered == "chief executive officer":
        return "CEO"
    if lowered == "co-founder":
        return "Co-Founder"
    return title.title()