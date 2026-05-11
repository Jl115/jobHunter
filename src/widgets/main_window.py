"""Modern main application window with custom title bar, sidebar, and content stack."""

import logging

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .email_preview_widget import EmailPreviewWidget
from .job_detail_widget import JobDetailWidget
from .job_list_widget import JobListWidget
from .theme import QuantumTheme

logger = logging.getLogger(__name__)


class TitleBar(QWidget):
    """Custom title bar with draggable support and macOS-style controls."""

    def __init__(self, parent: QMainWindow) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {QuantumTheme.BG_BASE};")

        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Window controls (macOS-style traffic lights on all platforms)
        controls = QHBoxLayout()
        controls.setSpacing(8)

        self._btn_close = self._control_button("#ff5f57", "#e0443e")
        self._btn_close.clicked.connect(parent.close)
        controls.addWidget(self._btn_close)

        self._btn_min = self._control_button("#febc2e", "#e5a82a")
        self._btn_min.clicked.connect(parent.showMinimized)
        controls.addWidget(self._btn_min)

        self._btn_max = self._control_button("#28c840", "#24b53a")
        self._btn_max.clicked.connect(self._toggle_maximized)
        controls.addWidget(self._btn_max)

        layout.addLayout(controls)

        # Title
        self._title = QLabel("Job Hunter")
        self._title.setStyleSheet(
            f"color: {QuantumTheme.TEXT_SECONDARY}; font-size: 13px; font-weight: 600; background: transparent;"
        )
        layout.addWidget(self._title, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    @staticmethod
    def _control_button(colour: str, hover: str) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(12, 12)
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {colour};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            """
        )
        return btn

    def _toggle_maximized(self) -> None:
        if self._parent.isMaximized():
            self._parent.showNormal()
        else:
            self._parent.showMaximized()

    def mousePressEvent(self, event) -> None:
        """Track the mouse position at the start of a drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self._parent.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Drag the window by moving it relative to the tracked offset."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self._drag_pos is not None:
                self._parent.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        """Double-click to toggle maximize/restore."""
        self._toggle_maximized()
        event.accept()


class MainWindow(QMainWindow):
    """Frameless main window with sidebar navigation and stacked content views."""

    def __init__(
        self,
        job_repository=None,
        resume_repository=None,
        job_matcher=None,
        email_composer=None,
        thread_pool=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._job_repository = job_repository
        self._resume_repository = resume_repository
        self._job_matcher = job_matcher
        self._email_composer = email_composer
        self._thread_pool = thread_pool

        # Frameless for custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # --- Central widget & layout ---
        container = QWidget()
        container.setStyleSheet(
            f"background-color: {QuantumTheme.BG_DEEP}; padding-left: 10px; padding-right: 10px;"
        )
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar
        self._title_bar = TitleBar(self)
        main_layout.addWidget(self._title_bar)

        # Content area (sidebar + stack)
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            f"background-color: {QuantumTheme.BG_DEEP}; border-right: 1px solid {QuantumTheme.BORDER};"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(12)

        self._nav_jobs = QPushButton("Jobs")
        self._nav_jobs.setCheckable(True)
        self._nav_jobs.setChecked(True)
        self._nav_jobs.clicked.connect(lambda: self._show_page(0))
        sidebar_layout.addWidget(self._nav_jobs)

        sidebar_layout.addStretch()

        # Status at bottom
        self._status_label = QLabel("Server: Stopped")
        self._status_label.setStyleSheet(
            f"color: {QuantumTheme.TEXT_MUTED}; font-size: 11px;"
        )
        sidebar_layout.addWidget(self._status_label)

        content.addWidget(sidebar)

        # --- Stacked Widget ---
        self._stack = QStackedWidget()

        # Page 0: Job List
        self._job_list = JobListWidget(job_repository=job_repository)
        self._job_list.job_selected.connect(self._on_job_selected)
        self._stack.addWidget(self._job_list)

        # Page 1: Job Detail
        self._job_detail = JobDetailWidget(
            job_repository=job_repository,
            resume_repository=resume_repository,
            job_matcher=job_matcher,
            thread_pool=thread_pool,
        )
        self._job_detail.draft_email_requested.connect(self._on_draft_email)
        self._stack.addWidget(self._job_detail)

        # Page 2: Email Preview
        self._email_preview = EmailPreviewWidget(
            job_repository=job_repository,
            resume_repository=resume_repository,
            email_composer=email_composer,
        )
        self._email_preview.back_requested.connect(lambda: self._show_page(1))
        self._stack.addWidget(self._email_preview)

        content.addWidget(self._stack, stretch=1)

        main_layout.addLayout(content, stretch=1)

        # Initial page
        self._show_page(0)

    # --- Navigation ---
    def _show_page(self, index: int) -> None:
        """Switch the visible content page."""
        self._stack.setCurrentIndex(index)

    def _on_job_selected(self, job_id: int) -> None:
        """Load a job into the detail view and switch to it."""
        self._show_page(1)
        self._job_detail.load_job(job_id)

    def _on_draft_email(self, job_id: int) -> None:
        """Load an email draft and switch to the email page."""
        self._email_preview.load_draft(job_id)
        self._show_page(2)

    # --- Public API ---
    def set_server_status(self, running: bool) -> None:
        """Update the server status label in the sidebar."""
        color = QuantumTheme.BORDER_SUCCESS if running else QuantumTheme.BORDER_DANGER
        self._status_label.setText(f"Server: {'Running' if running else 'Stopped'}")
        self._status_label.setStyleSheet(f"color: {color}; font-size: 11px;")

    def refresh_job_list(self) -> None:
        """Trigger a refresh on the job list widget."""
        self._job_list.refresh()
