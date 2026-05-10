"""Main application window with QStackedWidget for view navigation."""

import logging
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from features.email import EmailComposer
from features.jobs import JobMatcher, JobRepository
from features.resume import ResumeRepository
from shared.models import Job

from .email_preview_widget import EmailPreviewWidget
from .job_detail_widget import JobDetailWidget
from .job_list_widget import JobListWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary desktop window hosting a stacked widget for view switching."""

    INDEX_LIST: int = 0
    INDEX_DETAIL: int = 1
    INDEX_EMAIL: int = 2

    def __init__(
        self,
        job_repository: JobRepository,
        resume_repository: ResumeRepository,
        job_matcher: JobMatcher,
        email_composer: EmailComposer,
        thread_pool: Any,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Job Hunter")
        self.resize(1200, 800)

        # Store injected dependencies
        self._job_repository = job_repository
        self._resume_repository = resume_repository
        self._job_matcher = job_matcher
        self._email_composer = email_composer
        self._thread_pool = thread_pool

        # Central stacked widget
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # Views with dependencies
        self._job_list = JobListWidget(job_repository=job_repository)
        self._job_detail = JobDetailWidget(
            job_repository=job_repository,
            resume_repository=resume_repository,
            job_matcher=job_matcher,
            thread_pool=thread_pool,
        )
        self._email_preview = EmailPreviewWidget(
            job_repository=job_repository,
            resume_repository=resume_repository,
            email_composer=email_composer,
        )

        self._stack.addWidget(self._job_list)
        self._stack.addWidget(self._job_detail)
        self._stack.addWidget(self._email_preview)

        # Toolbar
        self._toolbar = QToolBar()
        self.addToolBar(self._toolbar)
        self._toolbar.addAction("Jobs", lambda: self.show_view(self.INDEX_LIST))
        self._toolbar.addAction("Back", lambda: self.show_view(self.INDEX_DETAIL))

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._server_label = QLabel("Server: starting...")
        self._status.addPermanentWidget(self._server_label)

        # Wire signals
        self._job_list.job_selected.connect(self._on_job_selected)
        self._job_detail.draft_email_requested.connect(self._on_draft_email)
        self._email_preview.back_requested.connect(
            lambda: self.show_view(self.INDEX_DETAIL)
        )

    def show_view(self, index: int) -> None:
        """Switch the stacked widget to the given view index."""
        self._stack.setCurrentIndex(index)

    def set_server_status(self, running: bool) -> None:
        """Update the status bar label to reflect server health."""
        text = "Server: running" if running else "Server: stopped"
        self._server_label.setText(text)

    def refresh_job_list(self) -> None:
        """Reload jobs from repository and populate the list widget."""
        jobs = self._job_repository.list_all()
        self._job_list.populate(jobs)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_job_selected(self, job_id: int) -> None:
        """User clicked a job in the list — show detail view."""
        logger.info("Selected job %d", job_id)
        self._job_detail.load_job(job_id)
        self.show_view(self.INDEX_DETAIL)

    def _on_draft_email(self, job_id: int) -> None:
        """User requested an email draft — show preview view."""
        logger.info("Draft email for job %d", job_id)
        self._email_preview.load_draft(job_id)
        self.show_view(self.INDEX_EMAIL)
