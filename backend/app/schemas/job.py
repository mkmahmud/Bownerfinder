from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    id: str
    status: str
    source_filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadError(BaseModel):
    row_number: int
    message: str


class UploadResponse(BaseModel):
    job: JobRead
    errors: list[UploadError]

