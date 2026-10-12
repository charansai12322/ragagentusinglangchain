"""FastAPI Application Entry Point."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.errors import AppException
from backend.app.core.logging import get_logger, setup_logging
from backend.app.models.responses import ErrorResponse
from backend.app.services.rag_service import RAGService

# Initialize logging
setup_logging()
logger = get_logger(__name__)


class ApplicationState:
    """Container holding application-scoped services."""

    def __init__(self):
        self.rag_service = RAGService()


app_state = ApplicationState()


async def session_janitor_loop(rag_service: RAGService, interval_seconds: float = 60.0) -> None:
    """Background task to periodically purge expired document sessions."""
    logger.info("Started background session janitor (interval: %ds)", interval_seconds)
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            pruned = await rag_service.session_service.purge_expired()
            if pruned:
                for sid in pruned:
                    rag_service.vector_service.delete_session_index(sid)
                logger.info("Janitor evicted %d expired sessions", len(pruned))
        except asyncio.CancelledError:
            logger.info("Session janitor task stopped.")
            break
        except Exception as e:
            logger.warning("Error in session janitor loop: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup initialization and shutdown cleanup."""
    logger.info("Starting PDF Intelligence RAG Application (env: %s)", settings.APP_ENV)

    # Pre-warm embedding model
    try:
        dim = app_state.rag_service.embedding_service.dimension
        logger.info("Embedding service ready (dimension: %d)", dim)
    except Exception as e:
        logger.warning("Embedding service warm-up warning: %s", e)

    # Launch background janitor
    janitor_task = asyncio.create_task(session_janitor_loop(app_state.rag_service))

    yield

    # Clean up background tasks on shutdown
    janitor_task.cancel()
    try:
        await janitor_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutdown complete.")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="PDF Intelligence — RAG Document Chat API",
        description="Session-isolated, grounded question-answering for PDF documents.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

    # Global Exception Handlers
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.code,
                detail=exc.message,
                code=exc.code,
                request_id=req_id,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        errors = exc.errors()
        error_detail = "; ".join(f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                detail=error_detail,
                code="VALIDATION_ERROR",
                request_id=req_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled server exception [req_id=%s]: %s", req_id, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                detail="An unexpected internal server error occurred.",
                code="INTERNAL_SERVER_ERROR",
                request_id=req_id,
            ).model_dump(),
        )

    # Include root API router
    app.include_router(api_router)

    return app


app = create_app()
