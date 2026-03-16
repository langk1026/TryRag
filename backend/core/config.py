import os
from pathlib import Path


class Config:
    def __init__(self):
        raw_environment = os.getenv('ENVIRONMENT', 'development').strip().lower()
        if raw_environment not in ('development', 'production'):
            raw_environment = 'development'
        self.environment = raw_environment

        self.sharepoint_site_url = os.getenv('SHAREPOINT_SITE_URL', '')
        self.sharepoint_client_id = os.getenv('SHAREPOINT_CLIENT_ID', '')
        self.sharepoint_client_secret = os.getenv('SHAREPOINT_CLIENT_SECRET', '')
        self.sharepoint_tenant_id = os.getenv('SHAREPOINT_TENANT_ID', '')
        self.sharepoint_document_library = os.getenv('SHAREPOINT_DOCUMENT_LIBRARY', 'Shared Documents')
        self.local_documents_path = os.getenv('LOCAL_DOCUMENTS_PATH', '/tmp/tryrag_documents')

        self.google_api_key = os.getenv('GOOGLE_API_KEY', '')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'gemini-embedding-2-preview')
        self.llm_model = os.getenv('LLM_MODEL', 'gemini-2.0-flash-exp')

        self.vector_db_path = os.getenv('VECTOR_DB_PATH', './data/chromadb')
        self.collection_name = os.getenv('COLLECTION_NAME', 'sharepoint_documents')

        self.index_schedule_minutes = int(os.getenv('INDEX_SCHEDULE_MINUTES', '30'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '1000'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '200'))

        self.api_host = os.getenv('API_HOST', '0.0.0.0')
        self.api_port = int(os.getenv('API_PORT', '8000'))
        self.api_reload = os.getenv('API_RELOAD', 'false').lower() == 'true'
        self.cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', './logs/app.log')

        self.hyde_enabled = os.getenv('HYDE_ENABLED', 'true').lower() == 'true'
        self.hyde_temperature = float(os.getenv('HYDE_TEMPERATURE', '0.7'))
        self.hyde_max_tokens = int(os.getenv('HYDE_MAX_TOKENS', '300'))

        self.multi_query_enabled = os.getenv('MULTI_QUERY_ENABLED', 'true').lower() == 'true'
        self.multi_query_count = int(os.getenv('MULTI_QUERY_COUNT', '3'))
        self.hybrid_search_enabled = os.getenv('HYBRID_SEARCH_ENABLED', 'true').lower() == 'true'
        self.hybrid_vector_weight = float(os.getenv('HYBRID_VECTOR_WEIGHT', '0.6'))
        self.hybrid_keyword_weight = float(os.getenv('HYBRID_KEYWORD_WEIGHT', '0.4'))
        self.hybrid_candidate_pool = int(os.getenv('HYBRID_CANDIDATE_POOL', '20'))

        self.reranker_enabled = os.getenv('RERANKER_ENABLED', 'true').lower() == 'true'
        self.reranker_model = os.getenv('RERANKER_MODEL', 'BAAI/bge-reranker-v2-m3')
        self.reranker_top_n = int(os.getenv('RERANKER_TOP_N', '5'))

        self.ragas_enabled = os.getenv('RAGAS_ENABLED', 'true').lower() == 'true'
        self.faithfulness_threshold = float(os.getenv('FAITHFULNESS_THRESHOLD', '0.75'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '2'))

        self.telemetry_enabled = os.getenv('TELEMETRY_ENABLED', 'true').lower() == 'true'
        self.telemetry_service_name = os.getenv('TELEMETRY_SERVICE_NAME', 'tryrag-backend')
        self.telemetry_otlp_endpoint = os.getenv('TELEMETRY_OTLP_ENDPOINT', 'http://otel-collector:4317')
        self.telemetry_console_export = os.getenv('TELEMETRY_CONSOLE_EXPORT', 'false').lower() == 'true'

        self.cache_ttl_seconds = int(os.getenv('CACHE_TTL_SECONDS', '300'))
        self.cache_max_size = int(os.getenv('CACHE_MAX_SIZE', '100'))

        self.langfuse_enabled = os.getenv('LANGFUSE_ENABLED', 'false').lower() == 'true'
        self.langfuse_public_key = os.getenv('LANGFUSE_PUBLIC_KEY', '')
        self.langfuse_secret_key = os.getenv('LANGFUSE_SECRET_KEY', '')
        self.langfuse_host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')

        self._ensure_directories()

    def _ensure_directories(self):
        Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        if self.environment == 'development':
            Path(self.local_documents_path).mkdir(parents=True, exist_ok=True)


config = Config()
