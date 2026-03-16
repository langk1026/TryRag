from datetime import datetime, timezone
from backend.services.sharepoint_connector import SharePointConnector
from backend.services.local_document_connector import LocalDocumentConnector
from backend.services.document_processor import DocumentProcessor
from backend.services.vector_store import VectorStore
from backend.core.recursive_splitter import RecursiveCharacterSplitter
from backend.core.embeddings import EmbeddingService
from backend.core.logger import setup_logger
from backend.core.config import config
from backend.models.index_state import IndexState

logger = setup_logger(__name__)


class IndexingService:
    def __init__(self):
        if config.environment == 'production':
            self.document_source = SharePointConnector()
            logger.info("Indexing source set to SharePoint (production environment)")
        else:
            self.document_source = LocalDocumentConnector()
            logger.info("Indexing source set to local temp folder (development environment)")

        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.chunker = RecursiveCharacterSplitter()
        self.embedding_service = EmbeddingService()
        self.index_state = IndexState()

    def full_reindex(self):
        logger.info("Starting full reindex of all source documents")

        try:
            documents = self.document_source.get_all_documents()

            if not documents:
                logger.warning("No documents found in configured source")
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

            deleted_count = self._cleanup_deleted_documents()

            logger.info(f"Fetching documents modified since {last_indexed}")
            modified_docs = self.document_source.get_documents_modified_since(last_indexed)

            if not modified_docs:
                logger.info("No modified documents found")
                return {
                    'status': 'completed',
                    'documents_processed': 0,
                    'chunks_created': 0,
                    'documents_deleted': deleted_count,
                    'errors': []
                }

            logger.info(f"Found {len(modified_docs)} modified documents")

            for doc in modified_docs:
                self.vector_store.delete_document(doc['id'])

            results = self._process_documents(modified_docs)
            results['documents_deleted'] = deleted_count

            self.index_state.update_last_indexed_time(datetime.now(timezone.utc))

            logger.info(f"Incremental index completed: {results['documents_processed']} documents, "
                       f"{results['chunks_created']} chunks, {deleted_count} deleted")

            return results

        except Exception as e:
            logger.error(f"Incremental index failed: {str(e)}")
            raise

    def _cleanup_deleted_documents(self):
        try:
            logger.info("Checking for deleted documents in configured source")

            current_docs = self.document_source.get_all_documents()
            current_doc_ids = {doc['id'] for doc in current_docs}

            indexed_doc_ids = set(self.vector_store.get_all_document_ids())

            deleted_doc_ids = indexed_doc_ids - current_doc_ids

            if not deleted_doc_ids:
                logger.info("No deleted documents found")
                return 0

            logger.info(f"Found {len(deleted_doc_ids)} deleted documents")

            for doc_id in deleted_doc_ids:
                try:
                    self.vector_store.delete_document(doc_id)
                    logger.info(f"Removed deleted document from index: {doc_id}")
                except Exception as e:
                    logger.error(f"Failed to remove document {doc_id}: {str(e)}")

            logger.info(f"Cleanup completed: {len(deleted_doc_ids)} documents removed from index")
            return len(deleted_doc_ids)

        except Exception as e:
            logger.error(f"Cleanup deleted documents failed: {str(e)}")
            return 0

    def _process_documents(self, documents):
        processed_count = 0
        total_chunks = 0
        errors = []

        for doc in documents:
            try:
                logger.info(f"Processing document: {doc['name']}")

                content = self.document_source.download_file_content(doc['path'])

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
                    'url': doc.get('web_url', '')
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
        last_indexed = self.index_state.get_last_indexed_time()
        return {
            'total_chunks': self.vector_store.get_document_count(),
            'last_indexed': last_indexed.isoformat() if last_indexed else None,
            'collection_name': self.vector_store.collection_name
        }

    def get_indexed_documents(self):
        try:
            chunks = self.vector_store.get_all_chunks()
            documents = {}
            for chunk in chunks:
                metadata = chunk.get('metadata', {})
                doc_id = metadata.get('document_id')
                if doc_id and doc_id not in documents:
                    documents[doc_id] = {
                        'id': doc_id,
                        'name': metadata.get('document_name', 'Unknown'),
                        'path': metadata.get('document_path', ''),
                        'chunks_count': 0
                    }
                if doc_id:
                    documents[doc_id]['chunks_count'] += 1
            return list(documents.values())
        except Exception as e:
            logger.error(f"Failed to get indexed documents: {str(e)}")
            raise

    def delete_document(self, document_id: str):
        try:
            self.vector_store.delete_document(document_id)
            logger.info(f"Deleted document {document_id} via API")
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}")
            raise
