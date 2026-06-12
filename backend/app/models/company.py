from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (UniqueConstraint("job_id", "row_number", name="uq_companies_job_row"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(512), nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(512), nullable=True)
    instagram: Mapped[str | None] = mapped_column(String(512), nullable=True)
    decision_maker_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_maker_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("Job", back_populates="companies")
    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="company", cascade="all, delete-orphan")

