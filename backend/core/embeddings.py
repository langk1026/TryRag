import google.generativeai as genai
from backend.core.logger import setup_logger
from backend.core.config import config

logger = setup_logger(__name__)


class EmbeddingService:
    def __init__(self):
        genai.configure(api_key=config.google_api_key)
        self.model = config.embedding_model
        self.batch_size = config.batch_size

    def generate_embeddings(self, texts):
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            try:
                logger.debug(f"Generating embeddings for batch {i//self.batch_size + 1} ({len(batch)} texts)")

                batch_embeddings = []
                for text in batch:
                    result = genai.embed_content(
                        model=self.model,
                        content=text,
                        task_type="retrieval_document"
                    )
                    batch_embeddings.append(result['embedding'])

                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Generated {len(batch_embeddings)} embeddings")

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch: {str(e)}")
                raise

        logger.info(f"Generated total of {len(all_embeddings)} embeddings")
        return all_embeddings

    def generate_single_embedding(self, text):
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Failed to generate single embedding: {str(e)}")
            raise
