from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.core.config import Settings


TITLE_PRIORITY = ["founder", "owner", "ceo", "president", "managing director", "director"]


@dataclass(frozen=True)
class RankedCandidate:
    name: str
    title: str
    confidence: int
    reasoning: str


def rank_decision_maker(
    company_name: str,
    normalized_name: str,
    candidates: list[dict[str, str]],
    settings: Settings,
) -> RankedCandidate | None:
    cleaned_candidates = [candidate for candidate in candidates if candidate.get("name") and candidate.get("title")]
    if not cleaned_candidates:
        return None

    ollama_candidate = _rank_with_ollama(company_name, normalized_name, cleaned_candidates, settings)
    if ollama_candidate is not None:
        return ollama_candidate
    return _rank_deterministically(company_name, normalized_name, cleaned_candidates)


def _rank_with_ollama(
    company_name: str,
    normalized_name: str,
    candidates: list[dict[str, str]],
    settings: Settings,
) -> RankedCandidate | None:
    prompt = (
        "You are selecting the most likely decision maker for a local business lead. "
        "Return only JSON with keys name, title, confidence, reasoning. "
        "Prefer the highest-ranked title using this order: Founder > Owner > CEO > President > Managing Director > Director. "
        f"Company: {company_name}\n"
        f"Normalized company: {normalized_name}\n"
        f"Candidates: {json.dumps(candidates, ensure_ascii=True)}"
    )

    try:
        response = httpx.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=settings.search_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("response") or payload.get("message", {}).get("content") or ""
    except (httpx.HTTPError, ValueError, AttributeError):
        return None

    parsed = _parse_candidate_payload(content)
    if parsed is None:
        return None
    return parsed


def _rank_deterministically(company_name: str, normalized_name: str, candidates: list[dict[str, str]]) -> RankedCandidate:
    scored_candidates = []
    for candidate in candidates:
        title = candidate["title"].lower()
        score = 50
        for index, priority in enumerate(TITLE_PRIORITY):
            if priority in title:
                score += (len(TITLE_PRIORITY) - index) * 8
                break
        if normalized_name.lower() in candidate["name"].lower() or company_name.lower() in candidate["name"].lower():
            score += 6
        if any(token in title for token in ("founder", "owner")):
            score += 6
        scored_candidates.append((score, candidate))

    score, candidate = max(scored_candidates, key=lambda item: item[0])
    reasoning = f"Selected by title priority and company-name match heuristics for {company_name}."
    return RankedCandidate(
        name=candidate["name"],
        title=_normalize_title(candidate["title"]),
        confidence=min(95, int(score)),
        reasoning=reasoning,
    )


def _parse_candidate_payload(content: str) -> RankedCandidate | None:
    stripped = content.strip()
    if not stripped:
        return None
    if stripped.startswith("```"):
        stripped = stripped.strip("`\n ")
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            data = json.loads(stripped[start : end + 1])
        except json.JSONDecodeError:
            return None

    name = str(data.get("name") or "").strip()
    title = str(data.get("title") or "").strip()
    reasoning = str(data.get("reasoning") or "").strip()
    confidence_raw = data.get("confidence", 0)
    try:
        confidence = int(confidence_raw)
    except (TypeError, ValueError):
        confidence = 0

    if not name or not title:
        return None
    return RankedCandidate(name=name, title=_normalize_title(title), confidence=max(0, min(100, confidence)), reasoning=reasoning or "Local LLM ranking.")


def _normalize_title(title: str) -> str:
    lowered = title.lower()
    if lowered == "chief executive officer":
        return "CEO"
    if lowered == "co-founder":
        return "Co-Founder"
    return title.title()