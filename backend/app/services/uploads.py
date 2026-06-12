from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.company import Company
from app.models.enums import JobStatus
from app.models.job import Job
from app.services.upload_parser import ParseResult, parse_upload, validate_extension


class UploadTooLargeError(ValueError):
    pass


async def create_upload_job(db: Session, file: UploadFile, settings: Settings) -> tuple[Job, ParseResult]:
    if not file.filename:
        raise ValueError("Uploaded file must have a filename.")
    validate_extension(file.filename)
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise UploadTooLargeError("Uploaded file exceeds the configured size limit.")

    parse_result = parse_upload(file.filename, content)
    job_id = str(uuid4())
    stored_filename = _stored_filename(settings.upload_dir, job_id, file.filename)
    stored_filename.write_bytes(content)

    job = Job(
        id=job_id,
        status=JobStatus.pending.value,
        source_filename=Path(file.filename).name,
        stored_filename=str(stored_filename),
        total_rows=parse_result.total_rows,
        valid_rows=len(parse_result.leads),
        invalid_rows=len(parse_result.errors),
    )
    db.add(job)
    db.flush()

    for lead in parse_result.leads:
        db.add(
            Company(
                job_id=job.id,
                row_number=lead.row_number,
                business_name=lead.business_name,
                normalized_business_name=lead.normalized_business_name,
                website=lead.website,
                phone=lead.phone,
                email=lead.email,
                linkedin=lead.linkedin,
                facebook=lead.facebook,
                instagram=lead.instagram,
            )
        )

    db.commit()
    db.refresh(job)
    return job, parse_result


def _stored_filename(upload_dir: Path, job_id: str, original_filename: str) -> Path:
    safe_name = Path(original_filename).name.replace(" ", "_")
    return upload_dir / f"{job_id}_{safe_name}"

