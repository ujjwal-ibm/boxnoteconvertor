"""Handler for converting Box documents to HTML format."""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json, os
import requests
from requests.exceptions import RequestException

from ..mappers.html_mapper import HTMLMapper
from ..utils.browser import BrowserManager
from ..utils.image import ImageManager
from ..utils.box_api import BoxAPIClient
from ..utils.logger import setup_logger
from ..utils.constants import DEFAULT_OUTPUT_DIR

logger = setup_logger(__name__)

class HTMLHandler:
    """Handles conversion of Box documents to HTML format."""
    
    def __init__(self, output_dir: str = str(DEFAULT_OUTPUT_DIR)) -> None:
        """
        Initialize HTML handler.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.mapper = HTMLMapper()
        self.image_manager = ImageManager(str(self.output_dir / "images"))
        self.browser_manager = None  # Initialize as None
        self.api_client = None
        
    def set_browser_manager(self, browser_manager: Optional[BrowserManager]) -> None:
        """Set existing browser manager for reuse."""
        self.browser_manager = browser_manager

    def ensure_browser_initialized(self, credentials: Dict[str, str]) -> None:
        """Ensure browser is initialized and logged into Box."""
        if not self.browser_manager:
            self.browser_manager = BrowserManager()
            self.browser_manager.initialize_browser()
            self.browser_manager.authenticate_box(credentials)
            logger.info("Initialized and authenticated browser session")

    def set_api_token(self, api_token: str) -> None:
        """Set Box API token for direct downloads."""
        self.api_client = BoxAPIClient(api_token)

    def convert_to_html(
        self, 
        content: List[Dict],
        credentials: Optional[Dict[str, str]] = None,
        api_token: Optional[str] = None
    ) -> Tuple[str, List[Path]]:
        """Convert Box content to HTML with optional image download."""
        try:
            # Process images if we have either credentials or API token
            if credentials or api_token:
                self._process_images(content, credentials)
            
            # Generate HTML from content
            html_content = self.mapper.map_content(content)
            return html_content, list(self.image_manager.downloaded_images.values())
            
        except Exception as e:
            logger.error(f"HTML conversion failed: {str(e)}")
            raise


    def convert_file(
        self, 
        input_path: str,
        credentials: Optional[Dict[str, str]] = None,
        api_token: Optional[str] = None
    ) -> Tuple[Path, List[Path]]:
        """
        Convert a Box note file to HTML.
        
        Args:
            input_path: Path to input file
            credentials: Optional Box credentials for image download
            api_token: Optional Box API token for direct download

        Returns:
            Tuple of (HTML output path, list of downloaded image paths)
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            json.JSONDecodeError: If input file is invalid JSON
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise ValueError("Invalid BoxNote format: root must be an object")
                
            content = data.get('doc', {}).get('content', [])
            if not isinstance(content, list):
                raise ValueError("Invalid BoxNote format: content must be a list")
                
            html_content, image_paths = self.convert_to_html(content, credentials, api_token)
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / input_path.with_suffix('.html').name
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info(f"Created HTML file: {output_path}")
            return output_path, image_paths
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in input file: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"File conversion failed: {str(e)}")
            raise
    

    def _process_images(
        self,
        content: List[Dict],
        credentials: Optional[Dict[str, str]]
    ) -> None:
        """Process and download images from content."""
        image_urls = self._extract_image_urls(content)
        if not image_urls:
            return

        try:
            # Only initialize browser if not already initialized
            if credentials and not self.browser_manager:
                self.browser_manager = BrowserManager()
                self.browser_manager.initialize_browser()
                self.browser_manager.authenticate_box(credentials)
                
            session = requests.Session()
            if self.browser_manager and self.browser_manager.cookies:
                for cookie in self.browser_manager.cookies:
                    session.cookies.set(cookie['name'], cookie['value'])
                    
            # Make sure image directory is within the current output directory
            image_dir = self.output_dir / "images"
            self.image_manager.output_dir = image_dir

            for url in image_urls:
                try:
                    if 'box.com' in url.lower() and self.browser_manager:
                        result = self.image_manager.extract_image_links(
                            self.browser_manager.driver,
                            url
                        )
                        direct_url = result[0] if result else None
                    else:
                        direct_url = url
                        
                    if direct_url:
                        local_path = self.image_manager.add_pending_image(direct_url)
                        if local_path:
                            # Use path relative to current output directory
                            rel_path = local_path.relative_to(self.output_dir)
                            self.mapper.image_paths[url] = rel_path
                            logger.debug(f"Added image mapping: {url} -> {rel_path}")
                        
                except Exception as e:
                    logger.error(f"Error processing image {url}: {str(e)}")
                    continue
                    
            self.image_manager.download_pending_images(session)
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")

    def _download_images_with_api(self, image_urls: List[str]) -> None:
        """Download images using Box API."""
        if not self.api_client:
            return
            
        for url in image_urls:
            try:
                # Try to download using API
                if result := self.image_manager.download_with_api(url, self.api_client):
                    local_path, filename = result
                    self.mapper.image_paths[url] = local_path.relative_to(self.output_dir)
                    logger.info(f"Downloaded image via API: {filename}")
                else:
                    logger.warning(f"Failed to download image via API: {url}")
                    
            except Exception as e:
                logger.error(f"API download failed for {url}: {str(e)}")
       

    def _extract_image_urls(self, content: List[Dict]) -> List[str]:
        """Extract image URLs from content recursively."""
        urls = []
        
        def extract(items: List[Dict]) -> None:
            for item in items:
                if item.get('type') == 'image' and 'attrs' in item:
                    attrs = item['attrs']
                    # Try different possible image source attributes
                    url = attrs.get('src') or attrs.get('boxSharedLink') or attrs.get('url')
                    if url:
                        logger.debug(f"Found image URL: {url}")
                        urls.append(url)
                
                # Handle legacy box_image format
                elif item.get('type') == 'box_image' and 'attrs' in item:
                    attrs = item['attrs']
                    if file_id := attrs.get('file_id'):
                        url = f"https://app.box.com/file/{file_id}"
                        logger.debug(f"Found Box image ID: {file_id}")
                        urls.append(url)
                
                # Recurse into content
                if 'content' in item and isinstance(item['content'], list):
                    extract(item['content'])
        
        extract(content)
        logger.info(f"Found {len(urls)} images")
        if urls:
            logger.debug(f"Image URLs found: {urls}")
        return urls
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Only cleanup browser if we created it
        if hasattr(self, 'browser_manager') and self.browser_manager:
            self.browser_manager.cleanup()
            self.browser_manager = None