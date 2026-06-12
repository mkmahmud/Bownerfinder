from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.normalization import normalize_company_name

REQUIRED_COLUMNS = {"business_name"}
OPTIONAL_COLUMNS = {"website", "phone", "email", "linkedin", "facebook", "instagram"}
ACCEPTED_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS
SPREADSHEET_EXTENSIONS = {".csv", ".xlsx"}
FORMULA_PREFIXES = ("=", "+", "-", "@")


@dataclass(frozen=True)
class ParsedLead:
    row_number: int
    business_name: str
    normalized_business_name: str
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    linkedin: str | None = None
    facebook: str | None = None
    instagram: str | None = None


@dataclass(frozen=True)
class RowValidationError:
    row_number: int
    message: str


@dataclass(frozen=True)
class ParseResult:
    leads: list[ParsedLead]
    errors: list[RowValidationError]
    total_rows: int


def validate_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SPREADSHEET_EXTENSIONS:
        raise ValueError("Only CSV and XLSX files are supported.")
    return extension


def parse_upload(filename: str, content: bytes) -> ParseResult:
    extension = validate_extension(filename)
    frame = _read_frame(extension, content)
    frame = _normalize_columns(frame)
    _validate_columns(frame)

    leads: list[ParsedLead] = []
    errors: list[RowValidationError] = []
    for index, row in frame.iterrows():
        row_number = int(index) + 2
        values = {column: _clean_cell(row.get(column)) for column in ACCEPTED_COLUMNS}
        business_name = values.get("business_name")
        if not business_name:
            errors.append(RowValidationError(row_number=row_number, message="business_name is required."))
            continue
        if _looks_like_formula(business_name):
            errors.append(RowValidationError(row_number=row_number, message="business_name cannot start with a spreadsheet formula character."))
            continue
        sanitized = {key: _sanitize_export_value(value) for key, value in values.items()}
        leads.append(
            ParsedLead(
                row_number=row_number,
                business_name=sanitized["business_name"] or "",
                normalized_business_name=normalize_company_name(sanitized["business_name"] or ""),
                website=sanitized["website"],
                phone=sanitized["phone"],
                email=sanitized["email"],
                linkedin=sanitized["linkedin"],
                facebook=sanitized["facebook"],
                instagram=sanitized["instagram"],
            )
        )

    return ParseResult(leads=leads, errors=errors, total_rows=len(frame.index))


def _read_frame(extension: str, content: bytes) -> pd.DataFrame:
    buffer = BytesIO(content)
    if extension == ".csv":
        return pd.read_csv(buffer, dtype=str, keep_default_na=False)
    return pd.read_excel(buffer, dtype=str, keep_default_na=False, engine="openpyxl")


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]
    return normalized


def _validate_columns(frame: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required column: {missing_list}.")


def _clean_cell(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _looks_like_formula(value: str) -> bool:
    return value.startswith(FORMULA_PREFIXES)


def _sanitize_export_value(value: str | None) -> str | None:
    if value is None:
        return None
    if _looks_like_formula(value):
        return "'" + value
    return value

