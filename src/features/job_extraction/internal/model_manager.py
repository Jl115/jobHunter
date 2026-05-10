"""Universal model cache manager — single source of truth for all ML models."""

import logging
import os
from pathlib import Path

import requests
from shared.constants import DEFAULT_GGUF_MODEL, DEFAULT_SENTENCE_MODEL, MODELS_CACHE_DIR

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages download, caching, and path resolution for all ML models.

    Handles both GGUF (llama-cpp) and sentence-transformer models.
    """

    def __init__(
        self,
        gguf_model_name: str = DEFAULT_GGUF_MODEL,
        sentence_model_name: str = DEFAULT_SENTENCE_MODEL,
        cache_dir: Path = MODELS_CACHE_DIR,
    ) -> None:
        self.gguf_model_name = gguf_model_name
        self.sentence_model_name = sentence_model_name
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── GGUF Models ───────────────────────────────────────────────

    def get_gguf_model_path(self) -> Path:
        """Return the local path to the GGUF model, downloading if needed."""
        model_path = self.cache_dir / self.gguf_model_name
        if not model_path.exists():
            self._download_gguf(model_path)
        return model_path

    def is_gguf_available(self) -> bool:
        """Check whether the GGUF model is already cached locally."""
        return (self.cache_dir / self.gguf_model_name).exists()

    def _download_gguf(self, destination: Path) -> None:
        """Download the GGUF model from HuggingFace.

        Defaults to the Qwen2.5-3B-Instruct Q4_K_M quant.
        """
        from shared.constants import DEFAULT_GGUF_REPO

        url = (
            f"https://huggingface.co/{DEFAULT_GGUF_REPO}/resolve/main/"
            f"{self.gguf_model_name}"
        )
        logger.info("Downloading GGUF model from %s ...", url)
        self._download_with_progress(url, destination)
        logger.info("GGUF model saved to %s", destination)

    # ── Sentence-Transformer Models ───────────────────────────────

    def get_sentence_model_path(self) -> Path:
        """Return the local cache directory for the sentence-transformer model."""
        model_dir = self.cache_dir / "sentence_transformers" / self.sentence_model_name
        if not model_dir.exists():
            logger.info(
                "Sentence-transformer model '%s' will be downloaded on first use.",
                self.sentence_model_name,
            )
        return model_dir

    def is_sentence_model_available(self) -> bool:
        """Check whether the sentence-transformer model is cached."""
        model_dir = self.cache_dir / "sentence_transformers" / self.sentence_model_name
        return model_dir.exists()

    # ── Shared Download Helper ────────────────────────────────────

    @staticmethod
    def _download_with_progress(url: str, destination: Path, chunk_size: int = 8192) -> None:
        """Stream-download a file with basic progress logging."""
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0 and downloaded % (5 * 1024 * 1024) == 0:
                        pct = downloaded / total * 100
                        logger.info("Download progress: %.1f%%", pct)
