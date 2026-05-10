"""FastAPI router for job-related endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from features.jobs.repository import JobRepository
from shared.models import JobCapturePayload
from workers import ExtractionWorker

logger = logging.getLogger(__name__)
router = APIRouter()

job_repository = JobRepository()


class CaptureResponse(BaseModel):
    id: int
    status: str


class MatchResponse(BaseModel):
    job_id: int
    match_score: float


@router.post("/jobs/capture", response_model=CaptureResponse)
async def capture_job(payload: JobCapturePayload) -> CaptureResponse:
    """Receive a raw HTML job payload from the Chrome Extension."""
    job = payload.to_job()
    job_id = job_repository.create(job)
    logger.info("Captured job %d from %s", job_id, payload.source)

    # Trigger LLM extraction in the background via the controller's thread pool
    try:
        from app import ApplicationController

        controller = ApplicationController.get_instance()
        controller.submit_extraction(job_id, payload.html)
    except RuntimeError:
        logger.warning(
            "ApplicationController not ready; extraction for job %d will need manual trigger",
            job_id,
        )

    return CaptureResponse(id=job_id, status="queued")


@router.get("/jobs")
async def list_jobs(limit: int = 100, offset: int = 0) -> list[dict]:
    """List saved jobs with pagination."""
    jobs = job_repository.list_all(limit=limit, offset=offset)
    return [job.model_dump() for job in jobs]


@router.get("/jobs/{job_id}")
async def get_job(job_id: Annotated[int, Path(...)]) -> dict:
    """Retrieve a single job by ID."""
    job = job_repository.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump()


@router.post("/jobs/{job_id}/extract")
async def extract_job(job_id: Annotated[int, Path(...)]) -> dict:
    """Trigger manual LLM extraction for a job."""
    job = job_repository.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        from app import ApplicationController

        controller = ApplicationController.get_instance()
        if job.raw_html:
            controller.submit_extraction(job_id, job.raw_html)
        else:
            return {"job_id": job_id, "status": "error", "detail": "No raw HTML available"}
    except RuntimeError:
        logger.warning("ApplicationController not ready; cannot trigger extraction")
        return {"job_id": job_id, "status": "error", "detail": "Controller not ready"}

    return {"job_id": job_id, "status": "extraction_queued"}


@router.post("/jobs/{job_id}/match", response_model=MatchResponse)
async def match_job(job_id: Annotated[int, Path(...)]) -> MatchResponse:
    """Match a job against the most recently uploaded resume."""
    job = job_repository.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Trigger matching in the background via controller
    try:
        from app import ApplicationController

        controller = ApplicationController.get_instance()
        controller.submit_matching(job_id)
    except (RuntimeError, AttributeError):
        logger.warning("Matching not available via controller")

    # Return current (possibly stale) score immediately
    return MatchResponse(job_id=job_id, match_score=job.match_score)


@router.post("/jobs/{job_id}/draft-email")
async def draft_email(job_id: Annotated[int, Path(...)]) -> dict:
    """Generate an email draft for a specific job."""
    job = job_repository.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        from app import ApplicationController

        controller = ApplicationController.get_instance()
        # Use the controller's internal composer directly for the API response
        resume = controller._resume_repository.get_latest()
        draft = controller._email_composer.compose(job, resume)
        return {
            "job_id": job_id,
            "subject": draft.subject,
            "body": draft.body,
        }
    except (RuntimeError, AttributeError):
        logger.warning("Draft generation via controller not available")
        return {
            "job_id": job_id,
            "subject": f"Application for {job.title or 'position'}",
            "body": "Dear Hiring Manager,\n\nI am writing to apply...",
        }
