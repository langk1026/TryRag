import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.logger import setup_logger
from backend.services.sharepoint_connector import SharePointConnector
from backend.services.indexing_service import IndexingService
from backend.core.rag_engine import RAGEngine

logger = setup_logger(__name__)


def check_environment():
    logger.info("Checking environment configuration...")

    required_vars = [
        'SHAREPOINT_SITE_URL',
        'SHAREPOINT_CLIENT_ID',
        'SHAREPOINT_CLIENT_SECRET',
        'GOOGLE_API_KEY'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please configure your .env file")
        return False

    logger.info("Environment configuration OK")
    return True


def test_sharepoint_connection():
    logger.info("Testing SharePoint connection...")

    try:
        sp = SharePointConnector()
        documents = sp.get_all_documents()

        logger.info(f"Successfully connected to SharePoint")
        logger.info(f"Found {len(documents)} documents")

        if documents:
            logger.info(f"Sample document: {documents[0]['name']}")

        return True

    except Exception as e:
        logger.error(f"SharePoint connection failed: {str(e)}")
        return False


def run_initial_index():
    logger.info("Starting initial indexing...")

    try:
        indexing_service = IndexingService()
        result = indexing_service.full_reindex()

        logger.info("=" * 80)
        logger.info("INDEXING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Status: {result['status']}")
        logger.info(f"Documents processed: {result['documents_processed']}")
        logger.info(f"Chunks created: {result['chunks_created']}")

        if result['errors']:
            logger.warning(f"Errors encountered: {len(result['errors'])}")
            for error in result['errors'][:5]:
                logger.warning(f"  - {error}")

        return True

    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        return False


def test_query():
    logger.info("Testing query functionality...")

    try:
        rag_engine = RAGEngine()
        test_question = "What documents are available?"

        logger.info(f"Query: {test_question}")
        result = rag_engine.query(test_question, top_k=3)

        logger.info("=" * 80)
        logger.info("QUERY TEST COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Answer: {result['answer'][:200]}...")
        logger.info(f"Sources used: {result['num_sources']}")

        return True

    except Exception as e:
        logger.error(f"Query test failed: {str(e)}")
        return False


def main():
    logger.info("=" * 80)
    logger.info("RAG APPLICATION QUICK START")
    logger.info("=" * 80)

    if not check_environment():
        sys.exit(1)

    if not test_sharepoint_connection():
        logger.error("Cannot proceed without SharePoint connection")
        sys.exit(1)

    logger.info("")
    user_input = input("Run initial indexing? This may take several minutes. (y/n): ")

    if user_input.lower() == 'y':
        if not run_initial_index():
            logger.error("Indexing failed")
            sys.exit(1)

        logger.info("")
        logger.info("Testing query functionality...")
        test_query()

    logger.info("=" * 80)
    logger.info("QUICK START COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Start the backend: python backend/main.py")
    logger.info("2. Start the frontend: cd frontend && npm run dev")
    logger.info("3. Start the scheduler: python scripts/index_scheduler.py")
    logger.info("")
    logger.info("Visit http://localhost:3000 to use the application")


if __name__ == "__main__":
    main()
