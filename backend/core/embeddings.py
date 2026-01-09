import openai
from backend.core.logger import setup_logger
from backend.core.config import config

logger = setup_logger(__name__)


class EmbeddingService:
    def __init__(self):
        openai.api_key = config.openai_api_key
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

                response = openai.embeddings.create(
                    model=self.model,
                    input=batch
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Generated {len(batch_embeddings)} embeddings")

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch: {str(e)}")
                raise

        logger.info(f"Generated total of {len(all_embeddings)} embeddings")
        return all_embeddings

    def generate_single_embedding(self, text):
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else None
