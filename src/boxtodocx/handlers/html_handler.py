"""Handler for converting Box documents to HTML format."""
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json, os
import requests
from requests.exceptions import RequestException

from ..mappers.html_mapper import HTMLMapper
from ..utils.browser import BrowserManager
from ..utils.image import ImageManager
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
        self.browser_manager = BrowserManager()
        
    def convert_to_html(
        self, 
        content: List[Dict],
        credentials: Optional[Dict[str, str]] = None
    ) -> Tuple[str, List[Path]]:
        """
        Convert Box content to HTML with optional image download.
        
        Args:
            content: Box document content
            credentials: Optional Box credentials for image download
            
        Returns:
            Tuple of (HTML content, list of downloaded image paths)
        
        Raises:
            ValueError: If content format is invalid
        """
        try:
            # First process and download images
            self._process_images(content, credentials)
            
            # Pass the image mappings to the mapper
            self.mapper.image_paths = {
                url: os.path.relpath(path, self.output_dir)
                for url, path in self.image_manager.downloaded_images.items()
            }
            
            # Generate HTML
            html_content = self.mapper.map_content(content)
            
            return html_content, list(self.image_manager.downloaded_images.values())
            
        except Exception as e:
            logger.error(f"HTML conversion failed: {str(e)}")
            raise
            
        finally:
            self.cleanup()
    
    def convert_file(
        self, 
        input_path: str,
        credentials: Optional[Dict[str, str]] = None
    ) -> Tuple[Path, List[Path]]:
        """
        Convert a Box note file to HTML.
        
        Args:
            input_path: Path to input file
            credentials: Optional Box credentials for image download
            
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
                
            html_content, image_paths = self.convert_to_html(content, credentials)
            
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
        if not image_urls or not credentials:
            return
            
        try:
            # Initialize browser and authenticate
            self.browser_manager.initialize_browser(headless=True)
            self.browser_manager.authenticate_box(credentials)
            
            # Create session with authenticated cookies
            session = requests.Session()
            for cookie in self.browser_manager.cookies or []:
                session.cookies.set(cookie['name'], cookie['value'])
                
            # Process each image
            for url in image_urls:
                try:
                    direct_url = None
                    filename = None
                    
                    if 'box.com' in url.lower():
                        # Handle Box links
                        direct_url, filename = self.image_manager.extract_image_links(
                            self.browser_manager.driver, url
                        )
                    else:
                        # Handle direct URLs
                        direct_url, filename = url, None
                    
                    if direct_url:
                        # Add image to download queue and store mapping
                        local_path = self.image_manager.add_pending_image(direct_url, filename)
                        logger.debug(f"Added image to queue: {url} -> {local_path}")
                        
                except Exception as e:
                    logger.error(f"Error processing image {url}: {str(e)}")
                    continue
                    
            # Download all pending images
            self.image_manager.download_pending_images(session)
            
            # Log successful downloads
            for url, path in self.image_manager.downloaded_images.items():
                logger.info(f"Successfully downloaded: {url} -> {path}")
                
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
        finally:
            self.browser_manager.cleanup()
            
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
        return urls
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.browser_manager.cleanup()
        self.image_manager.cleanup()