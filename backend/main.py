from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.config import config
from backend.core.logger import setup_logger

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

app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {config.api_host}:{config.api_port}")

    uvicorn.run(
        "backend.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True,
        log_level=config.log_level.lower()
    )
