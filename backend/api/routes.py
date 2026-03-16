from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import shutil
from pathlib import Path
from backend.core.config import config
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
    evaluation: dict = {}
    retry_count: int = 0
    queries_used: list = []


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


@router.post("/index/upload", response_model=IndexResponse)
async def upload_document(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file upload: {file.filename}")
        
        # Save file to local path
        upload_dir = Path(config.local_documents_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"File saved to {file_path}, triggering incremental index")
        
        result = indexing_service.incremental_index()
        return IndexResponse(**result)

    except Exception as e:
        logger.error(f"Upload endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/stats")
async def get_index_statistics():
    import traceback
    try:
        stats = indexing_service.get_index_stats()
        return stats

    except Exception as e:
        logger.error(f"Index stats endpoint error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/documents")
async def get_indexed_documents():
    try:
        docs = indexing_service.get_indexed_documents()
        return docs
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/index/documents/{document_id}")
async def delete_indexed_document(document_id: str):
    try:
        indexing_service.delete_document(document_id)
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "RAG Application API"
    }

@router.get("/orchestration/graph")
async def get_langgraph_flow():
    try:
        mermaid_data = rag_engine.get_graph_mermaid()
        return {"mermaid": mermaid_data}
    except Exception as e:
        logger.error(f"Graph endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
