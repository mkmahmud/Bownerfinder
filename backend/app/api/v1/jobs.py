from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company
from app.models.job import Job
from app.schemas.company import CompanyRead
from app.schemas.job import JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobRead])
def list_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Job]:
    statement = select(Job).order_by(Job.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


@router.get("/{job_id}/companies", response_model=list[CompanyRead])
def list_job_companies(
    job_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Company]:
    if db.get(Job, job_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    statement = (
        select(Company)
        .where(Company.job_id == job_id)
        .order_by(Company.row_number.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())

