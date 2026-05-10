"""Sync job repository using standard library sqlite3."""

import logging
import sqlite3
from datetime import datetime

from infrastructure.database.connection import Database
from shared.models import Job, JobCapturePayload, JobStatus

logger = logging.getLogger(__name__)


class JobRepository:
    """CRUD and query operations for the ``jobs`` table."""

    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database.get_instance()

    def create(self, job: Job) -> int:
        """Insert a new job record and return its ID.

        If a job with the same URL already exists, updates the existing record
        and returns its original ID.
        """
        conn = self.database.get_connection()
        with conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO jobs (url, source, title, company, location,
                                      description, raw_html, scraped_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.url,
                        job.source,
                        job.title,
                        job.company,
                        job.location,
                        job.description,
                        job.raw_html,
                        job.scraped_at.isoformat() if job.scraped_at else None,
                        job.status.value,
                    ),
                )
                logger.info("Created new job %d", cursor.lastrowid)
                return cursor.lastrowid  # type: ignore[return-value]
            except sqlite3.IntegrityError:
                # UNIQUE constraint hit — fetch existing ID by URL and refresh data
                cursor = conn.execute("SELECT id FROM jobs WHERE url = ?", (job.url,))
                row = cursor.fetchone()
                if row:
                    existing_id = row[0]
                    conn.execute(
                        """
                        UPDATE jobs
                        SET source = ?, raw_html = ?, scraped_at = ?
                        WHERE id = ?
                        """,
                        (
                            job.source,
                            job.raw_html,
                            job.scraped_at.isoformat() if job.scraped_at else None,
                            existing_id,
                        ),
                    )
                    conn.commit()
                    logger.info("Refreshed existing job %d (re-scrape of %s)", existing_id, job.url)
                    return existing_id
                raise

    def get_by_id(self, job_id: int) -> Job | None:
        """Fetch a single job by ID."""
        conn = self.database.get_connection()
        conn.row_factory = self._row_factory
        with conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return Job(**row) if row else None

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Job]:
        """List jobs ordered by most recently scraped."""
        conn = self.database.get_connection()
        conn.row_factory = self._row_factory
        with conn:
            cursor = conn.execute(
                "SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = cursor.fetchall()
            return [Job(**row) for row in rows]

    def update_extraction(
        self,
        job_id: int,
        title: str | None,
        company: str | None,
        location: str | None,
        description: str | None,
    ) -> None:
        """Update structured fields after LLM extraction, preserving existing data."""
        conn = self.database.get_connection()
        with conn:
            # Fetch current values so we don't overwrite with nulls
            cursor = conn.execute(
                "SELECT title, company, location, description FROM jobs WHERE id = ?",
                (job_id,),
            )
            row = cursor.fetchone()
            if not row:
                return

            # Merge: keep existing non-null values if new value is None
            new_title = title if title else row[0]
            new_company = company if company else row[1]
            new_location = location if location else row[2]
            new_description = description if description else row[3]

            conn.execute(
                """
                UPDATE jobs
                SET title = ?, company = ?, location = ?,
                    description = ?, extracted_at = ?
                WHERE id = ?
                """,
                (
                    new_title,
                    new_company,
                    new_location,
                    new_description,
                    datetime.utcnow().isoformat(),
                    job_id,
                ),
            )
            conn.commit()
            logger.info("Updated extraction for job %d", job_id)

    def update_match_score(self, job_id: int, score: float) -> None:
        """Update the semantic match score for a job."""
        conn = self.database.get_connection()
        with conn:
            conn.execute(
                "UPDATE jobs SET match_score = ? WHERE id = ?",
                (score, job_id),
            )
            conn.commit()

    def update_status(self, job_id: int, status: JobStatus) -> None:
        """Update the lifecycle status of a job."""
        conn = self.database.get_connection()
        with conn:
            conn.execute(
                "UPDATE jobs SET status = ? WHERE id = ?",
                (status.value, job_id),
            )
            conn.commit()

    @staticmethod
    def _row_factory(cursor, row) -> dict:
        """Convert a sqlite3 row to a dict keyed by column names."""
        return {
            desc[0]: row[idx] for idx, desc in enumerate(cursor.description)
        }
