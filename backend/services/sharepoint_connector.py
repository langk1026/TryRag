from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from datetime import datetime
from backend.core.logger import setup_logger
from backend.core.config import config

logger = setup_logger(__name__)


class SharePointConnector:
    def __init__(self):
        self.site_url = config.sharepoint_site_url
        self.document_library = config.sharepoint_document_library
        self.ctx = None
        self._authenticate()

    def _authenticate(self):
        try:
            credentials = ClientCredential(
                config.sharepoint_client_id,
                config.sharepoint_client_secret
            )
            self.ctx = ClientContext(self.site_url).with_credentials(credentials)
            logger.info(f"Successfully authenticated to SharePoint site: {self.site_url}")
        except Exception as e:
            logger.error(f"SharePoint authentication failed: {str(e)}")
            raise

    def get_all_documents(self):
        try:
            logger.info(f"Fetching all documents from library: {self.document_library}")

            library = self.ctx.web.lists.get_by_title(self.document_library)
            items = library.items.get().execute_query()

            documents = []
            for item in items:
                if item.file_system_object_type == 0:
                    doc_info = {
                        'id': item.properties['UniqueId'],
                        'name': item.properties['FileLeafRef'],
                        'path': item.properties['FileRef'],
                        'modified': item.properties.get('Modified', ''),
                        'size': item.properties.get('File_x0020_Size', 0),
                        'author': item.properties.get('Author', {}).get('Title', 'Unknown')
                    }
                    documents.append(doc_info)

            logger.info(f"Retrieved {len(documents)} documents from SharePoint")
            return documents

        except Exception as e:
            logger.error(f"Failed to fetch documents: {str(e)}")
            raise

    def get_documents_modified_since(self, last_indexed_time):
        try:
            all_documents = self.get_all_documents()

            modified_docs = []
            for doc in all_documents:
                doc_modified = datetime.fromisoformat(doc['modified'].replace('Z', '+00:00'))
                if doc_modified > last_indexed_time:
                    modified_docs.append(doc)

            logger.info(f"Found {len(modified_docs)} documents modified since {last_indexed_time}")
            return modified_docs

        except Exception as e:
            logger.error(f"Failed to fetch modified documents: {str(e)}")
            raise

    def download_file_content(self, file_path):
        try:
            logger.debug(f"Downloading content from: {file_path}")

            file_obj = self.ctx.web.get_file_by_server_relative_url(file_path)
            content = file_obj.read()
            self.ctx.execute_query()

            logger.debug(f"Successfully downloaded {len(content)} bytes")
            return content

        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {str(e)}")
            raise

    def get_file_metadata(self, file_path):
        try:
            file_obj = self.ctx.web.get_file_by_server_relative_url(file_path)
            self.ctx.load(file_obj)
            self.ctx.execute_query()

            metadata = {
                'name': file_obj.properties['Name'],
                'size': file_obj.properties['Length'],
                'modified': file_obj.properties['TimeLastModified'],
                'created': file_obj.properties['TimeCreated'],
                'url': f"{self.site_url}{file_path}"
            }

            return metadata

        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {str(e)}")
            raise
