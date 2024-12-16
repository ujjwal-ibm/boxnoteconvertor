"""Box API utilities for downloading files."""
from typing import Optional, Tuple
import requests
from pathlib import Path
from ..utils.logger import setup_logger
import re
logger = setup_logger(__name__)

class BoxAPIClient:
    """Client for interacting with Box API."""
    
    def __init__(self, api_token: str):
        """Initialize Box API client with access token."""
        self.api_token = api_token
        self.base_url = "https://api.box.com/2.0"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json"
        }
    
    def get_file_info(self, file_id: str) -> Optional[dict]:
        """Get file information from Box."""
        try:
            logger.debug(f"Fetching info for file: {file_id}")
            response = requests.get(
                f"{self.base_url}/files/{file_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return None
    
    def download_file(self, file_id: str, output_path: Path) -> bool:
        """Download file directly using Box API."""
        try:
            # Get download URL
            response = requests.get(
                f"{self.base_url}/files/{file_id}/content",
                headers=self.headers,
                allow_redirects=False
            )
            
            if response.status_code == 302:
                download_url = response.headers.get('location')
                if not download_url:
                    raise ValueError("No download URL in response")
                    
                # Download file
                response = requests.get(download_url)
                response.raise_for_status()
                
                # Save file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                    
                logger.info(f"Successfully downloaded file to {output_path}")
                return True
                
            response.raise_for_status()
            return False
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False
    
    @staticmethod
    def extract_file_id_from_url(url: str) -> Optional[str]:
        """Extract Box file ID from URL."""
        import re
        patterns = [
            r"box\.com/s/([a-zA-Z0-9]+)",  # Shared link
            r"box\.com/file/(\d+)",         # Direct file link
            r"^(\d+)$"                      # Raw file ID
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, url):
                return match.group(1)
        return None