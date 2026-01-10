import os
from pathlib import Path


class Config:
    def __init__(self):
        self.sharepoint_site_url = os.getenv('SHAREPOINT_SITE_URL', '')
        self.sharepoint_client_id = os.getenv('SHAREPOINT_CLIENT_ID', '')
        self.sharepoint_client_secret = os.getenv('SHAREPOINT_CLIENT_SECRET', '')
        self.sharepoint_tenant_id = os.getenv('SHAREPOINT_TENANT_ID', '')
        self.sharepoint_document_library = os.getenv('SHAREPOINT_DOCUMENT_LIBRARY', 'Shared Documents')

        self.google_api_key = os.getenv('GOOGLE_API_KEY', '')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'models/text-embedding-004')
        self.llm_model = os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')

        self.vector_db_path = os.getenv('VECTOR_DB_PATH', './data/chromadb')
        self.collection_name = os.getenv('COLLECTION_NAME', 'sharepoint_documents')

        self.index_schedule_minutes = int(os.getenv('INDEX_SCHEDULE_MINUTES', '30'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '1000'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '200'))

        self.api_host = os.getenv('API_HOST', '0.0.0.0')
        self.api_port = int(os.getenv('API_PORT', '8000'))
        self.cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', './logs/app.log')

        self.hyde_enabled = os.getenv('HYDE_ENABLED', 'true').lower() == 'true'
        self.hyde_temperature = float(os.getenv('HYDE_TEMPERATURE', '0.7'))
        self.hyde_max_tokens = int(os.getenv('HYDE_MAX_TOKENS', '300'))

        self._ensure_directories()

    def _ensure_directories(self):
        Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


config = Config()
