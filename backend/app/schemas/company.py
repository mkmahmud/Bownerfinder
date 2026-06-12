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

    model_config = ConfigDict(from_attributes=True)

