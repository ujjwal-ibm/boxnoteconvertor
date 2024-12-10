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
        self.html_handler = HTMLHandler(str(self.output_dir))
        self.docx_handler = DOCXHandler()
    
    def convert(
        self,
        filepath: Union[str, Path],
        credentials: Optional[Dict[str, str]] = None
    ) -> Tuple[Path, Path, List[Path]]:
        """
        Convert a single Box document to HTML and DOCX.
        
        Args:
            filepath: Path to Box document
            credentials: Optional Box credentials for image download
            
        Returns:
            Tuple of (HTML path, DOCX path, list of image paths)
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If file format is invalid
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Input file not found: {filepath}")
        
        try:
            logger.info(f"Converting {filepath}")
            
            # Convert to HTML first
            html_path, image_paths = self.html_handler.convert_file(
                str(filepath),
                credentials
            )
            
            # Convert HTML to DOCX
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            docx_path = self.output_dir / filepath.with_suffix('.docx').name
            self.docx_handler.convert_html_to_docx(html_content, docx_path)
            
            logger.info(f"Conversion completed: {filepath}")
            return html_path, docx_path, image_paths
            
        except Exception as e:
            logger.error(f"Conversion failed for {filepath}: {str(e)}")
            raise
    
    def convert_directory(
        self,
        directory: Union[str, Path],
        credentials: Optional[Dict[str, str]] = None
    ) -> List[Tuple[Path, Path, List[Path]]]:
        """
        Convert all Box documents in a directory.
        
        Args:
            directory: Directory containing Box documents
            credentials: Optional Box credentials for image download
            
        Returns:
            List of (HTML path, DOCX path, image paths) tuples
            
        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
            
        results = []
        for filepath in directory.glob('*.boxnote'):
            try:
                result = self.convert(filepath, credentials)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to convert {filepath}: {str(e)}")
                continue
                
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