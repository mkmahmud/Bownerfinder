from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    id: str
    status: str
    source_filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    progress_percent: int
    current_step: str | None
    current_message: str | None
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


class JobStats(BaseModel):
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    companies_total: int
    companies_enriched: int


class EnrichmentRequest(BaseModel):
    mode: str = "full"


class ExportRequest(BaseModel):
    format: str = "csv"
    job_id: str | None = None
    selected_company_ids: list[str] | None = None


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


class DecisionMakerResult(BaseModel):
    name: str | None
    title: str | None
    confidence: int
    reasoning: str


class EnrichedCompanyRead(BaseModel):
    id: str
    job_id: str
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

    model_config = ConfigDict(from_attributes=True)


class ResultRead(EnrichedCompanyRead):
    enrichment_status: str
    evidence_count: int
    contact_count: int

