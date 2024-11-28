from typing import Dict, List
from pathlib import Path
import re
import requests
import base64
from urllib.parse import unquote
from boxtodocx.utils.logger import get_logger

logger = get_logger(__name__)

# Enhanced base style with more formatting options
base_style = '''<style type="text/css">
table {
    min-width: 500px;
    border-collapse: collapse;
    margin: 1em 0;
    font-family: Arial, sans-serif;
}
table, th, td {
    border: 1px solid #ddd;
}
table th, table td {
    padding: 8px;
    text-align: left;
    vertical-align: top;
}
table th {
    background-color: #f5f5f5;
    font-weight: bold;
}
table tr:nth-child(odd) {
    background-color: #fafafa;
}
table tr:nth-child(even) {
    background-color: #ffffff;
}
table tr:hover {
    background-color: #f0f7ff;
}
blockquote {
    display: block;
    border-left: 4px solid #ddd;
    margin: 1em 0;
    padding: 0.5em 0.8em;
    background-color: #f9f9f9;
    color: #666;
}
pre {
    background: #f6f8fa;
    border: 1px solid #ddd;
    border-left: 3px solid #2188ff;
    color: #24292e;
    page-break-inside: avoid;
    font-family: 'Courier New', Courier, monospace;
    line-height: 1.6;
    margin: 1em 0;
    max-width: 100%;
    overflow: auto;
    padding: 1em;
    display: block;
    word-wrap: break-word;
}
code {
    background-color: rgba(27,31,35,.05);
    border-radius: 3px;
    font-family: 'Courier New', Courier, monospace;
    font-size: 85%;
    margin: 0;
    padding: 0.2em 0.4em;
}
.call-out-box {
    margin: 1em 0;
    padding: 1em;
    border-radius: 4px;
    border-left: 4px solid;
}
.check-list {
    list-style: none;
    padding-left: 1.2em;
}
.check-list-item {
    margin: 0.5em 0;
    display: flex;
    align-items: center;
}
.check-list-item input[type="checkbox"] {
    margin-right: 0.5em;
}
img {
    max-width: 100%;
    height: auto;
    margin: 1em 0;
}
h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    line-height: 1.2;
}
a {
    color: #0366d6;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
</style>'''

# Enhanced tag mappings with more formatting options
tag_open_map = {
    'paragraph': '<p style="text-align: {alignment}; margin-bottom: 1em; line-height: 1.6;">',
    'strong': '<strong>',
    'em': '<em>',
    'underline': '<u>',
    'strikethrough': '<s>',
    'ordered_list': '<ol style="margin: 1em 0; padding-left: 2em;">',
    'blockquote': '<blockquote>',
    'bullet_list': '<ul style="margin: 1em 0; padding-left: 2em;">',
    'list_item': '<li style="margin: 0.5em 0;">',
    'check_list': '<ul class="check-list">',
    'check_list_item': '<li class="check-list-item"><input type="checkbox" {checked} disabled><span>[{x}]</span>',
    'horizontal_rule': '<hr style="border: none; border-top: 1px solid #ddd; margin: 2em 0;">',
    'table': '<table>',
    'table_row': '<tr>',
    'table_cell': '''<td colspan="{colspan}" rowspan="{rowspan}" 
                     style="width: {colwidth}px; text-align: {alignment}; 
                     background-color: {bgcolor}; color: {color};">''',
    'table_header': '<th style="text-align: {alignment};">',
    'image': '''<img src="{src}" alt="{alt}" title="{title}" 
               style="max-width: 100%; height: auto; display: block; margin: 1em auto;">''',
    'highlight': '<span style="background-color: {color};">',
    'heading': '<h{level} style="color: {color};">',
    'font_size': '<span style="font-size: {size}px;">',
    'font_color': '<span style="color: {color};">',
    'link': '<a href="{href}" title="{title}" target="{target}">',
    'code_block': '<pre><code class="language-{language}">',
    'call_out_box': '''<div class="call-out-box" style="background-color: {backgroundColor}; 
                    border-left-color: {borderColor};"><p>{emoji}'''
}

# Corresponding closing tags
tag_close_map = {
    'paragraph': '</p>',
    'strong': '</strong>',
    'em': '</em>',
    'underline': '</u>',
    'strikethrough': '</s>',
    'ordered_list': '</ol>',
    'blockquote': '</blockquote>',
    'bullet_list': '</ul>',
    'list_item': '</li>',
    'check_list': '</ul>',
    'check_list_item': '</li>',
    'table': '</table>',
    'table_row': '</tr>',
    'table_cell': '</td>',
    'table_header': '</th>',
    'image': '',
    'highlight': '</span>',
    'heading': '</h{level}>',
    'font_size': '</span>',
    'font_color': '</span>',
    'link': '</a>',
    'horizontal_rule': '',
    'code_block': '</code></pre>',
    'call_out_box': '</p></div>'
}

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and invalid characters"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def get_safe_color(color: str) -> str:
    """Validate and sanitize color values"""
    if not color:
        return 'inherit'
    if re.match(r'^#[0-9A-Fa-f]{6}$', color):
        return color
    if re.match(r'^rgb\(\d{1,3},\s*\d{1,3},\s*\d{1,3}\)$', color):
        return color
    return 'inherit'

def get_safe_size(size: str) -> str:
    """Validate and sanitize size values"""
    try:
        size_val = float(size)
        if 8 <= size_val <= 72:  # Reasonable font size range
            return str(size_val)
    except (ValueError, TypeError):
        pass
    return '12'

