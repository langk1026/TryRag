from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from backend.core.config import config
from backend.core.logger import setup_logger

logger = setup_logger(__name__)


class LocalDocumentConnector:
    def __init__(self):
        self.root_path = Path(config.local_documents_path).resolve()
        self.supported_extensions = {'.pdf', '.docx', '.txt', '.xlsx', '.md'}
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.site_url = f"file://{self.root_path.as_posix()}/"

        logger.info(f"Using local documents directory: {self.root_path}")

    def get_all_documents(self):
        documents = []

        for file_path in self.root_path.rglob('*'):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in self.supported_extensions:
                continue

            relative_path = file_path.relative_to(self.root_path).as_posix()
            modified = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)

            documents.append({
                'id': self._build_document_id(relative_path),
                'name': file_path.name,
                'path': relative_path,
                'modified': modified.isoformat().replace('+00:00', 'Z'),
                'size': file_path.stat().st_size,
                'author': 'local',
                'download_url': '',
                'web_url': f"{self.site_url}{relative_path}"
            })

        logger.info(f"Retrieved {len(documents)} documents from local folder")
        return documents

    def get_documents_modified_since(self, last_indexed_time):
        modified_documents = []

        for document in self.get_all_documents():
            modified_time = datetime.fromisoformat(document['modified'].replace('Z', '+00:00'))
            if modified_time > last_indexed_time:
                modified_documents.append(document)

        logger.info(f"Found {len(modified_documents)} local documents modified since {last_indexed_time}")
        return modified_documents

    def download_file_content(self, file_path):
        resolved_path = (self.root_path / file_path).resolve()

        if not self._is_within_root(resolved_path):
            raise Exception(f"Invalid local document path: {file_path}")

        if not resolved_path.exists() or not resolved_path.is_file():
            raise Exception(f"Local document not found: {file_path}")

        with open(resolved_path, 'rb') as f:
            return f.read()

    def _build_document_id(self, relative_path):
        return sha1(relative_path.encode('utf-8')).hexdigest()

    def _is_within_root(self, candidate_path):
        try:
            candidate_path.relative_to(self.root_path)
            return True
        except ValueError:
            return False
