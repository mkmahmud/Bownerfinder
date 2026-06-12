from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company
from app.models.job import Job
from app.schemas.job import JobStats
from app.schemas.result import ResultListResponse, ResultRead

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=ResultListResponse)
def list_results(
    q: str | None = Query(default=None, max_length=255),
    job_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    min_confidence: int | None = Query(default=None, ge=0, le=100),
    sort: str = Query(default="confidence_score"),
    order: str = Query(default="desc"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ResultListResponse:
    statement = select(Company, Job.source_filename, Job.status).join(Job, Job.id == Company.job_id)
    statement = _apply_filters(statement, q=q, job_id=job_id, status_filter=status_filter, min_confidence=min_confidence)
    sort_column = _sort_column(sort)
    sort_expression = desc(sort_column) if order.lower() != "asc" else asc(sort_column)
    statement = statement.order_by(sort_expression, Company.row_number.asc()).offset(offset).limit(limit)

    rows = db.execute(statement).all()
    items = [
        ResultRead(
            id=company.id,
            job_id=company.job_id,
            job_status=job_status,
            source_filename=source_filename,
            row_number=company.row_number,
            business_name=company.business_name,
            normalized_business_name=company.normalized_business_name,
            website=company.website,
            phone=company.phone,
            email=company.email,
            linkedin=company.linkedin,
            facebook=company.facebook,
            instagram=company.instagram,
            decision_maker_name=company.decision_maker_name,
            decision_maker_title=company.decision_maker_title,
            confidence_score=company.confidence_score,
            validation_errors=company.validation_errors,
            created_at=company.created_at,
            updated_at=company.updated_at,
            enrichment_status=_enrichment_status(company, job_status),
            evidence_count=len(company.evidence),
            contact_count=len(company.contacts),
        )
        for company, source_filename, job_status in rows
    ]

    total_statement = select(func.count()).select_from(Company).join(Job, Job.id == Company.job_id)
    total_statement = _apply_filters(total_statement, q=q, job_id=job_id, status_filter=status_filter, min_confidence=min_confidence)
    total = int(db.execute(total_statement).scalar_one())
    return ResultListResponse(items=items, total=total)


@router.get("/stats", response_model=JobStats)
def get_result_stats(db: Session = Depends(get_db)) -> JobStats:
    total_jobs = int(db.execute(select(func.count()).select_from(Job)).scalar_one())
    pending_jobs = int(db.execute(select(func.count()).select_from(Job).where(Job.status == "pending")).scalar_one())
    running_jobs = int(db.execute(select(func.count()).select_from(Job).where(Job.status == "running")).scalar_one())
    completed_jobs = int(db.execute(select(func.count()).select_from(Job).where(Job.status == "completed")).scalar_one())
    failed_jobs = int(db.execute(select(func.count()).select_from(Job).where(Job.status == "failed")).scalar_one())
    companies_total = int(db.execute(select(func.count()).select_from(Company)).scalar_one())
    companies_enriched = int(
        db.execute(select(func.count()).select_from(Company).where(Company.decision_maker_name.is_not(None))).scalar_one()
    )
    return JobStats(
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        running_jobs=running_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        companies_total=companies_total,
        companies_enriched=companies_enriched,
    )


def _sort_column(sort: str):
    mapping = {
        "confidence_score": Company.confidence_score,
        "business_name": Company.business_name,
        "decision_maker_name": Company.decision_maker_name,
        "created_at": Company.created_at,
        "updated_at": Company.updated_at,
        "website": Company.website,
        "row_number": Company.row_number,
    }
    return mapping.get(sort, Company.confidence_score)


def _apply_filters(statement, *, q: str | None, job_id: str | None, status_filter: str | None, min_confidence: int | None):
    if job_id:
        statement = statement.where(Company.job_id == job_id)
    if status_filter:
        statement = statement.where(Job.status == status_filter)
    if min_confidence is not None:
        statement = statement.where(Company.confidence_score >= min_confidence)
    if q:
        like = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                Company.business_name.ilike(like),
                Company.normalized_business_name.ilike(like),
                Company.website.ilike(like),
                Company.email.ilike(like),
                Company.phone.ilike(like),
                Company.decision_maker_name.ilike(like),
                Company.decision_maker_title.ilike(like),
            )
        )
    return statement


def _enrichment_status(company: Company, job_status: str) -> str:
    if company.decision_maker_name or company.confidence_score is not None:
        return "enriched"
    if job_status in {"running", "queued", "pending"}:
        return job_status
    return "not_enriched"