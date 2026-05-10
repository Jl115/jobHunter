"""Email preview widget with editable draft and mailto: action."""

import logging
import urllib.parse
import webbrowser

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from features.email import EmailComposer
from features.jobs import JobRepository
from features.resume import ResumeRepository
from shared.models import EmailDraft

logger = logging.getLogger(__name__)


class EmailPreviewWidget(QWidget):
    """Display and edit a drafted email before opening the mail client."""

    back_requested: Signal = Signal()
    """Emitted when the user clicks 'Back to Job'."""

    def __init__(
        self,
        job_repository: JobRepository | None = None,
        resume_repository: ResumeRepository | None = None,
        email_composer: EmailComposer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._job_id: int | None = None
        self._draft: EmailDraft | None = None
        self._job_repository = job_repository
        self._resume_repository = resume_repository
        self._email_composer = email_composer

        layout = QVBoxLayout(self)

        # Subject
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Subject:"))
        self._subject_edit = QTextEdit()
        self._subject_edit.setMaximumHeight(40)
        self._subject_edit.setReadOnly(True)
        subject_layout.addWidget(self._subject_edit)
        layout.addLayout(subject_layout)

        # Body
        layout.addWidget(QLabel("Body:"))
        self._body_edit = QTextEdit()
        self._body_edit.setReadOnly(True)
        layout.addWidget(self._body_edit)

        # Buttons
        buttons = QHBoxLayout()
        self._edit_btn = QPushButton("Edit Draft")
        self._edit_btn.setCheckable(True)
        self._edit_btn.toggled.connect(self._toggle_edit)

        self._send_btn = QPushButton("Open in Mail Client")
        self._send_btn.clicked.connect(self._open_mail_client)

        self._back_btn = QPushButton("Back to Job")
        self._back_btn.clicked.connect(self.back_requested.emit)

        buttons.addWidget(self._edit_btn)
        buttons.addWidget(self._send_btn)
        buttons.addWidget(self._back_btn)
        layout.addLayout(buttons)

    def load_draft(self, job_id: int) -> None:
        """Load an email draft for the given job ID using the EmailComposer."""
        self._job_id = job_id

        if self._email_composer is None or self._job_repository is None:
            self._draft = self._placeholder_draft(job_id)
        else:
            job = self._job_repository.get_by_id(job_id)
            if job is None:
                self._draft = self._placeholder_draft(job_id)
            else:
                resume = (
                    self._resume_repository.get_latest()
                    if self._resume_repository
                    else None
                )
                self._draft = self._email_composer.compose(job, resume)
                logger.info(
                    "Generated draft for job %d: subject=%s",
                    job_id,
                    self._draft.subject,
                )

        self._subject_edit.setPlainText(self._draft.subject)
        self._body_edit.setPlainText(self._draft.body)
        self._subject_edit.setReadOnly(True)
        self._body_edit.setReadOnly(True)
        self._edit_btn.setChecked(False)
        self._edit_btn.setText("Edit Draft")

    def _placeholder_draft(self, job_id: int) -> EmailDraft:
        """Return a fallback draft when data is unavailable."""
        return EmailDraft(
            subject=f"Application for job #{job_id}",
            body="Dear Hiring Manager,\n\nI am writing to apply...",
            recipient=None,
            job_id=job_id,
        )

    def _toggle_edit(self, checked: bool) -> None:
        """Toggle read-only mode for the subject and body fields."""
        self._subject_edit.setReadOnly(not checked)
        self._body_edit.setReadOnly(not checked)
        self._edit_btn.setText("Done Editing" if checked else "Edit Draft")

    def _open_mail_client(self) -> None:
        """Build a mailto: URL and open the default email client."""
        if self._draft is None:
            return
        subject = self._subject_edit.toPlainText()
        body = self._body_edit.toPlainText()

        params = urllib.parse.urlencode(
            {"subject": subject, "body": body},
            quote_via=urllib.parse.quote,
        )
        mailto_url = f"mailto:?{params}"

        logger.info("Opening mailto URL for job %s", self._job_id)
        webbrowser.open(mailto_url)
        QMessageBox.information(
            self, "Email Client", "Your default email client should now open with the draft pre-filled."
        )
