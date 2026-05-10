"""Thread-safe sync SQLite singleton with automatic migrations.

Uses the standard library ``sqlite3`` module. FastAPI endpoints that need
async compatibility should wrap calls with ``asyncio.to_thread()``.
"""

import logging
import sqlite3
from pathlib import Path
from typing import ClassVar

from shared.constants import DATABASE_PATH

logger = logging.getLogger(__name__)


class Database:
    """Singleton SQLite connection manager backed by the standard library.

    Creates ``.local/share/job_hunter/`` if needed and runs migrations on
    first initialisation. The returned connection has
    ``check_same_thread=False`` so it can be used from the FastAPI thread-pool.
    """

    _instance: ClassVar["Database | None"] = None
    _initialised: bool = False

    def __new__(cls) -> "Database":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "Database":
        """Return the singleton instance."""
        return cls()

    def initialise(self) -> None:
        """Ensure the database file exists and migrations have run."""
        if self._initialised:
            return

        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DATABASE_PATH) as conn:
            self._run_migrations(conn)
        self._initialised = True
        logger.info("Database initialised at %s", DATABASE_PATH)

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        """Execute SQL migration files in lexicographic order."""
        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            logger.warning("No migrations directory found at %s", migrations_dir)
            return

        for migration_file in sorted(migrations_dir.glob("*.sql")):
            sql = migration_file.read_text(encoding="utf-8")
            conn.executescript(sql)
            logger.info("Applied migration: %s", migration_file.name)
        conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Return a new ``sqlite3`` connection.

        ``check_same_thread=False`` allows the connection to be used across
        the main GUI thread and FastAPI thread-pool workers.
        """
        if not self._initialised:
            self.initialise()
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
