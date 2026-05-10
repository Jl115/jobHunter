"""Singleton reactive application state using Qt Signals."""

from typing import ClassVar

from PySide6.QtCore import QObject, Signal


class AppState(QObject):
    """Global reactive state singleton.

    Features connect to these signals to react to cross-cutting events
    without direct imports of each other's internals.

    Created lazily via ``get_instance()`` and lives for the application lifetime.
    """

    jobs_updated: Signal = Signal()
    """Emitted when the jobs table is modified (insert, update, delete)."""

    resume_uploaded: Signal = Signal(int)
    """Emitted when a new resume is uploaded. Carries the resume ID."""

    extraction_completed: Signal = Signal(int)
    """Emitted when LLM extraction finishes for a job. Carries the job ID."""

    email_drafted: Signal = Signal(int)
    """Emitted when an email draft is generated. Carries the job ID."""

    _instance: ClassVar["AppState | None"] = None

    def __init__(self, parent: QObject | None = None) -> None:
        """Guard against re-initialising the singleton's C++ side."""
        if hasattr(self, "_qobject_initialized"):
            return
        super().__init__(parent)
        self._qobject_initialized = True

    @classmethod
    def get_instance(cls) -> "AppState":
        """Return the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
