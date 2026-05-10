"""Sync resume repository using standard library sqlite3."""

import logging

from infrastructure.database.connection import Database
from shared.models import Resume

logger = logging.getLogger(__name__)


class ResumeRepository:
    """CRUD and query operations for the ``resumes`` table."""

    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database.get_instance()

    def create(
        self,
        filename: str,
        raw_text: str,
        parsed_skills: str,
        parsed_experience: str,
    ) -> int:
        """Insert a new resume record and return its ID."""
        conn = self.database.get_connection()
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO resumes (filename, raw_text, parsed_skills, parsed_experience)
                VALUES (?, ?, ?, ?)
                """,
                (filename, raw_text, parsed_skills, parsed_experience),
            )
            resume_id = cursor.lastrowid
            logger.info("Created resume %d", resume_id)
            return resume_id  # type: ignore[return-value]

    def get_by_id(self, resume_id: int) -> Resume | None:
        """Fetch a single resume by ID."""
        conn = self.database.get_connection()
        with conn:
            cursor = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
            row = cursor.fetchone()
            return Resume(**self._parse_row(row)) if row else None

    def list_all(self) -> list[Resume]:
        """List all uploaded resumes ordered by most recent."""
        conn = self.database.get_connection()
        with conn:
            cursor = conn.execute("SELECT * FROM resumes ORDER BY uploaded_at DESC")
            rows = cursor.fetchall()
            return [Resume(**self._parse_row(row)) for row in rows]

    def get_latest(self) -> Resume | None:
        """Return the most recently uploaded resume."""
        conn = self.database.get_connection()
        with conn:
            cursor = conn.execute(
                "SELECT * FROM resumes ORDER BY uploaded_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return Resume(**self._parse_row(row)) if row else None

    @staticmethod
    def _parse_row(row) -> dict:
        """Convert a sqlite3 Row into a dict, splitting CSV fields back into lists."""
        data = dict(row)
        data["parsed_skills"] = data["parsed_skills"].split(",") if data["parsed_skills"] else []
        data["parsed_experience"] = data["parsed_experience"].split(",") if data["parsed_experience"] else []
        return data

    @staticmethod
    def _row_factory(cursor, row) -> dict:
        """Convert a sqlite3 row to a dict keyed by column names."""
        return {
            desc[0]: row[idx] for idx, desc in enumerate(cursor.description)
        }
