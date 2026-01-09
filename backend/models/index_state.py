import json
from datetime import datetime
from pathlib import Path
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class IndexState:
    def __init__(self, state_file='./data/index_state.json'):
        self.state_file = Path(state_file)
        self._ensure_state_file()

    def _ensure_state_file(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.state_file.exists():
            self._write_state({'last_indexed': None})

    def _read_state(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read index state: {str(e)}")
            return {'last_indexed': None}

    def _write_state(self, state):
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write index state: {str(e)}")

    def get_last_indexed_time(self):
        state = self._read_state()
        last_indexed_str = state.get('last_indexed')

        if last_indexed_str:
            return datetime.fromisoformat(last_indexed_str)
        return None

    def update_last_indexed_time(self, timestamp):
        state = self._read_state()
        state['last_indexed'] = timestamp.isoformat()
        self._write_state(state)
        logger.info(f"Updated last indexed time to {timestamp}")
