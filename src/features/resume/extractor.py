"""PDF text extraction using pdfplumber."""

import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


class ResumeExtractor:
    """Extract raw text from a PDF resume."""

    def extract_text(self, pdf_path: Path) -> str:
        """Open a PDF and concatenate text from all pages."""
        text_parts: list[str] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception:
            logger.exception("Failed to extract text from %s", pdf_path)
            raise
        return "\n".join(text_parts)
