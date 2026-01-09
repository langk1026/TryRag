import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from backend.services.indexing_service import IndexingService
from backend.core.config import config
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class IndexScheduler:
    def __init__(self):
        self.indexing_service = IndexingService()
        self.scheduler = BlockingScheduler()

    def run_scheduled_index(self):
        logger.info("=" * 80)
        logger.info(f"Index Revolution triggered at {datetime.now()}")
        logger.info("=" * 80)

        try:
            result = self.indexing_service.incremental_index()

            logger.info("Index Revolution completed")
            logger.info(f"Documents processed: {result['documents_processed']}")
            logger.info(f"Chunks created: {result['chunks_created']}")

            if result['errors']:
                logger.warning(f"Errors encountered: {len(result['errors'])}")
                for error in result['errors']:
                    logger.warning(f"  - {error}")

        except Exception as e:
            logger.error(f"Index Revolution failed: {str(e)}")

    def start(self):
        logger.info("Starting Index Scheduler")
        logger.info(f"Indexing interval: {config.index_schedule_minutes} minutes")

        self.scheduler.add_job(
            self.run_scheduled_index,
            trigger=IntervalTrigger(minutes=config.index_schedule_minutes),
            id='incremental_index',
            name='Incremental Index Revolution',
            replace_existing=True
        )

        logger.info("Running initial index...")
        self.run_scheduled_index()

        logger.info("Scheduler started. Press Ctrl+C to stop.")
        self.scheduler.start()


if __name__ == "__main__":
    scheduler = IndexScheduler()
    scheduler.start()
