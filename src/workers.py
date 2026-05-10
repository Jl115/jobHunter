"""PySide6 background workers for long-running tasks.

These workers offload heavy operations (LLM inference, sentence-transformers,
email composition) to background threads so the GUI stays responsive.
"""

import logging

from PySide6.QtCore import QRunnable

from features.email import EmailComposer
from features.job_extraction import BatchExtractor
from features.jobs import JobMatcher, JobRepository
from features.resume import ResumeRepository
from shared.app_state import AppState
from shared.models import Job, Resume

logger = logging.getLogger(__name__)


class ExtractionWorker(QRunnable):
    """Background task: LLM extraction for a newly captured job."""

    def __init__(
        self,
        job_id: int,
        raw_html: str,
        extractor: BatchExtractor,
        repository: JobRepository,
    ) -> None:
        super().__init__()
        self.job_id = job_id
        self.raw_html = raw_html
        self.extractor = extractor
        self.repository = repository

    def run(self) -> None:
        try:
            logger.info("Starting LLM extraction for job %d", self.job_id)
            extracted = self.extractor.extract(self.raw_html)
            logger.info(
                "LLM extraction for job %d returned: title=%r company=%r location=%r desc_len=%d",
                self.job_id,
                extracted.title,
                extracted.company,
                extracted.location,
                len(extracted.description or ""),
            )

            # If the LLM returns nothing useful, fall back to the raw HTML as description
            # so the user at least sees the scraped text.
            desc = extracted.description or self.raw_html

            self.repository.update_extraction(
                self.job_id,
                title=extracted.title,
                company=extracted.company,
                location=extracted.location,
                description=desc,
            )
            self.repository.update_status(self.job_id, extracted.status)
            logger.info("Extraction completed for job %d", self.job_id)
            AppState.get_instance().extraction_completed.emit(self.job_id)
            AppState.get_instance().jobs_updated.emit()
        except Exception:
            logger.exception("Extraction failed for job %d", self.job_id)


class MatchWorker(QRunnable):
    """Background task: semantic matching for a job against latest resume."""

    def __init__(
        self,
        job_id: int,
        matcher: JobMatcher,
        job_repository: JobRepository,
        resume_repository: ResumeRepository,
    ) -> None:
        super().__init__()
        self.job_id = job_id
        self.matcher = matcher
        self.job_repository = job_repository
        self.resume_repository = resume_repository

    def run(self) -> None:
        try:
            job = self.job_repository.get_by_id(self.job_id)
            resume = self.resume_repository.get_latest()
            if job is None or resume is None:
                logger.warning("Cannot match: missing job or resume")
                return
            score = self.matcher.calculate_match(job, resume)
            self.job_repository.update_match_score(self.job_id, score)
            logger.info("Match score for job %d: %.3f", self.job_id, score)
            AppState.get_instance().jobs_updated.emit()
        except Exception:
            logger.exception("Matching failed for job %d", self.job_id)


class EmailDraftWorker(QRunnable):
    """Background task: generate an email draft for a job."""

    def __init__(
        self,
        job_id: int,
        composer: EmailComposer,
        job_repository: JobRepository,
        resume_repository: ResumeRepository,
        callback,
    ) -> None:
        super().__init__()
        self.job_id = job_id
        self.composer = composer
        self.job_repository = job_repository
        self.resume_repository = resume_repository
        self.callback = callback

    def run(self) -> None:
        try:
            job = self.job_repository.get_by_id(self.job_id)
            resume = self.resume_repository.get_latest()
            if job is None:
                logger.warning("Cannot draft email: job %d not found", self.job_id)
                return
            draft = self.composer.compose(job, resume)
            logger.info("Email drafted for job %d", self.job_id)
            AppState.get_instance().email_drafted.emit(self.job_id)
            self.callback(draft)
        except Exception:
            logger.exception("Email drafting failed for job %d", self.job_id)
