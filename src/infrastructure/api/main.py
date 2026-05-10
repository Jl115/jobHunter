"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.constants import CORS_ORIGINS
from .routers import jobs, resumes


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Job Hunter API",
        description="Local REST API for the Job Hunter Desktop App",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
    app.include_router(resumes.router, prefix="/api/v1", tags=["resumes"])

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Simple health endpoint for the Chrome Extension to probe."""
        return {"status": "ok"}

    return app
