from backend.core.logger import setup_logger
from backend.core.config import config

logger = setup_logger(__name__)


class RecursiveCharacterSplitter:
    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or config.chunk_size
        self.chunk_overlap = chunk_overlap or config.chunk_overlap

        self.separators = [
            "\n\n\n",
            "\n\n",
            "\n",
            ". ",
            "! ",
            "? ",
            "; ",
            ", ",
            " ",
            ""
        ]

    def split_text(self, text, metadata=None):
        if not text or not text.strip():
            return []

        logger.debug(f"Starting recursive split of {len(text)} characters")

        chunks = self._recursive_split(text, self.separators)

        result_chunks = []
        for idx, chunk_text in enumerate(chunks):
            if chunk_text.strip():
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': idx,
                    'chunk_size': len(chunk_text),
                    'chunking_method': 'recursive_character'
                })

                result_chunks.append({
                    'text': chunk_text.strip(),
                    'metadata': chunk_metadata
                })

        logger.debug(f"Created {len(result_chunks)} chunks from recursive split")
        return result_chunks

    def _recursive_split(self, text, separators):
        if not separators:
            return self._split_by_length(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            return self._split_by_length(text)

        splits = text.split(separator)

        merged_chunks = []
        current_chunk = ""

        for split in splits:
            if not split:
                continue

            test_chunk = current_chunk + separator + split if current_chunk else split

            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    merged_chunks.append(current_chunk)

                if len(split) > self.chunk_size:
                    sub_chunks = self._recursive_split(split, remaining_separators)
                    merged_chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = split

        if current_chunk:
            merged_chunks.append(current_chunk)

        if self.chunk_overlap > 0:
            merged_chunks = self._add_overlap(merged_chunks)

        return merged_chunks

    def _split_by_length(self, text):
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

    def _add_overlap(self, chunks):
        if len(chunks) <= 1:
            return chunks

        overlapped_chunks = []

        for i in range(len(chunks)):
            chunk = chunks[i]

            if i > 0:
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-self.chunk_overlap:]
                chunk = overlap_text + " " + chunk

            overlapped_chunks.append(chunk)

        return overlapped_chunks

    def chunk_text_with_pages(self, pages_data, metadata=None):
        all_chunks = []

        for page_data in pages_data:
            page_number = page_data['page_number']
            page_text = page_data['text']

            page_metadata = metadata.copy() if metadata else {}
            page_metadata['page_number'] = page_number

            page_chunks = self.split_text(page_text, page_metadata)

            all_chunks.extend(page_chunks)

        logger.info(f"Created {len(all_chunks)} chunks from {len(pages_data)} pages")
        return all_chunks
