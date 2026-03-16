import time
import hashlib
import threading
from collections import OrderedDict
from backend.core.config import config
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class ResponseCache:
    """Simple thread-safe in-memory LRU cache with TTL for RAG responses."""

    def __init__(self):
        self.max_size = config.cache_max_size
        self.ttl_seconds = config.cache_ttl_seconds
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    def _make_key(self, query, top_k, temperature):
        normalized = query.strip().lower()
        raw = f"{normalized}|{top_k}|{temperature}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, query, top_k=5, temperature=0.7):
        key = self._make_key(query, top_k, temperature)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry['timestamp'] < self.ttl_seconds:
                    self._cache.move_to_end(key)
                    logger.info(f"Cache HIT for query: {query[:60]}...")
                    return entry['response']
                else:
                    del self._cache[key]
                    logger.debug(f"Cache EXPIRED for query: {query[:60]}...")
        return None

    def put(self, query, top_k, temperature, response):
        key = self._make_key(query, top_k, temperature)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            self._cache[key] = {
                'response': response,
                'timestamp': time.time()
            }
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
            logger.info(f"Cache STORE for query: {query[:60]}...")

    def clear(self):
        with self._lock:
            self._cache.clear()
            logger.info("Response cache cleared")

    def stats(self):
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
            }
