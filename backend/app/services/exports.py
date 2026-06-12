from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.company import Company
from app.models.enums import ExportFormat, ExportStatus
from app.models.export import Export
from app.models.job import Job


def create_export(
    db: Session,
    settings: Settings,
    *,
    job_id: str | None,
    company_ids: list[str] | None,
    export_format: str,
) -> Export:
    if export_format not in {ExportFormat.csv.value, ExportFormat.xlsx.value}:
        raise ValueError("Export format must be csv or xlsx.")
    if not job_id and not company_ids:
        raise ValueError("job_id or company_ids must be provided for export.")

    export = Export(job_id=job_id or _job_id_for_company_ids(db, company_ids or []), format=export_format, status=ExportStatus.running.value)
    db.add(export)
    db.flush()

    rows = _build_export_rows(db, job_id=job_id, company_ids=company_ids)
    export_path = _write_export_file(settings.export_dir, export, rows, export_format)
    export.file_path = str(export_path)
    export.status = ExportStatus.completed.value
    db.commit()
    db.refresh(export)
    return export


def _job_id_for_company_ids(db: Session, company_ids: list[str]) -> str:
    statement = select(Company.job_id).where(Company.id.in_(company_ids)).limit(1)
    job_id = db.execute(statement).scalar_one_or_none()
    if not job_id:
        raise ValueError("Unable to determine job for selected companies.")
    return str(job_id)


def _build_export_rows(db: Session, *, job_id: str | None, company_ids: list[str] | None) -> list[dict[str, object]]:
    statement: Select[tuple[Company, Job.source_filename]] = select(Company, Job.source_filename).join(Job, Job.id == Company.job_id)
    if job_id:
        statement = statement.where(Company.job_id == job_id)
    if company_ids:
        statement = statement.where(Company.id.in_(company_ids))
    statement = statement.order_by(Company.row_number.asc())

    rows: list[dict[str, object]] = []
    for company, source_filename in db.execute(statement).all():
        rows.append(
            {
                "job_id": company.job_id,
                "source_filename": source_filename,
                "row_number": company.row_number,
                "business_name": company.business_name,
                "normalized_business_name": company.normalized_business_name,
                "website": company.website,
                "phone": company.phone,
                "email": company.email,
                "linkedin": company.linkedin,
                "facebook": company.facebook,
                "instagram": company.instagram,
                "decision_maker_name": company.decision_maker_name,
                "decision_maker_title": company.decision_maker_title,
                "confidence_score": company.confidence_score,
                "validation_errors": company.validation_errors,
            }
        )
    return rows


def _write_export_file(export_dir: Path, export: Export, rows: list[dict[str, object]], export_format: str) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame(rows)
    base_name = f"{export.id}_results"
    if export_format == ExportFormat.csv.value:
        path = export_dir / f"{base_name}.csv"
        dataframe.to_csv(path, index=False)
        return path
    path = export_dir / f"{base_name}.xlsx"
    dataframe.to_excel(path, index=False)
    return path