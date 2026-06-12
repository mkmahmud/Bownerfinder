from enum import StrEnum


class JobStatus(StrEnum):
    pending = "pending"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ExportStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ExportFormat(StrEnum):
    csv = "csv"
    xlsx = "xlsx"