def get_tag_open(tag: str, **kwargs) -> str:
    """Enhanced tag opening with proper attribute handling and fallbacks"""
    if tag not in tag_open_map:
        return ''
        
    # Handle common attributes with defaults
    defaults = {
        'alignment': 'left',
        'colspan': '1',
        'rowspan': '1',
        'colwidth': '100',
        'bgcolor': 'inherit',
        'color': 'inherit',
        'alt': '',
        'title': '',
        'target': '_blank',
        'language': 'text',
        'borderColor': '#ddd'
    }
    
    # Update kwargs with defaults for missing values
    for key, value in defaults.items():
        if key not in kwargs:
            kwargs[key] = value
            
    # Sanitize values
    if 'color' in kwargs:
        kwargs['color'] = get_safe_color(kwargs['color'])
    if 'size' in kwargs:
        kwargs['size'] = get_safe_size(kwargs['size'])
    if 'src' in kwargs:
        kwargs['src'] = sanitize_filename(kwargs['src'])
    
    try:
        return tag_open_map[tag].format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing attribute for tag {tag}: {e}")
        return tag_open_map[tag].format(**defaults)
    except Exception as e:
        logger.error(f"Error formatting tag {tag}: {e}")
        return ''

def get_tag_close(tag: str, **kwargs) -> str:
    """Get closing tag with proper formatting"""
    return tag_close_map.get(tag, '').format(**kwargs) if tag in tag_close_map else ''

def handle_text_marks(marks: List[Dict], text: str) -> str:
    """Enhanced text mark handling with proper escaping and validation"""
    if not text:
        return ''
        
    # Escape HTML special characters
    text = (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    # Process marks in order
    try:
        tag_starts = []
        tag_ends = []
        
        for mark in marks:
            mark_type = mark.get('type', '')
            if mark_type in tag_open_map:
                attrs = mark.get('attrs', {})
                tag_starts.append(get_tag_open(mark_type, **attrs))
                tag_ends.insert(0, get_tag_close(mark_type, **attrs))
                
        return ''.join(tag_starts) + text + ''.join(tag_ends)
    except Exception as e:
        logger.error(f"Error processing text marks: {e}")
        return text

def handle_image(attrs: Dict[str, str], title: str, workdir: Path, token: str = None, user: str = None) -> str:
    """Enhanced image handling with better error handling and fallbacks"""
    try:
        if not workdir:
            logger.error("Working directory not specified")
            return ''
            
        image_attrs = {
            'src': '',
            'alt': attrs.get('fileName', 'image'),
            'title': attrs.get('fileName', ''),
        }

        if token and attrs.get('boxFileId'):
            # Handle Box-hosted images
            downloaded_path = download_image(
                attrs['boxFileId'],
                attrs['fileName'],
                workdir,
                token,
                user
            )
            if downloaded_path:
                image_attrs['src'] = str(downloaded_path)
        else:
            # Handle local images
            file_name = attrs.get('fileName')
            if file_name:
                image_path = find_local_image(file_name, title, workdir)
                if image_path:
                    image_attrs['src'] = str(image_path)

        if not image_attrs['src']:
            logger.warning(f"Could not resolve image: {attrs.get('fileName', 'unknown')}")
            return ''

        return get_tag_open('image', **image_attrs)
    except Exception as e:
        logger.error(f"Error handling image: {e}")
        return ''

def find_local_image(file_name: str, title: str, workdir: Path) -> Path:
    """Find local image with support for various file patterns"""
    try:
        file_stem = Path(file_name).stem
        file_ext = Path(file_name).suffix
        image_dir = workdir / Path(f'Box Notes Images/{title} Images/')
        
        # Support various file patterns
        patterns = [
            f'{file_stem}{file_ext}',                    # exact match
            f'{file_stem} (*){file_ext}',                # version number
            f'{file_stem.lower()}{file_ext.lower()}',    # case insensitive
            f'{file_stem.lower()} (*){file_ext.lower()}' # case insensitive with version
        ]
        
        for pattern in patterns:
            matches = list(image_dir.glob(pattern))
            if matches:
                return Path(*matches[0].parts[1:])
                
        logger.warning(f"Image not found: {file_name}")
        return None
    except Exception as e:
        logger.error(f"Error finding local image: {e}")
        return None

def download_image(box_file_id: str, file_name: str, workdir: Path, token: str, user: str) -> Path:
    """Enhanced image download with retries and better error handling"""
    try:
        if not token.startswith("Bearer "):
            token = "Bearer " + token
            
        headers = {
            'Authorization': token,
            'As-User': user if user else '',
            'Accept': 'application/octet-stream'
        }
        
        url = f'https://api.box.com/2.0/files/{box_file_id}/content'
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                if response.status_code == 200:
                    safe_filename = sanitize_filename(f'{box_file_id}_{file_name}')
                    file_path = workdir / safe_filename
                    
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.debug(f'Successfully downloaded image: {file_name}')
                    return file_path
                    
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f'Failed to download image {file_name} after {max_retries} attempts: {str(e)}')
                    return None
                logger.warning(f'Retry {attempt + 1}/{max_retries} for image {file_name}')
                continue
                
        return None
    except Exception as e:
        logger.error(f'Error downloading image {file_name}: {str(e)}')
        return None