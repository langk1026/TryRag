import time
from langgraph.graph import StateGraph, START, END
from backend.core.config import config
from backend.core.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.services.response_cache import ResponseCache
from backend.retrieval.multi_query_generator import MultiQueryGenerator
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.reranking.cross_encoder_reranker import CrossEncoderReranker
from backend.generation.context_builder import ContextBuilder
from backend.generation.llm_service import LLMService
from backend.evaluation.ragas_evaluator import RagasEvaluator
from backend.monitoring.telemetry import get_tracer
from backend.core.logger import setup_logger

logger = setup_logger(__name__)

# Keywords that indicate a simple/conversational query (no retrieval needed)
SIMPLE_QUERY_PATTERNS = [
    'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
    'thanks', 'thank you', 'bye', 'goodbye', 'how are you', 'what are you',
    'who are you', 'help', 'what can you do',
]


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
        self.response_cache = ResponseCache()
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

        # START → query_node
        graph.add_edge(START, "query_node")

        # query_node → route (simple vs complex)
        graph.add_conditional_edges(
            "query_node",
            self.route_query,
            {
                "simple": "generate_node",
                "complex": "rewrite_node",
                "cached": END,
            }
        )

        graph.add_edge("rewrite_node", "retrieve_node")

        # retrieve_node → route (has docs vs empty)
        graph.add_conditional_edges(
            "retrieve_node",
            self.route_after_retrieval,
            {
                "has_docs": "rerank_node",
                "no_docs": "generate_node",
            }
        )

        graph.add_edge("rerank_node", "generate_node")
        graph.add_edge("generate_node", "evaluate_node")

        # evaluate_node → retry or end
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

    # ──────────────── NODES ────────────────

    def query_node(self, state):
        with self._trace_span("query_node"):
            question = (state.get('question') or '').strip()
            top_k = int(state.get('top_k', 5))
            temperature = float(state.get('temperature', 0.7))

            # Check cache
            cached = self.response_cache.get(question, top_k, temperature)
            if cached:
                return {
                    **state,
                    'question': question,
                    'cached_response': cached,
                    'retry_count': 0,
                }

            return {
                **state,
                'question': question,
                'retry_count': state.get('retry_count', 0),
                'retrieved_docs': [],
                'reranked_docs': [],
                'evaluation': {},
                'is_simple_query': False,
                'cached_response': None,
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
                try:
                    docs = self.hybrid_retriever.search(q, top_k=max(top_k, config.hybrid_candidate_pool))
                    for doc in docs:
                        doc_id = doc.get('id')
                        if doc_id and doc_id not in seen_ids:
                            seen_ids.add(doc_id)
                            candidates.append(doc)
                except Exception as e:
                    logger.warning(f"Retrieval failed for query variant: {str(e)}")

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
            is_simple = state.get('is_simple_query', False)
            docs = state.get('reranked_docs') or state.get('retrieved_docs') or []

            if is_simple:
                # Simple query: generate without context
                answer = self.llm_service.generate_answer(
                    question,
                    "No document context is needed. Respond conversationally.",
                    temperature
                )
                return {
                    **state,
                    'answer': answer,
                    'context_used': '',
                }

            if not docs:
                # Fallback: no docs retrieved
                answer = self.llm_service.generate_answer(
                    question,
                    "No relevant documents were found in the knowledge base. "
                    "Answer based on general knowledge and clearly state that no "
                    "specific documents were found.",
                    temperature
                )
                return {
                    **state,
                    'answer': answer,
                    'context_used': '[fallback: no documents retrieved]',
                }

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
            is_simple = state.get('is_simple_query', False)
            docs = state.get('reranked_docs') or state.get('retrieved_docs') or []
            contexts = [doc.get('text', '') for doc in docs if doc.get('text')]

            # Skip evaluation for simple queries or fallback answers
            if is_simple or not contexts:
                return {
                    **state,
                    'evaluation': {
                        'faithfulness': 1.0,
                        'relevance': 1.0,
                        'completeness': 1.0,
                        'passed': True,
                        'threshold': self.evaluator.faithfulness_threshold,
                        'mode': 'skipped',
                    }
                }

            evaluation = self.evaluator.evaluate(question, answer, contexts)

            # Cache successful results
            if evaluation.get('passed', False):
                top_k = int(state.get('top_k', 5))
                temperature = float(state.get('temperature', 0.7))
                result = {
                    'answer': answer,
                    'sources': self._extract_sources(docs),
                    'context_used': state.get('context_used', ''),
                    'num_sources': len(docs),
                    'evaluation': evaluation,
                    'retry_count': state.get('retry_count', 0),
                    'queries_used': state.get('queries', [])
                }
                self.response_cache.put(question, top_k, temperature, result)

            return {
                **state,
                'evaluation': evaluation
            }

    def retry_node(self, state):
        with self._trace_span("retry_node"):
            retry_count = int(state.get('retry_count', 0)) + 1
            top_k = int(state.get('top_k', 5))
            updated_top_k = min(top_k + 3, max(top_k, config.hybrid_candidate_pool))

            # Exponential backoff: 0.5s, 1s, 2s, ...
            backoff = 0.5 * (2 ** (retry_count - 1))
            logger.info(f"Retrying RAG query (attempt {retry_count}/{self.max_retries}), "
                        f"backoff {backoff:.1f}s, new top_k={updated_top_k}")
            time.sleep(backoff)

            return {
                **state,
                'retry_count': retry_count,
                'top_k': updated_top_k
            }

    # ──────────────── ROUTING ────────────────

    def route_query(self, state):
        # If cache hit, short-circuit
        if state.get('cached_response'):
            return 'cached'

        question = state.get('question', '').lower().strip()

        # Detect simple/conversational queries
        for pattern in SIMPLE_QUERY_PATTERNS:
            if question == pattern or question.startswith(pattern + ' ') or question.endswith('?') and len(question.split()) <= 4 and pattern in question:
                logger.info(f"Routing as SIMPLE query: {question[:60]}")
                return 'simple'

        # Short queries with no document-specific intent
        if len(question.split()) <= 3 and not any(kw in question for kw in ['what', 'how', 'why', 'explain', 'describe', 'compare', 'list', 'find']):
            logger.info(f"Routing as SIMPLE query (short): {question[:60]}")
            return 'simple'

        logger.info(f"Routing as COMPLEX query: {question[:60]}")
        return 'complex'

    def route_after_retrieval(self, state):
        docs = state.get('retrieved_docs', [])
        if docs:
            return 'has_docs'
        logger.warning("No documents retrieved - falling back to LLM-only generation")
        return 'no_docs'

    def route_after_evaluation(self, state):
        evaluation = state.get('evaluation', {})
        passed = evaluation.get('passed', False)
        retry_count = int(state.get('retry_count', 0))

        if passed:
            return 'end'
        if retry_count < self.max_retries:
            return 'retry'
        logger.warning(f"Max retries ({self.max_retries}) exhausted - returning best effort answer")
        return 'end'

    # ──────────────── RUN ────────────────

    def run(self, question, top_k=5, temperature=0.7):
        initial_state = {
            'question': question,
            'top_k': top_k,
            'temperature': temperature,
            'retry_count': 0
        }

        final_state = self.graph.invoke(initial_state)

        # If cached, return cached response directly
        cached = final_state.get('cached_response')
        if cached:
            cached_copy = dict(cached)
            cached_copy['from_cache'] = True
            return cached_copy

        docs = final_state.get('reranked_docs') or final_state.get('retrieved_docs') or []

        return {
            'answer': final_state.get('answer', "I couldn't generate an answer."),
            'sources': self._extract_sources(docs),
            'context_used': final_state.get('context_used', ''),
            'num_sources': len(docs),
            'evaluation': final_state.get('evaluation', {}),
            'retry_count': final_state.get('retry_count', 0),
            'queries_used': final_state.get('queries', []),
            'from_cache': False,
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
