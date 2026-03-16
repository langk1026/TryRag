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

    def get_graph_mermaid(self):
        try:
            import re
            raw_mermaid = self.pipeline.graph.get_graph().draw_mermaid()

            # 1. Strip <p> tags
            clean = re.sub(r'<p>(.*?)</p>', r'\1', raw_mermaid)
            # 2. Remove &nbsp; entities
            clean = clean.replace('&nbsp;', ' ')
            # 3. Convert dotted-edge-with-label: "-. label .->" to "-.->|label|"
            clean = re.sub(
                r'-\.\s*(.+?)\s*\.\-\>',
                lambda m: f'-.->|{m.group(1).strip()}|',
                clean
            )
            # 4. Convert solid-edge-with-label: "-- label -->" to "-->|label|"
            clean = re.sub(
                r'--\s+(.+?)\s+--\>',
                lambda m: f'-->|{m.group(1).strip()}|',
                clean
            )
            return clean
        except Exception as e:
            logger.error(f"Failed to generate graph mermaid: {str(e)}")
            return ""
