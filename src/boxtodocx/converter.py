import json
from pathlib import Path
from .handlers.html_handler import HTMLHandler
from .handlers.docx_handler import DOCXHandler
from .utils.logger import setup_logger

logger = setup_logger()

class BoxNoteConverter:
    def __init__(self):
        self.html_handler = HTMLHandler()
        self.docx_handler = DOCXHandler()

    def convert(self, filepath, dest_dir=None):
        input_path = Path(filepath)
        dest_dir = dest_dir or input_path.parent
        
        logger.info(f"Processing: {input_path}")
        
        with open(input_path, "r") as boxnote:
            data = json.load(boxnote)

        if 'doc' in data:
            base_path = Path(dest_dir) / input_path.stem
            html_path = f"{base_path}.html"
            docx_path = f"{base_path}.docx"
            
            html_content = self.html_handler.convert_to_html(data['doc']['content'], dest_dir)
            
            with open(html_path, "w") as f:
                f.write(html_content)
                
            self.docx_handler.convert_html_to_docx(html_content, docx_path)
            logger.info(f"Created: {html_path} and {docx_path}")