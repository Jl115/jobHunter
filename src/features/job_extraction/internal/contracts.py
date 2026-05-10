"""Abstract contract for job field extractors."""

from abc import ABC, abstractmethod

from shared.models import Job


class IJobExtractor(ABC):
    """Protocol for extracting structured job fields from raw HTML."""

    @abstractmethod
    def extract(self, raw_html: str) -> Job:
        """Extract structured fields from raw article HTML.

        Args:
            raw_html: Clean article HTML from Readability.js.

        Returns:
            A Job model with ``title``, ``company``, ``location``,
            and ``description`` populated.
        """
        ...
