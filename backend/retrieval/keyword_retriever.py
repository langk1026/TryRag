import re
from rank_bm25 import BM25Okapi
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class KeywordRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def _tokenize(self, text):
        return re.findall(r"[a-zA-Z0-9]+", (text or "").lower())

    def search(self, query, top_k=10):
        chunks = self.vector_store.get_all_chunks()
        if not chunks:
            return []

        corpus_tokens = [self._tokenize(item.get('text', '')) for item in chunks]
        if not any(corpus_tokens):
            return []

        bm25 = BM25Okapi(corpus_tokens)
        query_tokens = self._tokenize(query)
        scores = bm25.get_scores(query_tokens)

        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in indexed_scores[:top_k]:
            chunk = chunks[idx]
            results.append({
                'id': chunk.get('id', ''),
                'text': chunk.get('text', ''),
                'metadata': chunk.get('metadata', {}),
                'keyword_score': float(score)
            })

        logger.debug(f"Keyword retriever returned {len(results)} results")
        return results
