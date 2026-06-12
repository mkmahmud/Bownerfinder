from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.contact import Contact
from app.models.evidence import Evidence
from app.models.enums import JobStatus
from app.models.job import Job
from app.services.ai import rank_decision_maker
from app.services.crawler import CrawlResult, crawl_company_site
from app.services.normalization import normalize_company_name
from app.services.queue import enqueue_job_pipeline
from app.services.search import discover_company_profiles, discover_people_candidates, discover_website


DECISION_TITLES = {
    "Founder": 100,
    "Co-Founder": 95,
    "Owner": 92,
    "CEO": 88,
    "President": 82,
    "Managing Director": 78,
    "Director": 70,
}

_executor_instance: ThreadPoolExecutor | None = None


@dataclass(frozen=True)
class CandidateEvidence:
    name: str
    title: str
    source_url: str | None
    source_type: str


def schedule_job_pipeline(job_id: str, settings: Settings | None = None) -> None:
    active_settings = settings or get_settings()
    if active_settings.job_execution_mode == "inline":
        run_job_pipeline(job_id, active_settings)
        return
    if active_settings.job_execution_mode == "queue":
        try:
            enqueue_job_pipeline(job_id, active_settings)
            return
        except Exception:
            pass
    executor = _get_executor()
    executor.submit(run_job_pipeline, job_id, active_settings)


def run_job_pipeline(job_id: str, settings: Settings | None = None) -> None:
    active_settings = settings or get_settings()
    db = SessionLocal()
    try:
        job = (
            db.query(Job)
            .options(selectinload(Job.companies).selectinload(Company.contacts), selectinload(Job.companies).selectinload(Company.evidence))
            .filter(Job.id == job_id)
            .one_or_none()
        )
        if job is None:
            return

        job.status = JobStatus.running.value
        _set_job_progress(db, job, 0, "Queued", "Starting enrichment pipeline.")
        db.commit()

        companies = sorted(job.companies, key=lambda item: item.row_number)
        total_companies = len(companies)
        for index, company in enumerate(companies, start=1):
            _set_job_progress(
                db,
                job,
                _progress_for(index - 1, total_companies),
                "Processing company",
                f"Processing {company.business_name} ({index}/{total_companies}).",
            )
            _process_company(db, company, active_settings)
            db.refresh(company)

        job.status = JobStatus.completed.value
        _set_job_progress(db, job, 100, "Completed", f"Finished enrichment for {total_companies} companies.")
        job.error_message = None
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive top-level guard
        job = db.get(Job, job_id)
        if job is not None:
            job.status = JobStatus.failed.value
            job.error_message = str(exc)
            job.current_step = "Failed"
            job.current_message = str(exc)
            db.commit()
        raise
    finally:
        db.close()


def _process_company(db: Session, company: Company, settings: Settings) -> None:
    company.normalized_business_name = normalize_company_name(company.business_name)

    website = company.website.strip() if company.website else None
    website_evidence = []
    if not website:
        _update_company_progress(db, company, "Find Website", f"Searching for the official website for {company.business_name}.")
        discovery = discover_website(company.business_name, company.normalized_business_name, settings.search_timeout_seconds)
        website = discovery.website
        website_evidence = discovery.evidence
        if website:
            company.website = website
            company.evidence.append(
                Evidence(
                    source_type="search_result",
                    source_url=website,
                    field_name="website",
                    field_value=website,
                    confidence=discovery.confidence,
                )
            )

    _update_company_progress(db, company, "Find Company Profiles", f"Searching company profiles for {company.business_name}.")
    profile_results = discover_company_profiles(company.business_name, company.normalized_business_name, settings.search_timeout_seconds)
    for profile in profile_results:
        company.evidence.append(
            Evidence(
                source_type="company_profile",
                source_url=profile.url,
                field_name="profile_url",
                field_value=profile.title,
                confidence=int(profile.score),
            )
        )

    crawl_result = CrawlResult(pages=[], emails=[], phones=[], candidates=[], social_links=[])
    if website:
        _update_company_progress(db, company, "Find People", f"Crawling {website} for public people and contact pages.")
        crawl_result = crawl_company_site(website, settings.max_crawl_pages, settings.crawl_timeout_seconds)

    _store_crawl_evidence(company, website_evidence, crawl_result)
    _store_contacts(company, crawl_result)

    _update_company_progress(db, company, "Verify Titles", f"Verifying public titles for {company.business_name}.")
    search_candidates = discover_people_candidates(company.business_name, company.normalized_business_name, settings.search_timeout_seconds)
    for candidate in search_candidates:
        company.evidence.append(
            Evidence(
                source_type="search_result",
                source_url=website,
                field_name="candidate",
                field_value=f"{candidate['name']} | {candidate['title']}",
                confidence=70,
            )
        )

    _update_company_progress(db, company, "Rank Decision Makers", f"Ranking the most likely decision maker for {company.business_name}.")
    candidates = _merge_candidates(company, crawl_result, search_candidates)
    ranked = rank_decision_maker(company.business_name, company.normalized_business_name, candidates, settings)
    if ranked is not None:
        company.decision_maker_name = ranked.name
        company.decision_maker_title = ranked.title
        company.confidence_score = _confidence_score(company, ranked.title, crawl_result, bool(website_evidence))
        company.evidence.append(
            Evidence(
                source_type="ai_ranking",
                source_url=website,
                field_name="decision_maker",
                field_value=f"{ranked.name} | {ranked.title}",
                confidence=ranked.confidence,
            )
        )
    else:
        company.confidence_score = _confidence_score(company, None, crawl_result, bool(website_evidence))

    _update_company_progress(db, company, "Find Contact Information", f"Collecting public contact details for {company.business_name}.")
    if company.email is None:
        company.email = _best_email(crawl_result)
    if company.phone is None:
        company.phone = _best_phone(crawl_result)

    _update_company_progress(db, company, "Done", f"Finished processing {company.business_name}.")
    db.commit()


def _store_crawl_evidence(company: Company, website_evidence, crawl_result: CrawlResult) -> None:
    for result in website_evidence:
        if hasattr(result, "url"):
            company.evidence.append(
                Evidence(
                    source_type="search_result",
                    source_url=getattr(result, "url", None),
                    field_name="website_result",
                    field_value=getattr(result, "title", ""),
                    confidence=int(getattr(result, "score", 0)),
                )
            )

    for page in crawl_result.pages:
        company.evidence.append(
            Evidence(
                source_type="crawl_page",
                source_url=page.url,
                field_name="page_title",
                field_value=page.title or page.url,
                confidence=50,
            )
        )
        for email in page.emails:
            company.evidence.append(
                Evidence(
                    source_type="crawl_page",
                    source_url=page.url,
                    field_name="email",
                    field_value=email,
                    confidence=85,
                )
            )
        for phone in page.phones:
            company.evidence.append(
                Evidence(
                    source_type="crawl_page",
                    source_url=page.url,
                    field_name="phone",
                    field_value=phone,
                    confidence=85,
                )
            )
        for candidate in page.candidates:
            company.evidence.append(
                Evidence(
                    source_type="crawl_page",
                    source_url=page.url,
                    field_name="candidate",
                    field_value=f"{candidate['name']} | {candidate['title']}",
                    confidence=80,
                )
            )
        for link in page.social_links:
            company.evidence.append(
                Evidence(
                    source_type="social_profile",
                    source_url=link,
                    field_name="profile_url",
                    field_value=link,
                    confidence=65,
                )
            )


def _store_contacts(company: Company, crawl_result: CrawlResult) -> None:
    seen: set[tuple[str | None, str | None]] = set()
    for candidate in crawl_result.candidates:
        key = (candidate.get("name"), candidate.get("title"))
        if key in seen:
            continue
        seen.add(key)
        company.contacts.append(
            Contact(
                name=candidate.get("name"),
                title=candidate.get("title"),
                source_url=company.website,
                notes="Discovered from public website crawl.",
            )
        )

    for email in crawl_result.emails[:3]:
        company.contacts.append(
            Contact(
                email=email,
                source_url=company.website,
                notes="Public email discovered on website.",
            )
        )

    for phone in crawl_result.phones[:3]:
        company.contacts.append(
            Contact(
                phone=phone,
                source_url=company.website,
                notes="Public phone discovered on website.",
            )
        )


def _merge_candidates(company: Company, crawl_result: CrawlResult, search_candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = list(crawl_result.candidates) + list(search_candidates)
    if company.decision_maker_name and company.decision_maker_title:
        candidates.append({"name": company.decision_maker_name, "title": company.decision_maker_title})
    return _deduplicate_candidates(candidates)


def _confidence_score(company: Company, title: str | None, crawl_result: CrawlResult, website_found: bool) -> int:
    score = 20
    if website_found:
        score += 25
    if len(crawl_result.pages) > 1:
        score += 10
    if crawl_result.emails:
        score += 10
    if crawl_result.phones:
        score += 5
    if title is not None:
        score += DECISION_TITLES.get(title, 0) // 4
    if company.normalized_business_name.lower() in company.business_name.lower():
        score += 5
    return max(0, min(100, score))


def _best_email(crawl_result: CrawlResult) -> str | None:
    return crawl_result.emails[0] if crawl_result.emails else None


def _best_phone(crawl_result: CrawlResult) -> str | None:
    return crawl_result.phones[0] if crawl_result.phones else None


def _get_executor() -> ThreadPoolExecutor:
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ThreadPoolExecutor(max_workers=4)
    return _executor_instance


def _set_job_progress(db: Session, job: Job, percent: int, step: str, message: str) -> None:
    job.progress_percent = max(0, min(100, percent))
    job.current_step = step
    job.current_message = message
    db.add(job)
    db.commit()


def _update_company_progress(db: Session, company: Company, step: str, message: str) -> None:
    job = db.get(Job, company.job_id)
    if job is None:
        return
    job.current_step = f"{step}: {company.business_name}"
    job.current_message = message
    job.progress_percent = max(job.progress_percent, min(99, job.progress_percent))
    db.add(job)
    db.commit()


def _progress_for(index: int, total: int) -> int:
    if total <= 0:
        return 0
    return min(99, int((index / total) * 100))


def _deduplicate_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduplicated: list[dict[str, str]] = []
    for candidate in candidates:
        name = candidate.get("name", "").strip()
        title = candidate.get("title", "").strip()
        if not name or not title:
            continue
        key = (name.lower(), title.lower())
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append({"name": name, "title": title})
    return deduplicated