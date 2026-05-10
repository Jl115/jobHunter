"""Application-wide constants."""

from pathlib import Path

DEFAULT_PORT: int = 8080
"""Default port for the FastAPI local server."""

DATABASE_PATH: Path = Path.home() / ".local" / "share" / "job_hunter" / "job_hunter.db"
"""Path to the SQLite database file."""

MODELS_CACHE_DIR: Path = Path.home() / ".cache" / "job_hunter" / "models"
"""Directory where GGUF and sentence-transformer models are cached."""

CORS_ORIGINS: list[str] = ["chrome-extension://*"]
"""Allowed CORS origins for the FastAPI server."""

DEFAULT_GGUF_REPO: str = "Qwen/Qwen2.5-3B-Instruct-GGUF"
"""HuggingFace repo ID that hosts quantized GGUF files (ungated)."""

DEFAULT_GGUF_MODEL: str = "qwen2.5-3b-instruct-q4_k_m.gguf"
"""Default local LLM model file for job field extraction (~1.8 GB)."""

DEFAULT_SENTENCE_MODEL: str = "all-MiniLM-L6-v2"
"""Default sentence-transformer model for semantic matching."""
