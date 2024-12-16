"""Core converter for Box documents to HTML and DOCX formats."""
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json

from .handlers.html_handler import HTMLHandler
from .handlers.docx_handler import DOCXHandler
from .utils.logger import setup_logger
from .utils.constants import DEFAULT_OUTPUT_DIR

logger = setup_logger(__name__)

class BoxNoteConverter:
    """Converts Box documents to HTML and DOCX formats."""
    
    def __init__(self, output_dir: Union[str, Path] = DEFAULT_OUTPUT_DIR) -> None:
        """
        Initialize converter with output directory.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_output_dir = Path(output_dir)
        self.html_handler = None  # Initialize only when needed
        self.docx_handler = DOCXHandler()
        self.browser_initialized = False
    
    def convert(
        self,
        filepath: Union[str, Path],
        credentials: Optional[Dict[str, str]] = None,
        api_token: Optional[str] = None,
        generate_html: bool = True,
        html_handler: Optional[HTMLHandler] = None,
        reuse_browser: bool = False
    ) -> Tuple[Path, Path, List[Path]]:
        """Convert a Box document to HTML and DOCX."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Input file not found: {filepath}")
        
        temp_dir = None
        local_html_handler = None
        
        try:
            # Set up all paths
            docx_path, assets_dir, html_path = self._setup_paths(filepath, generate_html)
            if not generate_html:
                temp_dir = assets_dir
                
            # Use existing handler or create new one
            if html_handler and reuse_browser:
                # Update output directory for existing handler
                html_handler.output_dir = assets_dir
                handler = html_handler
            else:
                # Create new handler
                handler = HTMLHandler(str(assets_dir))
                if api_token:
                    handler.set_api_token(api_token)
                local_html_handler = handler
                
            # Ensure image directory is within the assets directory
            handler.image_manager.output_dir = assets_dir / "images"
            
            # Process file
            try:
                with open(str(filepath), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                html_content, image_paths = handler.convert_to_html(
                    data['doc']['content'],
                    credentials,
                    api_token
                )
                
                # Write HTML file
                with open(str(html_path), 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Convert to DOCX
                docx_handler = DOCXHandler()
                docx_handler.convert_html_to_docx(
                    html_content,
                    str(docx_path),
                    str(assets_dir)
                )
                
                return html_path, docx_path, image_paths
                
            finally:
                # Only cleanup if we created a new handler and aren't reusing
                if local_html_handler and not reuse_browser:
                    local_html_handler.cleanup()
                    
        except Exception as e:
            logger.error(f"Conversion failed for {filepath}: {str(e)}")
            raise

    def _setup_output_dirs(self, input_path: Path) -> Tuple[Path, Path, Path]:
        """
        Set up output directories for a given input file.
        
        Args:
            input_path: Path to input file
            
        Returns:
            Tuple of (docx_path, html_dir, html_path)
        """
        # DOCX goes next to the input file
        docx_path = input_path.with_suffix('.docx')
        
        # Create a folder with the same name as the boxnote for HTML and images
        html_dir = input_path.parent / input_path.stem
        html_dir.mkdir(parents=True, exist_ok=True)
        
        # HTML file path inside the folder
        html_path = html_dir / input_path.with_suffix('.html').name
        
        logger.debug(f"Set up paths - DOCX: {docx_path}, HTML Dir: {html_dir}, HTML: {html_path}")
        return docx_path, html_dir, html_path
    
    def _setup_paths(self, input_path: Path, generate_html: bool = True) -> Tuple[Path, Path, Path]:
        """
        Set up all output paths for a given input file.
        
        Args:
            input_path: Path to Box note file
            generate_html: If True, create permanent HTML/images, else use temp directory

        Returns:
            Tuple of (docx_path, assets_dir, html_path)
        """
        import tempfile
        # DOCX goes next to the original file
        docx_path = input_path.with_suffix('.docx')
        
        if generate_html:
            # Create permanent directory structure
            assets_dir = input_path.parent / input_path.stem
            assets_dir.mkdir(parents=True, exist_ok=True)
            html_path = assets_dir / input_path.with_suffix('.html').name
            
            # Create images folder
            (assets_dir / 'images').mkdir(parents=True, exist_ok=True)
        else:
            # Create temporary directory that will be automatically cleaned up
            temp_dir = tempfile.mkdtemp(prefix='boxnote_')
            assets_dir = Path(temp_dir)
            html_path = assets_dir / input_path.with_suffix('.html').name
            
            # Create images folder in temp directory
            (assets_dir / 'images').mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Processing {input_path.name}:")
        logger.info(f"- DOCX will be created at: {docx_path}")
        logger.info(f"- Assets directory: {assets_dir}")
        
        return docx_path, assets_dir, html_path

    def convert_directory(
        self,
        directory: Union[str, Path],
        credentials: Optional[Dict[str, str]] = None,
        api_token: Optional[str] = None,
        generate_html: bool = True,
        export_images: bool = False
    ) -> List[Tuple[Path, Path, List[Path]]]:
        """Convert all Box documents in a directory recursively."""
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        results = []
        boxnotes = list(directory.rglob('*.boxnote'))
        
        if not boxnotes:
            logger.warning(f"No .boxnote files found in {directory}")
            return results
            
        logger.info(f"Found {len(boxnotes)} .boxnote files in {directory}")
        
        shared_html_handler = None
        try:
            # Initialize HTML handler only once if needed
            if export_images and (credentials or api_token):
                shared_html_handler = HTMLHandler(str(directory))
                if api_token:
                    shared_html_handler.set_api_token(api_token)
                logger.info("Initialized HTML handler with browser for image processing")

            for filepath in boxnotes:
                try:
                    result = self.convert(
                        filepath, 
                        credentials=credentials, 
                        api_token=api_token,
                        generate_html=generate_html,
                        html_handler=shared_html_handler,  # Pass the shared handler
                        reuse_browser=True  # Indicate we're reusing the browser
                    )
                    results.append(result)
                    logger.info(f"Successfully converted: {filepath.name}")
                except Exception as e:
                    logger.error(f"Failed to convert {filepath.name}: {str(e)}")
                    continue
                    
        finally:
            # Only cleanup if we created the handler
            if shared_html_handler:
                shared_html_handler.cleanup()
                logger.info("Cleaned up browser session")
        
        return results
    @staticmethod
    def validate_boxnote(filepath: Union[str, Path]) -> bool:
        """
        Validate Box document format.
        
        Args:
            filepath: Path to Box document
            
        Returns:
            True if valid, False otherwise
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                return False
                
            if 'doc' not in data or not isinstance(data['doc'], dict):
                return False
                
            if 'content' not in data['doc'] or not isinstance(data['doc']['content'], list):
                return False
                
            return True
            
        except (json.JSONDecodeError, OSError):
            return False