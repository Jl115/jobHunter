"""Lightweight in-memory job cache invalidated by AppState signals."""

from typing import ClassVar

from PySide6.QtCore import QObject

from shared.app_state import AppState
from shared.models import Job


class JobStore(QObject):
    """Simple in-memory cache for the job list.

    Invalidated whenever ``AppState.jobs_updated`` is emitted.
    """

    _instance: ClassVar["JobStore | None"] = None

    def __new__(cls) -> "JobStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, parent=None) -> None:
        if hasattr(self, "_initialised"):
            return
        super().__init__(parent)
        self._jobs: list[Job] = []
        AppState.get_instance().jobs_updated.connect(self.invalidate)
        self._initialised = True

    @classmethod
    def get_instance(cls) -> "JobStore":
        """Return the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_jobs(self, jobs: list[Job]) -> None:
        """Populate the cache."""
        self._jobs = jobs

    def get_jobs(self) -> list[Job]:
        """Return cached jobs."""
        return list(self._jobs)

    def invalidate(self) -> None:
        """Clear the cache so the next read hits the database."""
        self._jobs = []
