import google.generativeai as genai
from backend.core.config import config
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class MultiQueryGenerator:
    def __init__(self):
        genai.configure(api_key=config.google_api_key)
        self.enabled = config.multi_query_enabled
        self.query_count = config.multi_query_count
        self.model = genai.GenerativeModel(config.llm_model)

    def generate(self, question):
        if not self.enabled or self.query_count <= 1:
            return [question]

        prompt = f"""You generate retrieval rewrites for a RAG system.

Return exactly {self.query_count} alternative search queries that preserve user intent and improve recall.
Each query must be on its own line and avoid numbering.

User question: {question}
"""

        try:
            response = self.model.generate_content(prompt)
            text = (response.text or "").strip()
            candidates = [line.strip(" -\t") for line in text.splitlines() if line.strip()]

            unique_queries = []
            seen = set()
            for candidate in [question] + candidates:
                normalized = candidate.lower().strip()
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    unique_queries.append(candidate.strip())
                if len(unique_queries) >= self.query_count:
                    break

            if question not in unique_queries:
                unique_queries.insert(0, question)

            logger.debug(f"Generated {len(unique_queries)} retrieval queries")
            return unique_queries
        except Exception as e:
            logger.warning(f"Multi-query generation failed, falling back to single query: {str(e)}")
            return [question]
