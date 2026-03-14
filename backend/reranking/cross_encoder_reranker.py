from backend.core.config import config
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class CrossEncoderReranker:
    def __init__(self):
        self.enabled = config.reranker_enabled
        self.top_n = config.reranker_top_n
        self.model_name = config.reranker_model
        self._model = None

        if self.enabled:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
                logger.info(f"Loaded reranker model: {self.model_name}")
            except Exception as e:
                self.enabled = False
                logger.warning(f"Reranker initialization failed, using fallback ranking: {str(e)}")

    def rerank(self, query, docs):
        if not docs:
            return []

        if not self.enabled or not self._model:
            ranked = sorted(
                docs,
                key=lambda item: item.get('hybrid_score', 1.0 - float(item.get('distance', 1.0))),
                reverse=True
            )
            return ranked[:self.top_n]

        pairs = [(query, item.get('text', '')) for item in docs]

        try:
            scores = self._model.predict(pairs)
            ranked = []
            for idx, doc in enumerate(docs):
                enriched = dict(doc)
                enriched['rerank_score'] = float(scores[idx])
                ranked.append(enriched)

            ranked.sort(key=lambda item: item.get('rerank_score', 0.0), reverse=True)
            return ranked[:self.top_n]
        except Exception as e:
            logger.warning(f"Reranking failed, using fallback ranking: {str(e)}")
            ranked = sorted(
                docs,
                key=lambda item: item.get('hybrid_score', 1.0 - float(item.get('distance', 1.0))),
                reverse=True
            )
            return ranked[:self.top_n]
