from datetime import datetime, timezone
from backend.services.sharepoint_connector import SharePointConnector
from backend.services.document_processor import DocumentProcessor
from backend.services.vector_store import VectorStore
from backend.core.recursive_splitter import RecursiveCharacterSplitter
from backend.core.embeddings import EmbeddingService
from backend.core.logger import setup_logger
from backend.models.index_state import IndexState

logger = setup_logger(__name__)


class IndexingService:
    def __init__(self):
        self.sharepoint = SharePointConnector()
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.chunker = RecursiveCharacterSplitter()
        self.embedding_service = EmbeddingService()
        self.index_state = IndexState()

    def full_reindex(self):
        logger.info("Starting full reindex of all SharePoint documents")

        try:
            documents = self.sharepoint.get_all_documents()

            if not documents:
                logger.warning("No documents found in SharePoint")
                return {
                    'status': 'completed',
                    'documents_processed': 0,
                    'chunks_created': 0,
                    'errors': []
                }

            logger.info(f"Found {len(documents)} documents to index")

            self.vector_store.clear_collection()

            results = self._process_documents(documents)

            self.index_state.update_last_indexed_time(datetime.now(timezone.utc))

            logger.info(f"Full reindex completed: {results['documents_processed']} documents, "
                       f"{results['chunks_created']} chunks")

            return results

        except Exception as e:
            logger.error(f"Full reindex failed: {str(e)}")
            raise

    def incremental_index(self):
        logger.info("Starting incremental index of modified documents")

        try:
            last_indexed = self.index_state.get_last_indexed_time()

            if not last_indexed:
                logger.info("No previous index found, performing full reindex")
                return self.full_reindex()

            logger.info(f"Fetching documents modified since {last_indexed}")
            modified_docs = self.sharepoint.get_documents_modified_since(last_indexed)

            if not modified_docs:
                logger.info("No modified documents found")
                return {
                    'status': 'completed',
                    'documents_processed': 0,
                    'chunks_created': 0,
                    'errors': []
                }

            logger.info(f"Found {len(modified_docs)} modified documents")

            for doc in modified_docs:
                self.vector_store.delete_document(doc['id'])

            results = self._process_documents(modified_docs)

            self.index_state.update_last_indexed_time(datetime.now(timezone.utc))

            logger.info(f"Incremental index completed: {results['documents_processed']} documents, "
                       f"{results['chunks_created']} chunks")

            return results

        except Exception as e:
            logger.error(f"Incremental index failed: {str(e)}")
            raise

    def _process_documents(self, documents):
        processed_count = 0
        total_chunks = 0
        errors = []

        for doc in documents:
            try:
                logger.info(f"Processing document: {doc['name']}")

                content = self.sharepoint.download_file_content(doc['path'])

                pages_data = self.doc_processor.extract_text_with_pages(content, doc['name'])

                if not pages_data:
                    logger.warning(f"Skipping {doc['name']}: no text content extracted")
                    continue

                metadata = {
                    'document_id': doc['id'],
                    'document_name': doc['name'],
                    'document_path': doc['path'],
                    'modified': doc['modified'],
                    'author': doc['author'],
                    'url': f"{self.sharepoint.site_url}{doc['path']}"
                }

                chunks = self.chunker.chunk_text_with_pages(pages_data, metadata)

                if not chunks:
                    logger.warning(f"No chunks created for {doc['name']}")
                    continue

                chunk_texts = [chunk['text'] for chunk in chunks]
                embeddings = self.embedding_service.generate_embeddings(chunk_texts)

                self.vector_store.add_documents(chunks, embeddings)

                processed_count += 1
                total_chunks += len(chunks)

                logger.info(f"Successfully indexed {doc['name']} ({len(chunks)} chunks)")

            except Exception as e:
                error_msg = f"Failed to process {doc['name']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        return {
            'status': 'completed' if not errors else 'completed_with_errors',
            'documents_processed': processed_count,
            'chunks_created': total_chunks,
            'errors': errors
        }

    def get_index_stats(self):
        return {
            'total_chunks': self.vector_store.get_document_count(),
            'last_indexed': self.index_state.get_last_indexed_time(),
            'collection_name': self.vector_store.collection_name
        }
