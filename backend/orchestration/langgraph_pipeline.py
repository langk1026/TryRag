from langgraph.graph import StateGraph, START, END
from backend.core.config import config
from backend.core.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.retrieval.multi_query_generator import MultiQueryGenerator
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.reranking.cross_encoder_reranker import CrossEncoderReranker
from backend.generation.context_builder import ContextBuilder
from backend.generation.llm_service import LLMService
from backend.evaluation.ragas_evaluator import RagasEvaluator
from backend.monitoring.telemetry import get_tracer
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class LangGraphRAGPipeline:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.query_generator = MultiQueryGenerator()
        self.hybrid_retriever = HybridRetriever(self.embedding_service, self.vector_store)
        self.reranker = CrossEncoderReranker()
        self.context_builder = ContextBuilder()
        self.llm_service = LLMService()
        self.evaluator = RagasEvaluator()
        self.max_retries = config.max_retries
        self.hyde_enabled = config.hyde_enabled
        self.tracer = get_tracer("tryrag.langgraph")
        self.graph = self._build_graph()

    def _trace_span(self, name):
        if self.tracer:
            return self.tracer.start_as_current_span(name)

        class DummySpan:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        return DummySpan()

    def _build_graph(self):
        graph = StateGraph(dict)

        graph.add_node("query_node", self.query_node)
        graph.add_node("rewrite_node", self.rewrite_node)
        graph.add_node("retrieve_node", self.retrieve_node)
        graph.add_node("rerank_node", self.rerank_node)
        graph.add_node("generate_node", self.generate_node)
        graph.add_node("evaluate_node", self.evaluate_node)
        graph.add_node("retry_node", self.retry_node)

        graph.add_edge(START, "query_node")
        graph.add_edge("query_node", "rewrite_node")
        graph.add_edge("rewrite_node", "retrieve_node")
        graph.add_edge("retrieve_node", "rerank_node")
        graph.add_edge("rerank_node", "generate_node")
        graph.add_edge("generate_node", "evaluate_node")

        graph.add_conditional_edges(
            "evaluate_node",
            self.route_after_evaluation,
            {
                "retry": "retry_node",
                "end": END
            }
        )
        graph.add_edge("retry_node", "rewrite_node")

        return graph.compile()

    def query_node(self, state):
        with self._trace_span("query_node"):
            question = (state.get('question') or '').strip()
            return {
                **state,
                'question': question,
                'retry_count': state.get('retry_count', 0),
                'retrieved_docs': [],
                'reranked_docs': [],
                'evaluation': {}
            }

    def rewrite_node(self, state):
        with self._trace_span("rewrite_node"):
            question = state.get('question', '')
            queries = self.query_generator.generate(question)

            if self.hyde_enabled:
                try:
                    hyde_query = self.llm_service.generate_hypothetical_answer(question)
                    if hyde_query and hyde_query not in queries:
                        queries.append(hyde_query)
                except Exception as e:
                    logger.warning(f"HyDE query generation failed: {str(e)}")

            return {
                **state,
                'queries': queries
            }

    def retrieve_node(self, state):
        with self._trace_span("retrieve_node"):
            queries = state.get('queries') or [state.get('question', '')]
            top_k = int(state.get('top_k', 5))

            candidates = []
            seen_ids = set()

            for q in queries:
                docs = self.hybrid_retriever.search(q, top_k=max(top_k, config.hybrid_candidate_pool))
                for doc in docs:
                    doc_id = doc.get('id')
                    if doc_id and doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        candidates.append(doc)

            candidates.sort(
                key=lambda item: item.get('hybrid_score', 1.0 - float(item.get('distance', 1.0))),
                reverse=True
            )

            return {
                **state,
                'retrieved_docs': candidates[:max(top_k, config.hybrid_candidate_pool)]
            }

    def rerank_node(self, state):
        with self._trace_span("rerank_node"):
            question = state.get('question', '')
            docs = state.get('retrieved_docs', [])
            reranked = self.reranker.rerank(question, docs)

            return {
                **state,
                'reranked_docs': reranked
            }

    def generate_node(self, state):
        with self._trace_span("generate_node"):
            question = state.get('question', '')
            temperature = float(state.get('temperature', 0.7))
            docs = state.get('reranked_docs') or state.get('retrieved_docs') or []

            context = self.context_builder.build(docs)
            answer = self.llm_service.generate_answer(question, context, temperature)

            return {
                **state,
                'answer': answer,
                'context_used': context
            }

    def evaluate_node(self, state):
        with self._trace_span("evaluate_node"):
            question = state.get('question', '')
            answer = state.get('answer', '')
            docs = state.get('reranked_docs') or state.get('retrieved_docs') or []
            contexts = [doc.get('text', '') for doc in docs if doc.get('text')]

            evaluation = self.evaluator.evaluate(question, answer, contexts)
            return {
                **state,
                'evaluation': evaluation
            }

    def retry_node(self, state):
        with self._trace_span("retry_node"):
            retry_count = int(state.get('retry_count', 0)) + 1
            top_k = int(state.get('top_k', 5))
            updated_top_k = min(top_k + 3, max(top_k, config.hybrid_candidate_pool))

            logger.info(f"Retrying RAG query (attempt {retry_count}/{self.max_retries})")

            return {
                **state,
                'retry_count': retry_count,
                'top_k': updated_top_k
            }

    def route_after_evaluation(self, state):
        evaluation = state.get('evaluation', {})
        passed = evaluation.get('passed', False)
        retry_count = int(state.get('retry_count', 0))

        if passed:
            return 'end'
        if retry_count < self.max_retries:
            return 'retry'
        return 'end'

    def run(self, question, top_k=5, temperature=0.7):
        initial_state = {
            'question': question,
            'top_k': top_k,
            'temperature': temperature,
            'retry_count': 0
        }

        final_state = self.graph.invoke(initial_state)
        docs = final_state.get('reranked_docs') or final_state.get('retrieved_docs') or []

        return {
            'answer': final_state.get('answer', "I couldn't generate an answer."),
            'sources': self._extract_sources(docs),
            'context_used': final_state.get('context_used', ''),
            'num_sources': len(docs),
            'evaluation': final_state.get('evaluation', {}),
            'retry_count': final_state.get('retry_count', 0),
            'queries_used': final_state.get('queries', [])
        }

    def _extract_sources(self, retrieved_docs):
        sources = []

        for doc in retrieved_docs:
            metadata = doc.get('metadata', {})
            source = {
                'document_id': metadata.get('document_id', ''),
                'document_name': metadata.get('document_name', 'Unknown'),
                'document_path': metadata.get('document_path', ''),
                'page_number': metadata.get('page_number', 'N/A'),
                'url': metadata.get('url', ''),
                'relevance_score': doc.get('hybrid_score', 1.0 - float(doc.get('distance', 1.0))),
                'chunk_index': metadata.get('chunk_index', 0)
            }
            sources.append(source)

        return sources
