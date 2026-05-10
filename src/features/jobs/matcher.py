"""Semantic job-resume matching via sentence-transformers embeddings."""

import logging
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from shared.constants import DEFAULT_SENTENCE_MODEL, MODELS_CACHE_DIR
from shared.models import Job, Resume

logger = logging.getLogger(__name__)


class JobMatcher:
    """Compute semantic similarity between a job description and a resume."""

    def __init__(self, model_name: str = DEFAULT_SENTENCE_MODEL) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            cache_dir = MODELS_CACHE_DIR / "sentence_transformers"
            logger.info("Loading sentence-transformer model '%s'...", self.model_name)
            self._model = SentenceTransformer(
                self.model_name, cache_folder=str(cache_dir)
            )
        return self._model

    def calculate_match(self, job: Job, resume: Resume) -> float:
        """Return a cosine similarity score in [0.0, 1.0].

        Encodes the job description and resume text into embeddings,
        then computes cosine similarity.
        """
        model = self._load_model()
        job_text = f"{job.title or ''}\n{job.company or ''}\n{job.description or ''}"
        resume_text = f"{resume.raw_text}\nSkills: {', '.join(resume.parsed_skills)}"

        embeddings = model.encode([job_text, resume_text], convert_to_numpy=True)
        similarity = self._cosine_similarity(embeddings[0], embeddings[1])
        score = float((similarity + 1) / 2)  # map [-1, 1] -> [0, 1]
        logger.info("Match score for job %s vs resume %s: %.3f", job.id, resume.id, score)
        return score

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
