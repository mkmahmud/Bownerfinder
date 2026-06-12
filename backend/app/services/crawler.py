from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx


ALLOWED_SLUGS = (
    "about",
    "about-us",
    "aboutus",
    "who-we-are",
    "team",
    "our-team",
    "leadership",
    "leadership-team",
    "management",
    "staff",
    "people",
    "executive",
    "company",
    "contact",
    "contact-us",
)
TITLE_KEYWORDS = (
    "founder",
    "owner",
    "ceo",
    "president",
    "managing director",
    "director",
    "co-founder",
    "partner",
)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}(?:\s?(?:ext\.?|x)\s?\d{1,6})?",
    flags=re.IGNORECASE,
)
NAME_TITLE_PATTERNS = (
    re.compile(
        r"(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s*(?:,|\-|–|\|)?\s*(?P<title>Founder|Owner|CEO|Chief Executive Officer|President|Managing Director|Director|Co-Founder|Partner)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"(?P<title>Founder|Owner|CEO|Chief Executive Officer|President|Managing Director|Director|Co-Founder|Partner)\s*(?:,|\-|–|\|)?\s*(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        flags=re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class PageSnapshot:
    url: str
    title: str | None
    text: str
    links: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    candidates: list[dict[str, str]] = field(default_factory=list)
    social_links: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CrawlResult:
    pages: list[PageSnapshot]
    emails: list[str]
    phones: list[str]
    candidates: list[dict[str, str]]
    social_links: list[str]


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self._in_title = False
        self._in_ignored_tag = False
        self._text_parts: list[str] = []
        self.links: list[str] = []
        self.social_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        if tag in {"script", "style", "noscript"}:
            self._in_ignored_tag = True
            return
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = attr_map.get("href", "")
            if href:
                self.links.append(href)
                if any(domain in href.lower() for domain in ("linkedin.com", "facebook.com", "instagram.com")):
                    self.social_links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._in_ignored_tag = False
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_ignored_tag:
            return
        text = data.strip()
        if not text:
            return
        if self._in_title and self.title is None:
            self.title = text
        self._text_parts.append(text)

    @property
    def text(self) -> str:
        return " ".join(self._text_parts)


def crawl_company_site(website: str, max_pages: int, timeout_seconds: float) -> CrawlResult:
    normalized_website = _normalize_url(website)
    if normalized_website is None:
        return CrawlResult(pages=[], emails=[], phones=[], candidates=[], social_links=[])

    client = httpx.Client(
        headers={"User-Agent": "Mozilla/5.0 (compatible; Bownerfinder/1.0)"},
        timeout=timeout_seconds,
        follow_redirects=True,
    )
    visited: set[str] = set()
    queue: list[str] = [normalized_website]
    pages: list[PageSnapshot] = []
    aggregate_emails: set[str] = set()
    aggregate_phones: set[str] = set()
    aggregate_candidates: list[dict[str, str]] = []
    aggregate_social_links: set[str] = set()

    try:
        while queue and len(pages) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            snapshot = _fetch_page(client, url)
            if snapshot is None:
                continue

            pages.append(snapshot)
            aggregate_emails.update(snapshot.emails)
            aggregate_phones.update(snapshot.phones)
            aggregate_social_links.update(snapshot.social_links)
            aggregate_candidates.extend(snapshot.candidates)

            for link in snapshot.links:
                next_url = _canonicalize_link(normalized_website, link)
                if next_url and next_url not in visited and _is_allowed_page(next_url):
                    queue.append(next_url)
    finally:
        client.close()

    return CrawlResult(
        pages=pages,
        emails=sorted(aggregate_emails),
        phones=sorted(aggregate_phones),
        candidates=_deduplicate_candidates(aggregate_candidates),
        social_links=sorted(aggregate_social_links),
    )


def _fetch_page(client: httpx.Client, url: str) -> PageSnapshot | None:
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    raw_html = response.text
    parser = _PageParser()
    parser.feed(response.text)
    text = parser.text
    emails = sorted({*EMAIL_PATTERN.findall(text), *_extract_mailto_emails(raw_html)})
    phones = sorted({*{match.group(0).strip() for match in PHONE_PATTERN.finditer(text)}, *_extract_tel_numbers(raw_html)})
    candidates = _extract_candidates(text)
    return PageSnapshot(
        url=str(response.url),
        title=parser.title,
        text=text,
        links=parser.links,
        emails=emails,
        phones=phones,
        candidates=candidates,
        social_links=parser.social_links,
    )


def _extract_candidates(text: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for pattern in NAME_TITLE_PATTERNS:
        for match in pattern.finditer(text):
            name = match.group("name").strip()
            title = _normalize_title(match.group("title").strip())
            if len(name.split()) >= 2:
                results.append({"name": name, "title": title})
    return results


def _deduplicate_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
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


def _normalize_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        if url.startswith("//"):
            return f"https:{url}"
        return None
    if parsed.path in {"", "/"}:
        return f"{parsed.scheme}://{parsed.netloc}/"
    return url


def _canonicalize_link(base_url: str, link: str) -> str | None:
    if link.startswith("mailto:") or link.startswith("tel:"):
        return None
    absolute_url = urljoin(base_url, link)
    parsed = urlparse(absolute_url)
    base_host = urlparse(base_url).netloc.lower()
    if parsed.netloc.lower() != base_host:
        return None
    return absolute_url.split("#", 1)[0]


def _is_allowed_page(url: str) -> bool:
    path = urlparse(url).path.lower().strip("/")
    if not path:
        return True
    return any(slug in path for slug in ALLOWED_SLUGS)


def _extract_mailto_emails(raw_html: str) -> set[str]:
    return {match.group(1) for match in re.finditer(r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", raw_html, flags=re.IGNORECASE)}


def _extract_tel_numbers(raw_html: str) -> set[str]:
    numbers = set()
    for match in re.finditer(r"tel:([^\"'\s>]+)", raw_html, flags=re.IGNORECASE):
        value = re.sub(r"[^0-9+]+", "", match.group(1))
        if value:
            numbers.add(value)
    return numbers