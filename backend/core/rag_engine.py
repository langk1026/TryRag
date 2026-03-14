from backend.orchestration.langgraph_pipeline import LangGraphRAGPipeline
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class RAGEngine:
    def __init__(self):
        self.pipeline = LangGraphRAGPipeline()

    def query(self, user_question, top_k=5, temperature=0.7):
        logger.info(f"Processing RAG query with LangGraph: {user_question[:100]}...")

        try:
            result = self.pipeline.run(user_question, top_k=top_k, temperature=temperature)
            logger.info("RAG query completed successfully")
            return result
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise
