"""Premium 2027 email preview with split-pane editor and live preview."""

import logging
import urllib.parse
import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from features.email import EmailComposer
from features.jobs import JobRepository
from features.resume import ResumeRepository
from shared.models import EmailDraft
from .theme import QuantumTheme

logger = logging.getLogger(__name__)


class EmailPreviewWidget(QWidget):
    """Split-pane email composer with live preview and mailto action."""

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
        self._editing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # ═══════════════ Header ════════════════
        header = QHBoxLayout()
        self._header_label = QLabel("Draft Email")
        self._header_label.setObjectName("heading")
        self._header_label.setStyleSheet(
            f"color: {QuantumTheme.TEXT_PRIMARY}; font-size: {QuantumTheme.SIZE_HERO}; font-weight: 800;"
        )
        header.addWidget(self._header_label)
        header.addStretch()
        layout.addLayout(header)

        # ═══════════════ Split Pane ════════════════
        splitter = QSplitter()
        splitter.setStyleSheet(
            f"""
            QSplitter::handle {{
                background-color: {QuantumTheme.BORDER};
                width: 2px;
            }}
            """
        )

        # Editor pane
        editor_widget = self._build_editor_pane()
        splitter.addWidget(editor_widget)

        # Preview pane
        preview_widget = self._build_preview_pane()
        splitter.addWidget(preview_widget)

        # Equal split
        splitter.setSizes([600, 600])
        layout.addWidget(splitter, stretch=1)

        # ═══════════════ Action Bar ════════════════
        action_bar = QWidget()
        action_bar.setStyleSheet("background: transparent;")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(12)
        action_layout.addStretch()

        self._edit_btn = QPushButton("✎  Edit Draft")
        self._edit_btn.setObjectName("primary")
        self._edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_btn.clicked.connect(self._toggle_edit)
        action_layout.addWidget(self._edit_btn)

        self._send_btn = QPushButton("✉  Open in Mail Client")
        self._send_btn.setObjectName("success")
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.clicked.connect(self._open_mail_client)
        action_layout.addWidget(self._send_btn)

        self._back_btn = QPushButton("←  Back to Job")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self.back_requested.emit)
        action_layout.addWidget(self._back_btn)

        layout.addWidget(action_bar)

    def _build_editor_pane(self) -> QWidget:
        """Build the editable side of the split."""
        w = QWidget()
        QuantumTheme.apply_card_shadow(w)
        v = QVBoxLayout(w)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)

        sub = QLabel("Editor")
        sub.setObjectName("subtitle")
        sub.setStyleSheet(
            f"color: {QuantumTheme.TEXT_PRIMARY}; font-size: {QuantumTheme.SIZE_SUBTITLE}; font-weight: 700;"
        )
        v.addWidget(sub)

        # Subject
        v.addWidget(self._m_label("Subject"))
        self._subject_edit = QTextEdit()
        self._subject_edit.setMaximumHeight(44)
        self._subject_edit.setPlaceholderText("Email subject...")
        v.addWidget(self._subject_edit)

        # Body
        v.addWidget(self._m_label("Body"))
        self._body_edit = QTextEdit()
        self._body_edit.setPlaceholderText("Email body...")
        v.addWidget(self._body_edit)

        self._subject_edit.setReadOnly(True)
        self._body_edit.setReadOnly(True)

        return w

    def _build_preview_pane(self) -> QWidget:
        """Build the rendered-preview side of the split with accent accents."""
        w = QWidget()
        QuantumTheme.apply_card_shadow(w)
        v = QVBoxLayout(w)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)

        sub = QLabel("Preview")
        sub.setObjectName("subtitle")
        sub.setStyleSheet(
            f"color: {QuantumTheme.TEXT_PRIMARY}; font-size: {QuantumTheme.SIZE_SUBTITLE}; font-weight: 700;"
        )
        v.addWidget(sub)

        self._subject_preview = QLabel("—")
        self._subject_preview.setStyleSheet(
            f"color: {QuantumTheme.TEXT_PRIMARY}; font-size: {QuantumTheme.SIZE_TITLE}; font-weight: 700; padding: 8px 0;"
        )
        self._subject_preview.setWordWrap(True)
        v.addWidget(self._subject_preview)

        self._body_preview = QLabel("—")
        self._body_preview.setStyleSheet(
            f"color: {QuantumTheme.TEXT_SECONDARY}; font-size: {QuantumTheme.SIZE_BODY}; line-height: 1.6;"
        )
        self._body_preview.setWordWrap(True)
        self._body_preview.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        v.addWidget(self._body_preview)

        v.addStretch()

        return w

    @staticmethod
    def _m_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {QuantumTheme.TEXT_MUTED}; font-size: {QuantumTheme.SIZE_SMALL}; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;"
        )
        return lbl

    # ── Data Loading ─────────────────────────────────────────────────

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
        self._editing = False
        self._edit_btn.setText("✎  Edit Draft")

        self._update_preview()

    def _update_preview(self) -> None:
        """Sync editor content to preview pane."""
        self._subject_preview.setText(self._subject_edit.toPlainText())
        # Convert plain text to HTML-like line breaks for preview
        body = self._body_edit.toPlainText()
        body_html = body.replace("\n", "<br/>")
        self._body_preview.setText(body_html)

    def _placeholder_draft(self, job_id: int) -> EmailDraft:
        """Return a fallback draft when data is unavailable."""
        return EmailDraft(
            subject=f"Application for job #{job_id}",
            body="Dear Hiring Manager,\n\nI am writing to apply...",
            recipient=None,
            job_id=job_id,
        )

    # ── Interaction ──────────────────────────────────────────────────

    def _toggle_edit(self) -> None:
        """Toggle read-only mode for the subject and body fields."""
        self._editing = not self._editing
        self._subject_edit.setReadOnly(not self._editing)
        self._body_edit.setReadOnly(not self._editing)
        self._edit_btn.setText("Done Editing" if self._editing else "✎  Edit Draft")
        self._edit_btn.setObjectName("primary" if not self._editing else "success")

        if not self._editing:
            # Sync back to preview
            self._update_preview()

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
