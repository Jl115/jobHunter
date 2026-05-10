"""Shared contracts, state, and constants across the application."""

from .app_state import AppState
from .constants import DEFAULT_PORT, DATABASE_PATH, MODELS_CACHE_DIR, CORS_ORIGINS
from .models import EmailDraft, Job, JobCapturePayload, JobStatus, Resume

__all__ = [
    "AppState",
    "DEFAULT_PORT",
    "DATABASE_PATH",
    "MODELS_CACHE_DIR",
    "CORS_ORIGINS",
    "EmailDraft",
    "Job",
    "JobCapturePayload",
    "JobStatus",
    "Resume",
]
