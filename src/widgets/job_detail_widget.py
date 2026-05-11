"""Premium 2027 job detail view with hero header, compact top-right stats, and full-width description."""

import logging
import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from features.jobs import JobMatcher, JobRepository
from features.resume import ResumeExtractor, ResumeParser, ResumeRepository
from shared.app_state import AppState
from workers import MatchWorker
from .theme import QuantumTheme
from .markdown_viewer import MarkdownViewer

logger = logging.getLogger(__name__)


class _Card(QFrame):
    """Elevated card with subtle border and optional padding."""

    def __init__(
        self,
        title: str = "",
        padding: int = 24,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(16)

        if title:
            heading = QLabel(title)
            heading.setObjectName("subtitle")
            heading.setStyleSheet(
                f"color: {QuantumTheme.TEXT_PRIMARY}; font-size: {QuantumTheme.SIZE_SUBTITLE}; font-weight: 700;"
            )
            self._layout.addWidget(heading)

        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(12)
        self._layout.addWidget(self._body)

        QuantumTheme.apply_card_shadow(self)

    @property
    def body(self) -> QVBoxLayout:
        return self._body_layout


class _OpenLinkButton(QPushButton):
    """Compact pill button that opens a URL in the default browser."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Open Link", parent)
        self._url = ""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {QuantumTheme.BG_INPUT};
                color: {QuantumTheme.ACCENT_PRIMARY};
                border: 1px solid {QuantumTheme.BORDER};
                border-radius: 10px;
                padding: 4px 14px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {QuantumTheme.BG_CARD};
                border-color: {QuantumTheme.ACCENT_PRIMARY};
            }}
            """
        )
        self.clicked.connect(self._on_click)

    def set_url(self, url: str) -> None:
        """Store the URL and enable/disable the button."""
        self._url = url
        self.setEnabled(bool(url))
        # Show full URL as tooltip
        self.setToolTip(url if url else "")

    def _on_click(self) -> None:
        if self._url:
            webbrowser.open(self._url)


class _ScoreBadge(QLabel):
    """Compact coloured match-score badge."""

    def __init__(self, score: float = 0.0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.set_score(score)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_score(self, score: float) -> None:
        colour = QuantumTheme.score_color(score)
        label = QuantumTheme.score_label(score)
        font_size = "13px" if score >= 0.8 else "12px"
        self.setText(f"<b>{score:.0%}</b>  <span style='font-size:10px;opacity:0.8;'>{label}</span>")
        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {colour};
                color: {QuantumTheme.BG_DEEP};
                border-radius: 12px;
                padding: 4px 12px;
                font-size: {font_size};
                font-weight: 800;
            }}
            """
        )


class _InfoPill(QLabel):
    """Small metadata pill (icon + text)."""

    def __init__(self, icon: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setText(f" {icon}  {text}")
        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {QuantumTheme.BG_INPUT};
                color: {QuantumTheme.TEXT_SECONDARY};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            """
        )


