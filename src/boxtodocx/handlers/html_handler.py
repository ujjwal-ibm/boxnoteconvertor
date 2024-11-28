import json
from typing import Dict, List, Union, Optional, Any
from pathlib import Path
from boxtodocx.mappers import html_mapper
import re, json
from bs4 import BeautifulSoup
from boxtodocx.utils.logger import get_logger

logger = get_logger(__name__)

class BoxNoteParser:
    def __init__(self):
        self.token = None
        self.user = None
        self.workdir = None
        self.title = None
        self.content_stack = []
        self.list_stack = []

    def try_parse_json(self, content: str) -> Dict:
        """Try different approaches to parse the BoxNote content"""
        try:
            # First try: direct JSON parse
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # Second try: Clean the content and try again
                cleaned_content = re.sub(r'[\x00-\x1F\x7F]', '', content)
                return json.loads(cleaned_content)
            except json.JSONDecodeError:
                try:
                    # Third try: Try to find JSON content within the string
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
                except:
                    pass
                
                # If all attempts fail, try to parse as plain text
                return {
                    "doc": {
                        "content": {
                            "type": "paragraph",
                            "content": [{
                                "type": "text",
                                "text": content
                            }]
                        }
                    }
                }

    def validate_boxnote_structure(self, boxnote: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix BoxNote structure if needed"""
        if not isinstance(boxnote, dict):
            logger.warning("BoxNote content is not a dictionary, wrapping it")
            return {
                "doc": {
                    "content": boxnote
                }
            }

        if "doc" not in boxnote:
            logger.warning("No 'doc' field found, wrapping content")
            return {
                "doc": {
                    "content": boxnote
                }
            }

        if "content" not in boxnote.get("doc", {}):
            logger.warning("No 'content' field found in doc, creating empty content")
            boxnote["doc"]["content"] = {}

        return boxnote

    def parse(self, boxnote_content: Union[str, bytes, bytearray], title: str = None, 
             workdir: Path = None, access_token: str = None, user_id: str = None) -> str:
        try:
            self.token = access_token
            self.user = user_id
            self.workdir = workdir
            self.title = title

            # Convert bytes to string if needed
            if isinstance(boxnote_content, (bytes, bytearray)):
                boxnote_content = boxnote_content.decode('utf-8', errors='replace')

            # Parse the content
            boxnote = self.try_parse_json(boxnote_content)
            
            # Validate and fix structure
            boxnote = self.validate_boxnote_structure(boxnote)

            # Initialize HTML document
            contents = [
                '<!DOCTYPE html>',
                '<html>',
                '<head>',
                '<meta charset="UTF-8">',
                f'<title>{title}</title>',
                '</head>',
                '<body>'
            ]

            # Parse the content
            self.parse_content(boxnote['doc']['content'], contents)

            # Finalize HTML document
            contents.extend(['</body>', '</html>'])

            # Clean up empty paragraphs and normalize spacing
            result = ''.join(filter(None, contents))
            result = re.sub(r'<p style="text-align: left"></p>', '', result)
            result = re.sub(r'\s+', ' ', result)
            logger.debug("Complete generated HTML:")
            logger.debug(result)
            return result

        except Exception as e:
            logger.error(f"Error in main parsing: {str(e)}")
            logger.error(f"Stack trace:\n{traceback.format_exc()}")
            return self.create_error_html(str(e))

        
    def parse_content(self, content: Union[Dict, List], contents: List[str], 
                     ignore_paragraph: bool = False):
        """Parse BoxNote content with enhanced style handling"""
        if not content:
            return

        try:
            # Handle list content
            if isinstance(content, list):
                for item in content:
                    self.parse_content(item, contents, ignore_paragraph)
                return

            # Handle dictionary content
            if not isinstance(content, dict):
                return

            content_type = content.get('type', '')
            
            # Special handling for text to preserve formatting
            if content_type == 'text':
                text_content = content.get('text', '')
                # Skip if it looks like a style tag
                if not text_content.strip().startswith('<style'):
                    marks = content.get('marks', [])
                    contents.append(html_mapper.handle_text_marks(marks, text_content))
            
            # Handle other content types...
            elif content_type == 'paragraph' and not ignore_paragraph:
                alignment = 'left'
                for mark in content.get('marks', []):
                    if mark.get('type') == 'alignment':
                        alignment = mark.get('attrs', {}).get('alignment', 'left')
                contents.append(html_mapper.get_tag_open('paragraph', alignment=alignment))
                self.parse_content(content.get('content', []), contents)
                contents.append(html_mapper.get_tag_close('paragraph'))
                
            elif content_type in ['list_item', 'check_list_item']:
                args = {}
                if content_type == 'check_list_item':
                    checked = content.get('attrs', {}).get('checked', False)
                    args = {'checked': 'checked' if checked else '', 'x': 'X' if checked else '  '}
                contents.append(html_mapper.get_tag_open(content_type, **args))
                self.parse_content(content.get('content', []), contents, True)
                contents.append(html_mapper.get_tag_close(content_type))
            elif content_type == 'image':
                contents.append(html_mapper.handle_image(
                    content.get('attrs', {}),
                    self.title,
                    self.workdir,
                    self.token,
                    self.user
                ))
            elif content_type == 'table':
                # Append table with proper styling
                contents.append('\n<table border="1" style="border-collapse: collapse; width: 100%;">\n')
                
                # Process each row
                for row in content.get('content', []):
                    if row['type'] != 'table_row':
                        continue
                        
                    contents.append('  <tr>\n')
                    
                    # Process each cell
                    for cell in row.get('content', []):
                        if cell['type'] != 'table_cell':
                            continue
                            
                        attrs = cell.get('attrs', {})
                        colspan = attrs.get('colspan', 1)
                        rowspan = attrs.get('rowspan', 1)
                        
                        # Build cell attributes
                        cell_attrs = []
                        if colspan > 1:
                            cell_attrs.append(f'colspan="{colspan}"')
                        if rowspan > 1:
                            cell_attrs.append(f'rowspan="{rowspan}"')
                        
                        # Add cell with styling
                        contents.append(f'    <td {" ".join(cell_attrs)} style="border: 1px solid black; padding: 8px;">')
                        
                        # Process cell content
                        cell_content = cell.get('content', [])
                        if cell_content:
                            self.parse_content(cell_content, contents)
                        
                        contents.append('</td>\n')
                        
                    contents.append('  </tr>\n')
                contents.append('</table>\n\n')
                logger.debug(f"Generated table content: {''.join(contents[-50:])}")
            else:
                # Handle other content types
                if content_type in html_mapper.tag_open_map:
                    contents.append(html_mapper.get_tag_open(
                        content_type,
                        **content.get('attrs', {})
                    ))
                    self.parse_content(content.get('content', []), contents)
                    contents.append(html_mapper.get_tag_close(content_type))

        except Exception as e:
            logger.warning(f"Error parsing content type '{content_type}': {str(e)}")
            # Continue processing other content

    def create_error_html(self, error_message: str) -> str:
        """Create basic HTML for error cases"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
        <p>Error converting BoxNote: {error_message}</p>
        </body>
        </html>
        """

def parse(*args, **kwargs):
    """Convenience function to parse BoxNote content"""
    parser = BoxNoteParser()
    return parser.parse(*args, **kwargs)