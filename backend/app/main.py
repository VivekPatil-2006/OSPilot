from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.api.v1.router import api_v1_router
from app.db import Base, engine, models  # noqa: F401

def ensure_db_schema_migrations():
    """Auto-migrates SQLite database schema for missing columns in existing tables."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if inspector.has_table("file_documents"):
            columns = [c["name"] for c in inspector.get_columns("file_documents")]
            if "last_modified_time" not in columns:
                logger.info("Migrating SQLite table 'file_documents': Adding missing 'last_modified_time' column...")
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE file_documents ADD COLUMN last_modified_time FLOAT"))
                    conn.commit()
    except Exception as e:
        logger.warning(f"SQLite auto-migration notice: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager creating database schema and initializing app resources."""
    Base.metadata.create_all(bind=engine)
    ensure_db_schema_migrations()
    logger.info(f"{settings.PROJECT_NAME} initialized successfully.")
    yield

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException

def create_app() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Offline Production-Quality AI Desktop Assistant Backend Core",
        version="1.0.0",
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    # Enable CORS for Electron / Frontend IPC client connections
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Global Exception Handlers ---
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP {exc.status_code} Error on {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "status": exc.status_code, "message": str(exc.detail)}
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        logger.error(f"FileNotFound Error on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": True, "status": 404, "message": f"Resource not found: {str(exc)}"}
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.error(f"Validation ValueError on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": True, "status": 400, "message": str(exc)}
        )

    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Global Server Error on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": True, "status": 500, "message": f"Internal Server Error: {str(exc)}"}
        )

    app.include_router(api_v1_router)

    @app.get("/")
    def root():
        """Root endpoint redirecting to documentation and health status."""
        return {
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
            "status": "online",
            "documentation": "http://127.0.0.1:8000/docs",
            "health_check": "http://127.0.0.1:8000/api/v1/health",
            "metrics": "http://127.0.0.1:8000/api/v1/health/metrics"
        }

    return app


app = create_app()

