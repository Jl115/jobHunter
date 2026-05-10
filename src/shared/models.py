"""Pydantic models for core domain entities."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Lifecycle states for a job posting."""

    NEW = "new"
    VIEWED = "viewed"
    APPLIED = "applied"
    REJECTED = "rejected"


class Job(BaseModel):
    """A scraped job posting with extracted structured fields."""

    id: int | None = None
    url: str
    source: str = Field(..., description="Job board: linkedin, indeed, xing")
    title: str | None = None
    company: str | None = None
    location: str | None = None
    description: str | None = None
    raw_html: str = Field(..., description="Clean article HTML from Readability.js")
    scraped_at: datetime | None = None
    extracted_at: datetime | None = None
    match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: JobStatus = JobStatus.NEW
    created_at: datetime | None = None

    model_config: dict[str, Any] = {"from_attributes": True}


class Resume(BaseModel):
    """A parsed resume with structured fields."""

    id: int | None = None
    filename: str
    raw_text: str
    parsed_skills: list[str] = Field(default_factory=list)
    parsed_experience: list[str] = Field(default_factory=list)
    uploaded_at: datetime | None = None

    model_config: dict[str, Any] = {"from_attributes": True}


class EmailDraft(BaseModel):
    """A drafted outreach email for a specific job."""

    subject: str
    body: str
    recipient: str | None = None
    job_id: int


class JobCapturePayload(BaseModel):
    """Payload sent by the Chrome Extension when scraping a job page."""

    url: str
    source: str = Field(..., pattern=r"^(linkedin|indeed|xing)$")
    title: str | None = None
    html: str = Field(..., description="Clean article HTML from Readability.js")
    scraped_at: datetime

    def to_job(self) -> Job:
        """Convert payload to an un-extracted Job record."""
        return Job(
            url=self.url,
            source=self.source,
            title=self.title,
            raw_html=self.html,
            scraped_at=self.scraped_at,
        )
