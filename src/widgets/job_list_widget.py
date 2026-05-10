"""Futuristic job list with rich cards, badges, and live filters."""

import logging

from PySide6 import QtGui
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from features.jobs import JobRepository
from shared.app_state import AppState
from shared.models import Job
from .theme import QuantumTheme

logger = logging.getLogger(__name__)


class SourceBadge(QLabel):
    """Platform source badge with brand colours."""

    _PALETTES: dict[str, tuple[str, str]] = {
        "linkedin": (QuantumTheme.BADGE_LINKEDIN, "#ffffff"),
        "indeed": (QuantumTheme.BADGE_INDEED, "#ffffff"),
        "xing": (QuantumTheme.BADGE_XING, "#ffffff"),
    }

    def __init__(self, source: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        key = source.lower().split()[0] if source else ""
        bg, fg = self._PALETTES.get(key, (QuantumTheme.ACCENT_SECONDARY, "#ffffff"))
        self.setText(source.upper() if source else "OTHER")
        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            """
        )
        self.setMaximumWidth(120)


class MatchPill(QLabel):
    """Coloured match-score pill."""

    def __init__(self, score: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(70)
        self.set_score(score)

    def set_score(self, score: float) -> None:
        colour = QuantumTheme.score_color(score)
        self.setText(f"{score:.0%}")
        self.setStyleSheet(
            f"""
            QLabel {{
                background-color: {QuantumTheme.BG_DEEP};
                color: {colour};
                border: 1px solid {colour};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )


class StatusDot(QLabel):
    """Small status indicator dot."""

    _COLOURS = {
        "new": QuantumTheme.ACCENT_PRIMARY,
        "extracting": QuantumTheme.BORDER_WARNING,
        "extracted": QuantumTheme.BORDER_SUCCESS,
        "failed": QuantumTheme.BORDER_DANGER,
    }

    def __init__(self, status: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        colour = self._COLOURS.get(status.lower(), QuantumTheme.BORDER)
        self.setText(f"\u25cf  {status.upper()}")
        self.setStyleSheet(
            f"""
            QLabel {{
                color: {colour};
                font-size: 11px;
                font-weight: 600;
                padding: 2px 0;
            }}
            """
        )


class JobListWidget(QWidget):
    """Display scraped jobs in a modern sortable table with search."""

    job_selected: Signal = Signal(int)
    """Emitted when the user clicks a job row. Carries the job ID."""

    def __init__(self, job_repository: JobRepository | None = None) -> None:
        super().__init__()
        self._repository = job_repository

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # ═══════════════ Header Bar ════════════════
        header = QHBoxLayout()
        header.setSpacing(12)

        self._count_label = QLabel("Your Opportunities")
        self._count_label.setObjectName("heading")
        self._count_label.setStyleSheet(
            f"color: {QuantumTheme.TEXT_PRIMARY}; font-size: {QuantumTheme.SIZE_HERO}; font-weight: 800;"
        )
        header.addWidget(self._count_label)

        self._subtitle = QLabel("0 jobs found")
        self._subtitle.setObjectName("muted")
        self._subtitle.setStyleSheet(f"color: {QuantumTheme.TEXT_MUTED}; font-size: 13px;")
        header.addWidget(self._subtitle)
        header.addStretch()

        # Search with icon placeholder
        self._search = QLineEdit()
        self._search.setPlaceholderText("\U0001F50E  Search by title or company...")
        self._search.setFixedWidth(320)
        self._search.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {QuantumTheme.BG_CARD};
                color: {QuantumTheme.TEXT_PRIMARY};
                border: 1px solid {QuantumTheme.BORDER};
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {QuantumTheme.BORDER_FOCUS};
            }}
            """
        )
        self._search.textChanged.connect(self._apply_filter)
        header.addWidget(self._search)
        layout.addLayout(header)

        # ═══════════════ Table ════════════════
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "", "Role", "Company", "Source", "Match", "",
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(56)
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: transparent;
                alternate-background-color: {QuantumTheme.BG_CARD};
                border: 1px solid {QuantumTheme.BORDER};
                gridline-color: transparent;
                selection-background-color: {QuantumTheme.BG_HOVER};
                selection-color: {QuantumTheme.TEXT_PRIMARY};
                outline: none;
                border-radius: 16px;
            }}
            QTableWidget::item {{
                padding: 14px 18px;
                border-bottom: 1px solid {QuantumTheme.BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {QuantumTheme.BG_HOVER};
                color: {QuantumTheme.ACCENT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: {QuantumTheme.TEXT_PRIMARY};
                padding: 14px 18px;
                font-weight: 600;
                font-size: {QuantumTheme.SIZE_SMALL};
                text-transform: uppercase;
                letter-spacing: 1px;
                border: none;
                border-bottom: 2px solid {QuantumTheme.BORDER};
            }}
            QTableCornerButton::section {{
                background-color: transparent;
                border-bottom: 2px solid {QuantumTheme.BORDER};
            }}
            """
        )
        layout.addWidget(self._table, stretch=1)

        # Refresh when database changes
        AppState.get_instance().jobs_updated.connect(self.refresh)

    def refresh(self) -> None:
        """Reload job data from the database and repopulate the table."""
        if self._repository is None:
            self._table.setRowCount(0)
            logger.warning("JobListWidget has no repository")
            return
        jobs = self._repository.list_all()
        self.populate(jobs)
        logger.debug("Job list refreshed with %d rows", len(jobs))

    def populate(self, jobs: list[Job]) -> None:
        """Populate the table with rich job data."""
        self._count_label.setText(f"Your Opportunities")
        self._subtitle.setText(f"{len(jobs)} {'job' if len(jobs) == 1 else 'jobs'} found")
        self._table.setRowCount(len(jobs))
        self._table.blockSignals(True)

        for row, job in enumerate(jobs):
            # Status dot
            status_dot = StatusDot(job.status.value)
            self._table.setCellWidget(row, 0, status_dot)

            # Title bold (store job ID in UserRole)
            title_item = QTableWidgetItem(job.title or "—")
            title_item.setFont(
                QtGui.QFont(QuantumTheme.FONT_FAMILY.split(",")[0].strip(), 13, QtGui.QFont.Weight.Bold)
            )
            title_item.setData(Qt.ItemDataRole.UserRole, job.id)
            self._table.setItem(row, 1, title_item)

            # Company
            self._table.setItem(row, 2, QTableWidgetItem(job.company or "—"))

            # Source badge
            source_badge = SourceBadge(job.source)
            self._table.setCellWidget(row, 3, source_badge)

            # Match pill
            match_pill = MatchPill(job.match_score)
            self._table.setCellWidget(row, 4, match_pill)

            # Status text
            self._table.setItem(row, 5, QTableWidgetItem(job.status.value.upper()))

        self._table.blockSignals(False)

    def _apply_filter(self, text: str) -> None:
        """Live filter on the Title and Company columns."""
        text_lower = text.lower()
        visible_count = 0
        for row in range(self._table.rowCount()):
            title = self._table.item(row, 1).text().lower()
            company = self._table.item(row, 2).text().lower()
            visible = text_lower in title or text_lower in company
            self._table.setRowHidden(row, not visible)
            if visible:
                visible_count += 1
        self._subtitle.setText(f"{visible_count} {'job' if visible_count == 1 else 'jobs'} found")

    def _on_cell_clicked(self, row: int, _column: int) -> None:
        """Emit the selected job ID when a row is clicked."""
        # Job ID is stored in UserRole of the title (column 1)
        item = self._table.item(row, 1)
        if item is None:
            return
        job_id = item.data(Qt.ItemDataRole.UserRole)
        if job_id is not None and isinstance(job_id, int):
            self.job_selected.emit(job_id)