class JobDetailWidget(QWidget):
    """Premium 2027 job detail with hero stats, full-width description, and action bar."""

    draft_email_requested: Signal = Signal(int)

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # ═══════════════ Hero Card ════════════════
        self._hero_card = _Card(padding=28)
        hero = self._hero_card.body

        # Top row: Source/status on the LEFT, compact score + details on the RIGHT
        top = QHBoxLayout()
        top.setSpacing(10)

        # ── Left: Source & status badges
        self._source_badge = QLabel("LINKEDIN")
        self._source_badge.setObjectName("badge")
        self._source_badge.setStyleSheet(
            f"background-color: {QuantumTheme.BADGE_LINKEDIN}; color: #fff; border-radius: 8px; padding: 3px 12px; font-size: 10px; font-weight: 700;"
        )
        top.addWidget(self._source_badge)

        self._status_badge = QLabel("NEW")
        self._status_badge.setObjectName("badge")
        self._status_badge.setStyleSheet(
            f"background-color: {QuantumTheme.ACCENT_PRIMARY}; color: {QuantumTheme.BG_DEEP}; border-radius: 8px; padding: 3px 12px; font-size: 10px; font-weight: 700;"
        )
        top.addWidget(self._status_badge)

        self._extraction_status = QLabel("✓ Extracted")
        self._extraction_status.setStyleSheet(
            f"color: {QuantumTheme.BORDER_SUCCESS}; font-size: 12px; font-weight: 600;"
        )
        self._extraction_status.setVisible(False)
        top.addWidget(self._extraction_status)

        top.addStretch()

        # ── Right: compact score badge
        self._score_badge = _ScoreBadge()
        top.addWidget(self._score_badge)
        hero.addLayout(top)

        # ── Title (smaller hero size)
        self._title_label = QLabel("—")
        self._title_label.setObjectName("heading")
        self._title_label.setStyleSheet(
            f"color: {QuantumTheme.TEXT_PRIMARY}; font-size: {QuantumTheme.SIZE_TITLE}; font-weight: 800; letter-spacing: -0.3px; padding-top: 4px;"
        )
        self._title_label.setWordWrap(True)
        hero.addWidget(self._title_label)

        # ── Bottom row: Company + location pills (left), URL + scraped stacked (right)
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        # Left: company & location
        self._company_pill = _InfoPill("🏢", "—")
        bottom.addWidget(self._company_pill)
        self._location_pill = _InfoPill("📍", "—")
        bottom.addWidget(self._location_pill)

        bottom.addStretch()

        # Right: URL above scraped timestamp, vertically stacked
        details_stack = QVBoxLayout()
        details_stack.setSpacing(2)
        details_stack.setContentsMargins(0, 0, 0, 0)
        details_stack.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._url_label = _OpenLinkButton()
        details_stack.addWidget(self._url_label)

        self._scraped_label = QLabel("—")
        self._scraped_label.setStyleSheet(
            f"color: {QuantumTheme.TEXT_MUTED}; font-size: 11px;"
        )
        self._scraped_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        details_stack.addWidget(self._scraped_label)

        bottom.addLayout(details_stack)
        hero.addLayout(bottom)

        layout.addWidget(self._hero_card)

        # ═══════════════ Description (main, takes most space) ════════════════
        self._desc_card = _Card("Description")
        desc = self._desc_card.body
        self._markdown_viewer = MarkdownViewer()
        desc.addWidget(self._markdown_viewer)
        layout.addWidget(self._desc_card, stretch=1)

        # ═══════════════ Action Bar ════════════════
        action_bar = QFrame()
        action_bar.setStyleSheet(
            f"""
            QFrame {{
                background-color: {QuantumTheme.BG_CARD};
                border: 1px solid {QuantumTheme.BORDER};
                border-radius: 14px;
            }}
            """
        )
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(12)
        action_layout.addStretch()

        self._upload_btn = QPushButton("📄  Upload Resume")
        self._upload_btn.setObjectName("primary")
        self._upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._upload_btn.clicked.connect(self._upload_resume)
        action_layout.addWidget(self._upload_btn)

        self._match_btn = QPushButton("⬥  Match Resume")
        self._match_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._match_btn.clicked.connect(self._match_resume)
        action_layout.addWidget(self._match_btn)

        self._draft_btn = QPushButton("✉  Draft Email")
        self._draft_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._draft_btn.clicked.connect(self._draft_email)
        action_layout.addWidget(self._draft_btn)

        layout.addWidget(action_bar)

        # Listen for updates so score/description refresh automatically
        AppState.get_instance().jobs_updated.connect(self._on_jobs_updated)

    # ── Data Loading ─────────────────────────────────────────────────

    def load_job(self, job_id: int) -> None:
        """Load job data into the form."""
        self._job_id = job_id
        if self._repository is None:
            logger.warning("Detail widget has no repository; cannot load job %d", job_id)
            return
        job = self._repository.get_by_id(job_id)
        if job is None:
            self._clear_view()
            return

        # ── Hero ──
        self._title_label.setText(job.title or "Untitled Job")
        self._company_pill.setText(f" 🏢  {job.company or 'Unknown Company'} ")
        self._location_pill.setText(f" 📍  {job.location or 'Unknown Location'} ")

        # Source badge
        source = (job.source or "").lower()
        if "linkedin" in source:
            self._source_badge.setText("LINKEDIN")
            self._source_badge.setStyleSheet(
                f"background-color: {QuantumTheme.BADGE_LINKEDIN}; color: #fff; border-radius: 8px; padding: 3px 12px; font-size: 10px; font-weight: 700;"
            )
        elif "indeed" in source:
            self._source_badge.setText("INDEED")
            self._source_badge.setStyleSheet(
                f"background-color: {QuantumTheme.BADGE_INDEED}; color: #fff; border-radius: 8px; padding: 3px 12px; font-size: 10px; font-weight: 700;"
            )
        else:
            self._source_badge.setText(source.upper() if source else "OTHER")
            self._source_badge.setStyleSheet(
                f"background-color: {QuantumTheme.ACCENT_SECONDARY}; color: #fff; border-radius: 8px; padding: 3px 12px; font-size: 10px; font-weight: 700;"
            )

        # Status badge
        self._status_badge.setText(job.status.value.upper())
        status_colours = {
            "new": QuantumTheme.ACCENT_PRIMARY,
            "viewed": QuantumTheme.BORDER,
            "applied": QuantumTheme.BORDER_SUCCESS,
            "rejected": QuantumTheme.BORDER_DANGER,
        }
        status_colour = status_colours.get(job.status.value, QuantumTheme.BORDER)
        self._status_badge.setStyleSheet(
            f"background-color: {status_colour}; color: {QuantumTheme.BG_DEEP}; border-radius: 8px; padding: 3px 12px; font-size: 10px; font-weight: 700;"
        )

        # Extraction done indicator
        self._extraction_status.setVisible(job.status.value != "new")

        # ── Top-right stats (compact score + details) ──
        self._score_badge.set_score(job.match_score)
        if job.match_score > 0:
            self._score_badge.setToolTip("Matched against your uploaded resume")
        else:
            self._score_badge.setToolTip("Upload a resume to get a match score")

        self._url_label.set_url(job.url)
        self._scraped_label.setText(f"Scraped: {job.scraped_at}")

        # ── Description ──
        self._markdown_viewer.set_markdown(
            job.description_markdown or job.description or "No description extracted yet."
        )

        logger.info("Loaded job %d: %s at %s", job_id, job.title, job.company)

    def _clear_view(self) -> None:
        """Reset all fields when job not found."""
        self._title_label.setText("Not Found")
        self._company_pill.setText(" 🏢  Unknown ")
        self._location_pill.setText(" 📍  Unknown ")
        self._source_badge.setText("?")
        self._status_badge.setText("ERROR")
        self._score_badge.set_score(0.0)
        self._url_label.set_url("")
        self._scraped_label.setText("—")
        self._markdown_viewer.set_markdown("")

    def _on_jobs_updated(self) -> None:
        """If the currently displayed job changes behind the scenes, refresh it."""
        if self._job_id is not None:
            self.load_job(self._job_id)

    # ── Actions ──────────────────────────────────────────────────────

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
