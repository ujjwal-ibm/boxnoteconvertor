"""Image handling utilities for downloading and processing Box images."""
from typing import Optional, Dict, List, Tuple
import os
import time
import hashlib, mimetypes, re
import requests
from pathlib import Path
from ..utils.box_api import BoxAPIClient
from urllib.parse import urlparse
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from .constants import DEFAULT_IMAGE_DIR
from .logger import setup_logger

logger = setup_logger(__name__)

class ImageManager:
    """Manages image downloads and processing from Box."""
    
    def __init__(self, output_dir: str = str(DEFAULT_IMAGE_DIR)) -> None:
        self.output_dir = Path(output_dir)
        self.pending_images: List[Tuple[str, Path]] = []
        self.downloaded_images: Dict[str, Path] = {}
    
    def add_pending_image(self, image_url: str, filename: Optional[str] = None) -> Path:
        """
        Add an image URL to the download queue.
        
        Args:
            image_url: URL of the image to download
            
        Returns:
            Path where the image will be saved
        """
        image_path = self._generate_image_path(image_url, filename)
        self.pending_images.append((image_url, image_path))
        return image_path
    
    def _generate_image_path(self, url: str, filename: Optional[str] = None) -> Path:
        """
        Generate a unique path for the image based on URL and filename.
        
        Args:
            url: URL of the image
            filename: Optional original filename
            
        Returns:
            Path object for the image
        """
        if filename:
            # Clean filename of invalid characters
            clean_filename = re.sub(r'[<>:"/\\|?*]', '', filename)
            
            # Ensure filename has correct extension
            current_ext = Path(clean_filename).suffix.lower()
            if current_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                # If it's jpeg, standardize to jpg
                if current_ext in ['.jpg', '.jpeg']:
                    clean_filename = clean_filename.rsplit('.', 1)[0] + '.jpg'
            else:
                # Add extension if missing
                clean_filename = clean_filename + self._get_extension(url)
        else:
            # Generate filename from URL
            url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
            clean_filename = f"image_{url_hash}{self._get_extension(url)}"

        # Ensure filename is unique
        base = clean_filename.rsplit('.', 1)[0]
        ext = clean_filename.rsplit('.', 1)[1]
        counter = 1
        while (self.output_dir / clean_filename).exists():
            clean_filename = f"{base}_{counter}.{ext}"
            counter += 1

        return self.output_dir / clean_filename
    
    def _get_extension(self, url: str, content_type: Optional[str] = None) -> str:
        """
        Get appropriate file extension for image.
        
        Args:
            url: Original image URL
            content_type: Optional content-type from response headers
            
        Returns:
            Appropriate file extension including the dot
        """
        # Define extension mappings
        content_type_mapping = {
            'image/jpeg': '.jpg',  # Always use .jpg for JPEG images
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp'
        }
        
        # Try to get extension from content-type first
        if content_type:
            content_type = content_type.lower().split(';')[0]
            if ext := content_type_mapping.get(content_type):
                logger.debug(f"Using extension {ext} from content-type {content_type}")
                return ext
        
        # Try to get from URL path
        from urllib.parse import urlparse
        path = urlparse(url).path.lower()
        
        # Handle known extensions
        if path.endswith(('.jpg', '.jpeg')):
            return '.jpg'  # Always use .jpg
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.gif'):
            return '.gif'
        elif path.endswith('.bmp'):
            return '.bmp'
        
        # Default to .jpg if we can't determine
        logger.debug(f"Could not determine extension from URL {url}, using default .jpg")
        return '.jpg'
    
    def download_pending_images(self, session: requests.Session) -> None:
        """Download all pending images using the provided session."""
        if not self.pending_images:
            return
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for url, path in self.pending_images:
            try:
                if not path.exists():  # Skip if already downloaded
                    response = session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Check content type and adjust extension if needed
                    content_type = response.headers.get('content-type')
                    if content_type:
                        correct_ext = self._get_extension(url, content_type)
                        if path.suffix.lower() != correct_ext:
                            # Update path with correct extension
                            path = path.with_suffix(correct_ext)
                    
                    path.write_bytes(response.content)
                    logger.info(f"Downloaded image: {path.name}")
                    
                self.downloaded_images[url] = path
                
            except requests.RequestException as e:
                logger.error(f"Failed to download image {url}: {str(e)}")
                continue
            
        self.pending_images.clear()
    
    def extract_image_links(self, driver: WebDriver, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract direct image link from Box preview page.
        
        Args:
            driver: Selenium WebDriver instance
            url: Box shared link URL
            
        Returns:
            Direct image URL if found, None otherwise
        """
        try:
            driver.get(url)
            time.sleep(2)  # Wait for page load

            # Extract filename from page
            filename_selectors = [
                "h1.bp-title",
                ".item-name",
                ".modal-title",
                "h1",
                "[data-testid='item-name']",
                ".file-name"
            ]
            
            filename = None
            for selector in filename_selectors:
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element and (text := element.text.strip()):
                        filename = text
                        break
                except:
                    continue

            # Extract image URL
            selectors = [
                "img.bp-preview-image-current",
                ".preview-image img",
                "img[src*='representation']",
                ".document-image",
                "img"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if url := element.get_attribute("src"):
                        return url, filename
                except:
                    continue

            return None, None

        except Exception as e:
            logger.error(f"Error extracting image link: {str(e)}")
            return None, None

    def download_with_api(self, url: str, api_client: BoxAPIClient) -> Optional[Tuple[Path, str]]:
        """
        Download image using Box API.
        
        Returns:
            Tuple of (local path, filename) if successful, None otherwise
        """

        if not url:
            logger.warning("Empty URL provided")
            return None
        file_id = api_client.extract_file_id_from_url(url)
        if not file_id:
            logger.warning(f"Could not extract file ID from URL: {url}")
            return None
            
        try:
            # Get file info for name
            file_info = api_client.get_file_info(file_id)
            if not file_info:
                return None
                
            filename = file_info.get('name')
            output_path = self._generate_image_path(url, filename)
            
            if api_client.download_file(file_id, output_path):
                self.downloaded_images[url] = output_path
                return output_path, filename
                
            return None
            
        except Exception as e:
            logger.error(f"API download failed for {url}: {str(e)}")
            return None

    
    def cleanup(self) -> None:
        """Clean up any temporary resources."""
        self.pending_images.clear()
        self.downloaded_images.clear()