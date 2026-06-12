from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanyRead(BaseModel):
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
    confidence_score: int | None
    validation_errors: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyEvidenceRead(BaseModel):
    id: str
    company_id: str
    source_type: str
    source_url: str | None
    field_name: str
    field_value: str
    confidence: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyContactRead(BaseModel):
    id: str
    company_id: str
    name: str | None
    title: str | None
    email: str | None
    phone: str | None
    source_url: str | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

