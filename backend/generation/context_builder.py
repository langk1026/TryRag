from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class ContextBuilder:
    def build(self, retrieved_docs):
        context_parts = []

        for idx, doc in enumerate(retrieved_docs, 1):
            metadata = doc.get('metadata', {})
            doc_name = metadata.get('document_name', 'Unknown')
            page_number = metadata.get('page_number', 'N/A')
            doc_text = doc.get('text', '')

            context_parts.append(f"[Document {idx}: {doc_name}, Page {page_number}]")
            context_parts.append(doc_text)
            context_parts.append("")

        context = '\n'.join(context_parts)
        logger.debug(f"Built context with {len(context)} chars")
        return context
