from backend.core.logger import setup_logger
from backend.core.config import config

logger = setup_logger(__name__)


class TextChunker:
    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or config.chunk_size
        self.chunk_overlap = chunk_overlap or config.chunk_overlap

    def chunk_text(self, text, metadata=None):
        if not text or not text.strip():
            return []

        chunks = []
        text_length = len(text)
        start = 0
        chunk_index = 0

        while start < text_length:
            end = start + self.chunk_size

            if end < text_length:
                end = self._find_sentence_boundary(text, end)

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': chunk_index,
                    'chunk_size': len(chunk_text),
                    'start_char': start,
                    'end_char': end
                })

                chunks.append({
                    'text': chunk_text,
                    'metadata': chunk_metadata
                })

                chunk_index += 1

            start = end - self.chunk_overlap

            if start >= text_length:
                break

        logger.debug(f"Created {len(chunks)} chunks from text of length {text_length}")
        return chunks

    def _find_sentence_boundary(self, text, position):
        sentence_endings = ['. ', '.\n', '! ', '!\n', '? ', '?\n']

        search_window = 100
        search_start = max(0, position - search_window)
        search_end = min(len(text), position + search_window)
        search_text = text[search_start:search_end]

        best_boundary = position
        for ending in sentence_endings:
            idx = search_text.rfind(ending)
            if idx != -1:
                actual_position = search_start + idx + len(ending)
                if actual_position > position - search_window:
                    best_boundary = actual_position
                    break

        return best_boundary
