from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResultRead(BaseModel):
    id: str
    job_id: str
    job_status: str
    source_filename: str
    row_number: int
    business_name: str
    normalized_business_name: str
    website: str | None
    phone: str | None
    email: str | None
    linkedin: str | None
    facebook: str | None
    instagram: str | None
    decision_maker_name: str | None
    decision_maker_title: str | None
    confidence_score: int | None
    validation_errors: str | None
    created_at: datetime
    updated_at: datetime
    enrichment_status: str
    evidence_count: int
    contact_count: int

    model_config = ConfigDict(from_attributes=True)


class ResultListResponse(BaseModel):
    items: list[ResultRead]
    total: int


class ExportRead(BaseModel):
    id: str
    job_id: str
    format: str
    status: str
    file_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportCreateResponse(BaseModel):
    export: ExportRead