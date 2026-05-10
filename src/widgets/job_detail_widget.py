"""Job detail view with actions (upload resume, match, draft email)."""

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from features.jobs import JobMatcher, JobRepository
from features.resume import ResumeExtractor, ResumeParser, ResumeRepository
from shared.app_state import AppState
from workers import MatchWorker

logger = logging.getLogger(__name__)


class JobDetailWidget(QWidget):
    """Display job details and provide action buttons."""

    draft_email_requested: Signal = Signal(int)
    """Emitted when the user clicks 'Draft Email'. Carries the job ID."""

    def __init__(
        self,
        job_repository: JobRepository | None = None,
        resume_repository: ResumeRepository | None = None,
        job_matcher: JobMatcher | None = None,
        thread_pool=None,
    ) -> None:
        super().__init__()
        self._job_id: int | None = None
        self._repository = job_repository
        self._resume_repository = resume_repository
        self._job_matcher = job_matcher
        self._thread_pool = thread_pool

        layout = QVBoxLayout(self)

        # Form fields (read-only by default)
        form_layout = QFormLayout()
        self._title_edit = QLineEdit()  # type: ignore[call-arg]
        self._title_edit.setReadOnly(True)
        self._company_edit = QLineEdit()  # type: ignore[call-arg]
        self._company_edit.setReadOnly(True)
        self._location_edit = QLineEdit()  # type: ignore[call-arg]
        self._location_edit.setReadOnly(True)

        form_layout.addRow("Title:", self._title_edit)
        form_layout.addRow("Company:", self._company_edit)
        form_layout.addRow("Location:", self._location_edit)
        layout.addLayout(form_layout)

        # Description
        self._description_edit = QTextEdit()
        self._description_edit.setReadOnly(True)
        self._description_edit.setPlaceholderText("Job description will appear here...")
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self._description_edit)

        # Match score label
        self._match_label = QLabel("Match Score: —")
        layout.addWidget(self._match_label)

        # Buttons
        buttons = QHBoxLayout()
        self._upload_btn = QPushButton("Upload Resume")
        self._upload_btn.clicked.connect(self._upload_resume)

        self._match_btn = QPushButton("Match Resume")
        self._match_btn.clicked.connect(self._match_resume)

        self._draft_btn = QPushButton("Draft Email")
        self._draft_btn.clicked.connect(self._draft_email)

        buttons.addWidget(self._upload_btn)
        buttons.addWidget(self._match_btn)
        buttons.addWidget(self._draft_btn)
        layout.addLayout(buttons)

        # Listen for updates so score/description refresh automatically
        AppState.get_instance().jobs_updated.connect(self._on_jobs_updated)

    def load_job(self, job_id: int) -> None:
        """Load job data into the form."""
        self._job_id = job_id
        if self._repository is None:
            logger.warning("Detail widget has no repository; cannot load job %d", job_id)
            return
        job = self._repository.get_by_id(job_id)
        if job is None:
            self._title_edit.setText("Not Found")
            self._company_edit.setText("")
            self._location_edit.setText("")
            self._description_edit.setPlainText("")
            self._match_label.setText("Match Score: —")
            return
        self._title_edit.setText(job.title or "")
        self._company_edit.setText(job.company or "")
        self._location_edit.setText(job.location or "")
        self._description_edit.setPlainText(job.description or "")
        self._match_label.setText(f"Match Score: {job.match_score:.0%}")
        logger.info("Loaded job %d: %s at %s", job_id, job.title, job.company)

    def _on_jobs_updated(self) -> None:
        """If the currently displayed job changes behind the scenes, refresh it."""
        if self._job_id is not None:
            self.load_job(self._job_id)

    def _upload_resume(self) -> None:
        """Open a file dialog to select a PDF resume, parse it, and store it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Resume PDF", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            extractor = ResumeExtractor()
            raw_text = extractor.extract_text(file_path)
            parser = ResumeParser()
            parsed = parser.parse(raw_text)

            if self._resume_repository is not None:
                resume_id = self._resume_repository.create(
                    filename=file_path,
                    raw_text=raw_text,
                    parsed_skills=",".join(parsed.parsed_skills),
                    parsed_experience=",".join(parsed.parsed_experience),
                )
                AppState.get_instance().resume_uploaded.emit(resume_id)
                QMessageBox.information(
                    self,
                    "Resume Uploaded",
                    f"Parsed {len(parsed.parsed_skills)} skills and "
                    f"{len(parsed.parsed_experience)} experience entries.",
                )
            else:
                QMessageBox.information(self, "Resume", f"Parsed:\n{file_path}")
            logger.info("Resume uploaded: %s", file_path)
        except Exception:
            logger.exception("Failed to upload resume")
            QMessageBox.critical(self, "Error", "Failed to parse the PDF resume.")

    def _match_resume(self) -> None:
        """Trigger semantic matching for the current job in a background thread."""
        if self._job_id is None:
            return
        if self._job_matcher is None or self._thread_pool is None:
            QMessageBox.information(self, "Match", "Matching not yet configured.")
            return
        worker = MatchWorker(
            job_id=self._job_id,
            matcher=self._job_matcher,
            job_repository=self._repository,
            resume_repository=self._resume_repository,
        )
        self._thread_pool.start(worker)
        QMessageBox.information(
            self, "Match", "Matching in progress... Results will appear shortly."
        )

    def _draft_email(self) -> None:
        """Emit signal to navigate to the email preview for this job."""
        if self._job_id is not None:
            self.draft_email_requested.emit(self._job_id)
