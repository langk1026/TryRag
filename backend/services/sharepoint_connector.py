import requests
from datetime import datetime
from backend.core.logger import setup_logger
from backend.core.config import config

logger = setup_logger(__name__)


class SharePointConnector:
    def __init__(self):
        self.tenant_id = config.sharepoint_tenant_id
        self.client_id = config.sharepoint_client_id
        self.client_secret = config.sharepoint_client_secret
        self.site_url = config.sharepoint_site_url
        self.document_library = config.sharepoint_document_library
        self.access_token = None
        self.site_id = None
        self.drive_id = None
        self._authenticate()

    def _authenticate(self):
        try:
            url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()

            response_data = response.json()
            self.access_token = response_data['access_token']

            self._get_site_id()
            self._get_drive_id()

            masked_url = self.site_url.replace('https://', '').split('/')[0]
            logger.info(f"Successfully authenticated to SharePoint site: {masked_url}")
        except Exception as e:
            logger.error(f"SharePoint authentication failed: {str(e)}")
            raise

    def _get_site_id(self):
        try:
            site_path = self.site_url.replace('https://', '')
            headers = {'Authorization': f'Bearer {self.access_token}'}

            response = requests.get(
                f'https://graph.microsoft.com/v1.0/sites/{site_path}',
                headers=headers
            )
            response.raise_for_status()

            data = response.json()
            self.site_id = data['id'].split(',')[1]
            logger.debug(f"Retrieved site ID")
        except Exception as e:
            logger.error(f"Failed to get site ID: {str(e)}")
            raise

    def _get_drive_id(self):
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}

            response = requests.get(
                f'https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives',
                headers=headers
            )
            response.raise_for_status()

            data = response.json()
            for item in data['value']:
                if item['name'] == 'Documents':
                    self.drive_id = item['id']
                    logger.debug(f"Retrieved drive ID")
                    return

            raise Exception("Documents drive not found")
        except Exception as e:
            logger.error(f"Failed to get drive ID: {str(e)}")
            raise

    def get_all_documents(self):
        try:
            logger.info(f"Fetching all documents from path: {self.document_library}")

            documents = []
            self._traverse_folder(self.document_library, "", documents)

            logger.info(f"Retrieved {len(documents)} documents from SharePoint")
            return documents

        except Exception as e:
            logger.error(f"Failed to fetch documents: {str(e)}")
            raise

    def _traverse_folder(self, base_folder, current_path, documents):
        try:
            if current_path == "":
                url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{base_folder}:/children"
            else:
                url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{base_folder}/{current_path}:/children"

            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(url, headers=headers)

            if response.status_code == 404:
                raise Exception(f"SharePoint folder not found: '{base_folder}/{current_path}'")
            elif response.status_code == 403:
                raise Exception(f"Access denied to SharePoint folder: '{base_folder}/{current_path}'")

            response.raise_for_status()
            data = response.json()

            if 'value' not in data:
                raise Exception(f"SharePoint folder '{base_folder}/{current_path}' not found or inaccessible")

            for item in data['value']:
                if 'file' in item:
                    doc_info = {
                        'id': item['id'],
                        'name': item['name'],
                        'path': f"{base_folder}/{current_path}/{item['name']}" if current_path else f"{base_folder}/{item['name']}",
                        'modified': item['lastModifiedDateTime'],
                        'size': item.get('size', 0),
                        'author': item.get('createdBy', {}).get('user', {}).get('displayName', 'Unknown'),
                        'download_url': item.get('@microsoft.graph.downloadUrl', ''),
                        'web_url': item.get('webUrl', '')
                    }
                    documents.append(doc_info)
                    logger.debug(f"Found file: {doc_info['name']}")

                elif 'folder' in item:
                    new_path = f"{current_path}/{item['name']}" if current_path else item['name']
                    self._traverse_folder(base_folder, new_path, documents)

        except Exception as e:
            logger.error(f"Failed to traverse folder {base_folder}/{current_path}: {str(e)}")
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

            url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{file_path}"
            headers = {'Authorization': f'Bearer {self.access_token}'}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            file_data = response.json()
            download_url = file_data.get('@microsoft.graph.downloadUrl')

            if not download_url:
                raise Exception(f"No download URL found for file: {file_path}")

            download_response = requests.get(download_url)
            download_response.raise_for_status()

            content = download_response.content
            logger.debug(f"Successfully downloaded {len(content)} bytes")
            return content

        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {str(e)}")
            raise

    def get_file_metadata(self, file_path):
        try:
            url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{file_path}"
            headers = {'Authorization': f'Bearer {self.access_token}'}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            metadata = {
                'name': data['name'],
                'size': data.get('size', 0),
                'modified': data['lastModifiedDateTime'],
                'created': data['createdDateTime'],
                'url': data.get('webUrl', '')
            }

            return metadata

        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {str(e)}")
            raise
