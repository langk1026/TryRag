import chromadb
from chromadb.config import Settings
from datetime import datetime
from backend.core.logger import setup_logger
from backend.core.config import config

logger = setup_logger(__name__)


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=config.vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = config.collection_name
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "SharePoint documents embeddings"}
            )
            logger.info(f"Connected to collection: {self.collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Failed to get/create collection: {str(e)}")
            raise

    def add_documents(self, chunks, embeddings):
        if not chunks or not embeddings:
            logger.warning("No chunks or embeddings provided")
            return

        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        try:
            ids = [f"{chunk['metadata']['document_id']}_{chunk['metadata']['chunk_index']}"
                   for chunk in chunks]

            texts = [chunk['text'] for chunk in chunks]

            metadatas = []
            for chunk in chunks:
                metadata = chunk['metadata'].copy()
                metadata['indexed_at'] = datetime.utcnow().isoformat()
                metadata['chunk_index'] = str(metadata['chunk_index'])
                metadata['chunk_size'] = str(metadata['chunk_size'])
                metadata['start_char'] = str(metadata['start_char'])
                metadata['end_char'] = str(metadata['end_char'])
                metadatas.append(metadata)

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Added {len(chunks)} document chunks to vector store")

        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {str(e)}")
            raise

    def search(self, query_embedding, top_k=5, filter_metadata=None):
        try:
            logger.debug(f"Searching for top {top_k} similar documents")

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )

            retrieved_docs = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    doc = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    retrieved_docs.append(doc)

            logger.info(f"Retrieved {len(retrieved_docs)} documents from vector store")
            return retrieved_docs

        except Exception as e:
            logger.error(f"Failed to search vector store: {str(e)}")
            raise

    def delete_document(self, document_id):
        try:
            self.collection.delete(
                where={"document_id": document_id}
            )
            logger.info(f"Deleted document {document_id} from vector store")
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise

    def get_document_count(self):
        try:
            count = self.collection.count()
            logger.debug(f"Vector store contains {count} chunks")
            return count
        except Exception as e:
            logger.error(f"Failed to get document count: {str(e)}")
            return 0

    def clear_collection(self):
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.warning("Cleared all documents from vector store")
        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            raise
