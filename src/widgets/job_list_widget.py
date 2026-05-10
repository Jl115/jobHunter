"""Job list view with a QTableWidget for browsing scraped jobs."""

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from features.jobs import JobRepository
from shared.app_state import AppState
from shared.models import Job

logger = logging.getLogger(__name__)


class JobListWidget(QWidget):
    """Display scraped jobs in a sortable table."""

    job_selected: Signal = Signal(int)
    """Emitted when the user clicks a job row. Carries the job ID."""

    def __init__(self, job_repository: JobRepository | None = None) -> None:
        super().__init__()
        self._repository = job_repository

        self._layout = QVBoxLayout(self)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "ID", "Title", "Company", "Source", "Score", "Status",
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.cellClicked.connect(self._on_cell_clicked)

        self._layout.addWidget(self._table)

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
        """Populate the table with job data."""
        self._table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            self._table.setItem(row, 0, QTableWidgetItem(str(job.id)))
            self._table.setItem(row, 1, QTableWidgetItem(job.title or "—"))
            self._table.setItem(row, 2, QTableWidgetItem(job.company or "—"))
            self._table.setItem(row, 3, QTableWidgetItem(job.source))
            self._table.setItem(row, 4, QTableWidgetItem(f"{job.match_score:.0%}"))
            self._table.setItem(row, 5, QTableWidgetItem(job.status.value))

    def _on_cell_clicked(self, row: int, _column: int) -> None:
        """Emit the selected job ID when a row is clicked."""
        item = self._table.item(row, 0)
        if item is not None:
            self.job_selected.emit(int(item.text()))
