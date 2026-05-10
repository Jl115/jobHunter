"""PySide6 widget layer public API."""

from .email_preview_widget import EmailPreviewWidget
from .job_detail_widget import JobDetailWidget
from .job_list_widget import JobListWidget
from .main_window import MainWindow

__all__ = [
    "MainWindow",
    "JobListWidget",
    "JobDetailWidget",
    "EmailPreviewWidget",
]
