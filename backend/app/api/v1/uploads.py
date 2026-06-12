from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.job import UploadError, UploadResponse
from app.services.uploads import UploadTooLargeError, create_upload_job

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_leads(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    try:
        job, parse_result = await create_upload_job(db, file, settings)
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return UploadResponse(
        job=job,
        errors=[UploadError(row_number=error.row_number, message=error.message) for error in parse_result.errors],
    )

