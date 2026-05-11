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
        """Execute SQL migration files in lexicographic order, skipping already-applied ones.

        Tracks applied migrations in ``schema_migrations`` so the app never crashes
        on restart when a column/index already exists.
        """
        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            logger.warning("No migrations directory found at %s", migrations_dir)
            return

        # Ensure tracking table exists (back-compat for DBs created before this logic)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "  filename TEXT PRIMARY KEY,"
            "  applied_at TEXT DEFAULT (datetime('now'))"
            ")"
        )
        conn.commit()

        # Determine which migrations have already run
        applied = {
            row[0]
            for row in conn.execute("SELECT filename FROM schema_migrations").fetchall()
        }

        for migration_file in sorted(migrations_dir.glob("*.sql")):
            name = migration_file.name
            if name in applied:
                logger.debug("Skipping already-applied migration: %s", name)
                continue

            sql = migration_file.read_text(encoding="utf-8")
            try:
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (?)",
                    (name,),
                )
                conn.commit()
                logger.info("Applied migration: %s", name)
            except sqlite3.OperationalError as exc:
                # If the migration fails because the change is already present
                # (e.g. column already exists), log and mark it applied so the
                # app doesn't crash on restart.
                err = str(exc).lower()
                if "duplicate column name" in err or "already exists" in err:
                    logger.warning("Migration %s partially applied: %s", name, exc)
                    conn.execute(
                        "INSERT INTO schema_migrations (filename) VALUES (?)",
                        (name,),
                    )
                    conn.commit()
                else:
                    raise

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
