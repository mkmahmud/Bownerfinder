"""phase 1 schema

Revision ID: 0001_phase_1_schema
Revises:
Create Date: 2026-06-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_phase_1_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=512), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("valid_rows", sa.Integer(), nullable=False),
        sa.Column("invalid_rows", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("business_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_business_name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("linkedin", sa.String(length=512), nullable=True),
        sa.Column("facebook", sa.String(length=512), nullable=True),
        sa.Column("instagram", sa.String(length=512), nullable=True),
        sa.Column("decision_maker_name", sa.String(length=255), nullable=True),
        sa.Column("decision_maker_title", sa.String(length=255), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("validation_errors", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "row_number", name="uq_companies_job_row"),
    )
    op.create_index("ix_companies_business_name", "companies", ["business_name"])
    op.create_index("ix_companies_job_id", "companies", ["job_id"])
    op.create_index("ix_companies_normalized_business_name", "companies", ["normalized_business_name"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("field_name", sa.String(length=128), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_company_id", "evidence", ["company_id"])

    op.create_table(
        "exports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exports_job_id", "exports", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_exports_job_id", table_name="exports")
    op.drop_table("exports")
    op.drop_index("ix_evidence_company_id", table_name="evidence")
    op.drop_table("evidence")
    op.drop_index("ix_contacts_company_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_index("ix_companies_normalized_business_name", table_name="companies")
    op.drop_index("ix_companies_job_id", table_name="companies")
    op.drop_index("ix_companies_business_name", table_name="companies")
    op.drop_table("companies")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_table("jobs")

