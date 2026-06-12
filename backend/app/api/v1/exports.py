from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.company import Company
from app.models.enums import ExportStatus
from app.models.export import Export
from app.schemas.job import ExportCreateResponse, ExportRead, ExportRequest
from app.services.exports import create_export

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("", response_model=list[ExportRead])
def list_exports(job_id: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[ExportRead]:
    statement = select(Export).order_by(Export.created_at.desc())
    if job_id:
        statement = statement.where(Export.job_id == job_id)
    return [ExportRead.model_validate(export) for export in db.scalars(statement).all()]


@router.post("", response_model=ExportCreateResponse, status_code=status.HTTP_201_CREATED)
def create_export_route(
    payload: ExportRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ExportCreateResponse:
    export = create_export(
        db,
        settings,
        job_id=payload.job_id,
        company_ids=payload.selected_company_ids,
        export_format=payload.format,
    )
    return ExportCreateResponse(export=ExportRead.model_validate(export))


@router.get("/{export_id}", response_model=ExportRead)
def get_export(export_id: str, db: Session = Depends(get_db)) -> ExportRead:
    export = db.get(Export, export_id)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found.")
    return ExportRead.model_validate(export)


@router.get("/{export_id}/download")
def download_export(export_id: str, db: Session = Depends(get_db)):
    export = db.get(Export, export_id)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found.")
    if export.status != ExportStatus.completed.value or not export.file_path:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Export is not ready.")
    filename = export.file_path.rsplit("/", 1)[-1]
    return FileResponse(export.file_path, filename=filename)