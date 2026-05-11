"""Batch extractor: split long job postings into sliding windows,
extract from each window, and merge the results."""

import logging

from shared.models import Job
from features.job_extraction.internal.llm_extractor import LlamaJobExtractor
from features.job_extraction.internal.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class BatchExtractor:
    """Wrapper around LlamaJobExtractor for long-text chunking."""

    def __init__(
        self,
        extractor: LlamaJobExtractor,
        prompt_builder: PromptBuilder,
        chunk_size: int = 1500,
        overlap: int = 300,
    ) -> None:
        self.extractor = extractor
        self.prompt_builder = prompt_builder
        self.chunk_size = chunk_size
        self.overlap = overlap

    def extract(self, raw_html: str) -> Job:
        """Extract structured fields from long raw HTML via batched chunks."""
        text = self.prompt_builder._strip_html_tags(raw_html)

        if len(text) <= self.chunk_size:
            # Short text — single pass
            return self._single_extract(text, raw_html)

        # Long text — split into overlapping chunks
        chunks = self._split_into_chunks(text)
        logger.info("Split text into %d chunk(s) for batched extraction", len(chunks))

        # Extract from each chunk and merge
        merged = self._extract_and_merge(chunks)

        # description_markdown carries the LLM-structured markdown.
        # description carries the full raw plain text for matching / indexing.
        return Job(
            url="",
            source="",
            title=merged.get("title"),
            company=merged.get("company"),
            location=merged.get("location"),
            description=text,  # full plain text for semantic matching
            description_markdown=merged.get("description"),
            raw_html=raw_html,
            scraped_at=None,  # type: ignore[arg-type]
        )

    # ── Internal helpers ─────────────────────────────────────────────

    def _single_extract(self, text: str, raw_html: str) -> Job:
        """Single-pass extraction for short text."""
        system_prompt = self.prompt_builder.SYSTEM_PROMPT
        user_prompt = self.prompt_builder.build_user_prompt(text)
        parsed = self.extractor.infer(system_prompt, user_prompt)

        return Job(
            url="",
            source="",
            title=parsed.get("title"),
            company=parsed.get("company"),
            location=parsed.get("location"),
            description=text,  # full plain text
            description_markdown=parsed.get("description"),
            raw_html=raw_html,
            scraped_at=None,  # type: ignore[arg-type]
        )

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into overlapping chunks for batched extraction."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = end - self.overlap
        return chunks

    def _extract_and_merge(self, chunks: list[str]) -> dict:
        """Run LLM on each chunk and merge non-null fields."""
        system_prompt = self.prompt_builder.SYSTEM_PROMPT
        max_desc_len = 0
        best_result: dict = {}

        for i, chunk in enumerate(chunks):
            user_prompt = self.prompt_builder.build_user_prompt(chunk)
            try:
                parsed = self.extractor.infer(system_prompt, user_prompt)
                logger.info("Chunk %d/%d result: %s", i + 1, len(chunks), parsed)
            except Exception:
                logger.exception("Chunk %d/%d extraction failed", i + 1, len(chunks))
                continue

            # Merge: prefer non-null fields
            for key in ("title", "company", "location"):
                if not best_result.get(key) and parsed.get(key):
                    best_result[key] = parsed.get(key)

            # For description, prefer the longest response (more content captured)
            chunk_desc = parsed.get("description")
            if chunk_desc and len(chunk_desc) > max_desc_len:
                best_result["description"] = chunk_desc
                max_desc_len = len(chunk_desc)

        return best_result
