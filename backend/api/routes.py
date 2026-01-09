from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.core.rag_engine import RAGEngine
from backend.services.indexing_service import IndexingService
from backend.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

rag_engine = RAGEngine()
indexing_service = IndexingService()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    temperature: float = 0.7


class QueryResponse(BaseModel):
    answer: str
    sources: list
    context_used: str
    num_sources: int


class IndexResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_created: int
    errors: list


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        logger.info(f"Received query: {request.question[:100]}...")

        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        result = rag_engine.query(
            request.question,
            top_k=request.top_k,
            temperature=request.temperature
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/full", response_model=IndexResponse)
async def trigger_full_reindex():
    try:
        logger.info("Full reindex triggered via API")

        result = indexing_service.full_reindex()

        return IndexResponse(**result)

    except Exception as e:
        logger.error(f"Full reindex endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/incremental", response_model=IndexResponse)
async def trigger_incremental_index():
    try:
        logger.info("Incremental index triggered via API")

        result = indexing_service.incremental_index()

        return IndexResponse(**result)

    except Exception as e:
        logger.error(f"Incremental index endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/stats")
async def get_index_statistics():
    try:
        stats = indexing_service.get_index_stats()
        return stats

    except Exception as e:
        logger.error(f"Index stats endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "RAG Application API"
    }
