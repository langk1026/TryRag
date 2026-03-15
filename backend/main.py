from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.config import config
from backend.core.logger import setup_logger
from backend.monitoring.telemetry import configure_telemetry

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RAG Application API starting up")
    logger.info(f"Vector DB path: {config.vector_db_path}")
    logger.info(f"Collection name: {config.collection_name}")

    yield
    logger.info("RAG Application API shutting down")


app = FastAPI(
    title="RAG Application API",
    description="Retrieval-Augmented Generation API for SharePoint Documents",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tracer = configure_telemetry()
if tracer:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OpenTelemetry instrumentation enabled")
    except Exception as e:
        logger.warning(f"FastAPI instrumentation failed: {str(e)}")

app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {config.api_host}:{config.api_port}")
    if config.api_reload:
        uvicorn.run(
            "backend.main:app",
            host=config.api_host,
            port=config.api_port,
            reload=True,
            log_level=config.log_level.lower()
        )
    else:
        uvicorn.run(
            app,
            host=config.api_host,
            port=config.api_port,
            reload=False,
            log_level=config.log_level.lower()
        )
