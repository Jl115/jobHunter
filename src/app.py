"""Application controller with dependency injection and server lifecycle."""

import logging
from pathlib import Path

from PySide6.QtCore import QThread, QThreadPool
from uvicorn import Config, Server

from features.email import EmailComposer, MailtoGenerator
from features.job_extraction import BatchExtractor, LlamaJobExtractor, ModelManager, PromptBuilder
from features.jobs import JobMatcher, JobRepository, JobStore
from features.resume import ResumeExtractor, ResumeParser, ResumeRepository
from infrastructure.api import create_app
from infrastructure.database.connection import Database
from shared.app_state import AppState
from shared.constants import DEFAULT_PORT
from widgets import MainWindow
from workers import ExtractionWorker

logger = logging.getLogger(__name__)


class ServerThread(QThread):
    """Run Uvicorn in a background QThread so the GUI stays responsive."""

    def __init__(self, port: int = DEFAULT_PORT, parent=None) -> None:
        super().__init__(parent)
        self.port = port
        self._server: Server | None = None

    def run(self) -> None:
        app = create_app()
        config = Config(app=app, host="127.0.0.1", port=self.port, log_level="info")
        self._server = Server(config=config)
        logger.info("Starting Uvicorn on 127.0.0.1:%d", self.port)
        self._server.run()

    def stop(self) -> None:
        """Signal the uvicorn server to shut down gracefully."""
        if self._server is not None:
            self._server.should_exit = True
            logger.info("Uvicorn shutdown requested")


class ApplicationController:
    """Orchestrates the entire desktop application lifecycle.

    Wires features together via dependency injection, initializes the database,
    starts the FastAPI server in a background thread, and launches the GUI.
    """

    _instance: "ApplicationController | None" = None

    @classmethod
    def get_instance(cls) -> "ApplicationController":
        """Return the singleton instance (set during app startup)."""
        if cls._instance is None:
            raise RuntimeError("ApplicationController has not been initialised yet")
        return cls._instance

    def __init__(self) -> None:
        if ApplicationController._instance is not None:
            raise RuntimeError("ApplicationController is a singleton")
        ApplicationController._instance = self

        # Thread pool for background LLL / matching / email tasks
        self.thread_pool = QThreadPool.globalInstance()

        # Initialize database (runs migrations on first call)
        self._database = Database.get_instance()

        # Feature wiring via dependency injection
        self._model_manager = ModelManager()
        self._prompt_builder = PromptBuilder()
        self._llm_extractor = LlamaJobExtractor(
            self._model_manager, self._prompt_builder
        )
        self._batch_extractor = BatchExtractor(
            self._llm_extractor, self._prompt_builder
        )

        self._job_repository = JobRepository(self._database)
        self._job_matcher = JobMatcher()
        self._job_store = JobStore.get_instance()

        self._resume_extractor = ResumeExtractor()
        self._resume_parser = ResumeParser(
            model_manager=self._model_manager,
            prompt_builder=self._prompt_builder,
        )
        self._resume_repository = ResumeRepository(self._database)

        self._email_composer = EmailComposer()
        self._mailto_generator = MailtoGenerator()

        # UI
        self._main_window: MainWindow | None = None

        # Server
        self._server_thread = ServerThread()

        # Wire AppState signals
        AppState.get_instance().jobs_updated.connect(self._on_jobs_updated)
        AppState.get_instance().extraction_completed.connect(
            self._on_extraction_completed
        )

    def run(self) -> None:
        """Initialize persistent state, start server, and show the main window."""
        self._database.initialise()
        logger.info("Database ready")

        self._server_thread.start()
        logger.info("Server thread started")

        # Inject dependencies into the main window so widgets can fetch real data
        self._main_window = MainWindow(
            job_repository=self._job_repository,
            resume_repository=self._resume_repository,
            job_matcher=self._job_matcher,
            email_composer=self._email_composer,
            thread_pool=self.thread_pool,
        )
        self._main_window.set_server_status(running=True)
        self._main_window.show()

        # Load initial data
        self._on_jobs_updated()

    def shutdown(self) -> None:
        """Gracefully stop the server and clean up resources."""
        if self._main_window is not None:
            self._main_window.set_server_status(running=False)
        self._server_thread.stop()
        self._server_thread.quit()
        self._server_thread.wait(5000)
        logger.info("Application shutdown complete")

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_jobs_updated(self) -> None:
        """Refresh the job list in the UI when data changes."""
        if self._main_window is not None:
            self._main_window.refresh_job_list()

    def _on_extraction_completed(self, job_id: int) -> None:
        """React when an LLM extraction finishes."""
        logger.info("Extraction completed for job %d", job_id)

    # ------------------------------------------------------------------
    # Public API for background work
    # ------------------------------------------------------------------

    def submit_extraction(self, job_id: int, raw_html: str) -> None:
        """Enqueue an LLM extraction task on the thread pool."""
        worker = ExtractionWorker(
            job_id=job_id,
            raw_html=raw_html,
            extractor=self._batch_extractor,
            repository=self._job_repository,
        )
        self.thread_pool.start(worker)
        logger.info("Submitted extraction worker for job %d", job_id)

    def submit_matching(self, job_id: int) -> None:
        """Enqueue a semantic matching task on the thread pool."""
        from workers import MatchWorker

        worker = MatchWorker(
            job_id=job_id,
            matcher=self._job_matcher,
            job_repository=self._job_repository,
            resume_repository=self._resume_repository,
        )
        self.thread_pool.start(worker)
        logger.info("Submitted matching worker for job %d", job_id)
