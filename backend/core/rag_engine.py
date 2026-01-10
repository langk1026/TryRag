import google.generativeai as genai
from backend.core.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore
from backend.core.logger import setup_logger
from backend.core.config import config

logger = setup_logger(__name__)


class RAGEngine:
    def __init__(self):
        genai.configure(api_key=config.google_api_key)
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.llm_model = config.llm_model
        self.hyde_enabled = config.hyde_enabled
        self.model = genai.GenerativeModel(self.llm_model)

    def query(self, user_question, top_k=5, temperature=0.7):
        logger.info(f"Processing RAG query: {user_question[:100]}...")

        try:
            if self.hyde_enabled:
                logger.debug("HyDE Mode: Step 1 - Generating hypothetical answer")
                hypothetical_answer = self._generate_hypothetical_answer(user_question)

                logger.info(f"Hypothetical Answer (HyDE): {hypothetical_answer[:200]}...")

                logger.debug("HyDE Mode: Step 2 - Embedding hypothetical answer")
                query_embedding = self.embedding_service.generate_single_embedding(hypothetical_answer)
            else:
                logger.debug("Standard Mode: Step 1 - Generating query embedding")
                query_embedding = self.embedding_service.generate_single_embedding(user_question)

            logger.debug(f"Step 2: Retrieving top {top_k} similar documents")
            retrieved_docs = self.vector_store.search(query_embedding, top_k=top_k)

            if not retrieved_docs:
                logger.warning("No relevant documents found")
                return {
                    'answer': "I couldn't find any relevant documents to answer your question.",
                    'sources': [],
                    'context_used': ""
                }

            logger.debug(f"Step 3: Constructing context from {len(retrieved_docs)} documents")
            context = self._build_context(retrieved_docs)

            logger.debug("Step 4: Generating LLM response")
            answer = self._generate_llm_response(user_question, context, temperature)

            sources = self._extract_sources(retrieved_docs)

            logger.info("RAG query completed successfully")

            return {
                'answer': answer,
                'sources': sources,
                'context_used': context,
                'num_sources': len(retrieved_docs)
            }

        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise

    def _generate_hypothetical_answer(self, question):
        hyde_prompt = f"""You are an expert at generating hypothetical answers for document retrieval.

Given the following question, generate a detailed, hypothetical answer as if you had access to the relevant documents. This answer will be used to find similar content in a document database.

Question: {question}

Generate a comprehensive hypothetical answer (2-3 paragraphs):"""

        try:
            generation_config = genai.types.GenerationConfig(
                temperature=config.hyde_temperature,
                max_output_tokens=config.hyde_max_tokens
            )

            response = self.model.generate_content(
                hyde_prompt,
                generation_config=generation_config
            )

            hypothetical_answer = response.text

            logger.debug(f"Generated hypothetical answer ({len(hypothetical_answer)} characters)")
            return hypothetical_answer

        except Exception as e:
            logger.error(f"HyDE answer generation failed: {str(e)}")
            logger.warning("Falling back to direct query embedding")
            return question

    def _build_context(self, retrieved_docs):
        context_parts = []

        for idx, doc in enumerate(retrieved_docs, 1):
            doc_name = doc['metadata'].get('document_name', 'Unknown')
            page_number = doc['metadata'].get('page_number', 'N/A')
            doc_text = doc['text']

            context_parts.append(f"[Document {idx}: {doc_name}, Page {page_number}]")
            context_parts.append(doc_text)
            context_parts.append("")

        context = '\n'.join(context_parts)

        logger.debug(f"Built context with {len(context)} characters from {len(retrieved_docs)} sources")
        return context

    def _generate_llm_response(self, question, context, temperature):
        prompt = f"""You are a helpful assistant that answers questions based on the provided context from SharePoint documents.

Instructions:
- Answer the question using ONLY the information from the provided context
- If the context doesn't contain enough information, say so clearly
- Cite the document names when referencing specific information
- Be concise but thorough
- If you're unsure, acknowledge the uncertainty

Context from documents:
{context}

Question: {question}

Please provide a clear and accurate answer based on the context above."""

        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=1000
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            answer = response.text

            logger.debug(f"Generated LLM response ({len(answer)} characters)")
            return answer

        except Exception as e:
            logger.error(f"LLM response generation failed: {str(e)}")
            raise

    def _extract_sources(self, retrieved_docs):
        sources = []

        for doc in retrieved_docs:
            metadata = doc['metadata']

            source = {
                'document_id': metadata.get('document_id', ''),
                'document_name': metadata.get('document_name', 'Unknown'),
                'document_path': metadata.get('document_path', ''),
                'page_number': metadata.get('page_number', 'N/A'),
                'url': metadata.get('url', ''),
                'relevance_score': 1 - doc.get('distance', 0),
                'chunk_index': metadata.get('chunk_index', 0)
            }
            sources.append(source)

        return sources
