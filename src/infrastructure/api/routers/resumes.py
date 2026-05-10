"""FastAPI router for resume-related endpoints."""

import logging
from pathlib import Path
import tempfile
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Path, UploadFile

from features.resume.extractor import ResumeExtractor
from features.resume.parser import ResumeParser
from features.resume.repository import ResumeRepository
from shared.app_state import AppState

logger = logging.getLogger(__name__)
router = APIRouter()

resume_repository = ResumeRepository()
resume_extractor = ResumeExtractor()
resume_parser = ResumeParser()
app_state = AppState.get_instance()


@router.post("/resumes/upload")
async def upload_resume(file: Annotated[UploadFile, File(...)]) -> dict:
    """Upload a PDF resume, extract text, parse structure, and store."""
    if file.content_type != "application/pdf" and not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        raw_text = resume_extractor.extract_text(tmp_path)
        parsed = resume_parser.parse(raw_text)
        resume_id = resume_repository.create(
            filename=file.filename,
            raw_text=raw_text,
            parsed_skills=",".join(parsed.parsed_skills),
            parsed_experience=",".join(parsed.parsed_experience),
        )
        app_state.resume_uploaded.emit(resume_id)
        logger.info("Uploaded resume %d: %s", resume_id, file.filename)
        return {
            "id": resume_id,
            "filename": file.filename,
            "skills": parsed.parsed_skills,
            "experience_count": len(parsed.parsed_experience),
        }
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get("/resumes")
async def list_resumes() -> list[dict]:
    """List all uploaded resumes."""
    resumes = resume_repository.list_all()
    return [resume.model_dump() for resume in resumes]


@router.get("/resumes/{resume_id}")
async def get_resume(resume_id: Annotated[int, Path(...)]) -> dict:
    """Retrieve a single resume by ID."""
    resume = resume_repository.get_by_id(resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume.model_dump()
