from backend.core.config import config
from backend.core.logger import setup_logger
from backend.retrieval.keyword_retriever import KeywordRetriever

logger = setup_logger(__name__)


class HybridRetriever:
    def __init__(self, embedding_service, vector_store):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.keyword_retriever = KeywordRetriever(vector_store)
        self.enabled = config.hybrid_search_enabled
        self.vector_weight = config.hybrid_vector_weight
        self.keyword_weight = config.hybrid_keyword_weight
        self.candidate_pool = config.hybrid_candidate_pool

    def _normalize_score_map(self, score_map):
        if not score_map:
            return {}
        scores = list(score_map.values())
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return {k: 1.0 for k in score_map}
        return {k: (v - min_score) / (max_score - min_score) for k, v in score_map.items()}

    def search(self, query, top_k=5):
        query_embedding = self.embedding_service.generate_single_embedding(query)
        vector_docs = self.vector_store.search(query_embedding, top_k=max(top_k, self.candidate_pool))

        if not self.enabled:
            return vector_docs[:top_k]

        keyword_docs = self.keyword_retriever.search(query, top_k=max(top_k, self.candidate_pool))

        vector_score_map = {}
        vector_doc_map = {}
        for doc in vector_docs:
            doc_id = doc.get('id')
            if not doc_id:
                continue
            vector_doc_map[doc_id] = doc
            vector_score_map[doc_id] = 1.0 - float(doc.get('distance', 1.0))

        keyword_score_map = {}
        keyword_doc_map = {}
        for doc in keyword_docs:
            doc_id = doc.get('id')
            if not doc_id:
                continue
            keyword_doc_map[doc_id] = doc
            keyword_score_map[doc_id] = float(doc.get('keyword_score', 0.0))

        vector_norm = self._normalize_score_map(vector_score_map)
        keyword_norm = self._normalize_score_map(keyword_score_map)

        merged_ids = set(vector_doc_map.keys()) | set(keyword_doc_map.keys())
        fused = []

        for doc_id in merged_ids:
            v = vector_norm.get(doc_id, 0.0)
            k = keyword_norm.get(doc_id, 0.0)
            score = (self.vector_weight * v) + (self.keyword_weight * k)

            merged_doc = vector_doc_map.get(doc_id) or keyword_doc_map.get(doc_id)
            merged_doc = dict(merged_doc)
            merged_doc['hybrid_score'] = score
            fused.append(merged_doc)

        fused.sort(key=lambda item: item.get('hybrid_score', 0.0), reverse=True)
        logger.debug(f"Hybrid retriever returned {len(fused[:top_k])} results")
        return fused[:top_k]
