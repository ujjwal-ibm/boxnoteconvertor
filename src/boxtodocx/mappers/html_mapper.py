"""HTML mapping utilities for converting Box document structures to HTML."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import html
from ..utils.logger import setup_logger
from dataclasses import dataclass, field
logger = setup_logger(__name__)

@dataclass
class BoxElement:
    """Represents a Box document element with its attributes."""
    type: str
    attrs: Dict[str, Any] = field(default_factory=dict)
    content: Optional[List[Any]] = None
    marks: Optional[List[Dict[str, Any]]] = None
    text: Optional[str] = None

class HTMLMapper:
    """Maps Box document elements to HTML."""
    
    def __init__(self) -> None:
        self.image_paths: Dict[str, Path] = {}
    
    def map_content(self, content: List[Dict[str, Any]]) -> str:
        """
        Convert Box content to HTML string.
        
        Args:
            content: List of Box content elements
            
        Returns:
            HTML string representation
        """
        try:
            elements = [self._create_element(item) for item in content]
            html_parts = ['<!DOCTYPE html>', '<html>', '<body>']
            
            for element in elements:
                html_parts.append(self._map_element(element))
                
            html_parts.extend(['</body>', '</html>'])
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error mapping content to HTML: {str(e)}")
            raise
    
    def _create_element(self, data: Dict[str, Any]) -> BoxElement:
        """Create BoxElement from dictionary data."""
        return BoxElement(
            type=data.get('type', ''),
            attrs=data.get('attrs', {}),
            content=data.get('content'),
            marks=data.get('marks'),
            text=data.get('text')
        )
    
    def _map_element(self, element: BoxElement) -> str:
        """Map a single BoxElement to HTML string."""
        if not element.type:
            return ''
            
        mapped = self._element_handlers.get(element.type)
        if mapped:
            return mapped(self, element)
            
        logger.warning(f"Unsupported element type: {element.type}")
        return ''
    
    def _map_text(self, element: BoxElement) -> str:
        """Map text element with marks to HTML."""
        if not element.text:
            return ''
            
        text = html.escape(element.text)
        if not element.marks:
            return text
            
        # Sort marks to ensure consistent application
        sorted_marks = sorted(element.marks, key=lambda x: {
            'color': 1,
            'bold': 2,
            'italic': 3,
            'underline': 4,
            'link': 5
        }.get(x.get('type', ''), 99))
        
        # Apply marks in order
        for mark in sorted_marks:
            text = self._apply_mark(text, mark)
            
        return text
    
    def _apply_mark(self, text: str, mark: Dict[str, Any]) -> str:
        """Apply a mark to text content."""
        mark_type = mark.get('type', '')
        attrs = mark.get('attrs', {})
        
        # Handle font color
        if mark_type == 'font_color' and 'color' in attrs:
            return f'<span style="color: {attrs["color"]}">{text}</span>'
        
        # Handle text color (alternative attribute)
        if mark_type == 'text_color' and 'color' in attrs:
            return f'<span style="color: {attrs["color"]}">{text}</span>'
        
        # Standard marks
        mark_handlers = {
            'bold': lambda t: f'<strong>{t}</strong>',
            'italic': lambda t: f'<em>{t}</em>',
            'underline': lambda t: f'<u>{t}</u>',
            'strike': lambda t: f'<s>{t}</s>',
            'link': lambda t: self._create_link(t, attrs.get('href', '#')),
            'highlight': lambda t: f'<mark>{t}</mark>'
        }
        
        handler = mark_handlers.get(mark_type)
        return handler(text) if handler else text
    
    def _create_link(self, text: str, href: str) -> str:
        """Create HTML link with proper escaping."""
        return f'<a href="{html.escape(href)}">{text}</a>'
    
    def _map_paragraph(self, element: BoxElement) -> str:
        """Map paragraph element to HTML."""
        style = self._get_style_attr(element.attrs)
        content = self._map_content_list(element.content) if element.content else ''
        return f'<p{style}>{content}</p>'
    
    def _map_heading(self, element: BoxElement) -> str:
        """Map heading element to HTML."""
        level = min(int(element.attrs.get('level', 1)), 6)
        content = self._map_content_list(element.content) if element.content else ''
        return f'<h{level}>{content}</h{level}>'
    
    def _map_list(self, element: BoxElement, ordered: bool = False) -> str:
        """Map list element to HTML."""
        tag = 'ol' if ordered else 'ul'
        content = self._map_content_list(element.content) if element.content else ''
        return f'<{tag}>{content}</{tag}>'
    
    def _map_list_item(self, element: BoxElement) -> str:
        """Map list item to HTML."""
        content = self._map_content_list(element.content) if element.content else ''
        return f'<li>{content}</li>'
    
    def _map_table(self, element: BoxElement) -> str:
        """Map table element to HTML."""
        content = self._map_content_list(element.content) if element.content else ''
        return f'<table border="1" cellspacing="0">{content}</table>'
    
    def _map_table_row(self, element: BoxElement) -> str:
        """Map table row to HTML."""
        content = self._map_content_list(element.content) if element.content else ''
        return f'<tr>{content}</tr>'
    
    def _map_table_cell(self, element: BoxElement) -> str:
        """Map table cell to HTML."""
        attrs = []
        if colspan := element.attrs.get('colspan'):
            attrs.append(f'colspan="{colspan}"')
        if rowspan := element.attrs.get('rowspan'):
            attrs.append(f'rowspan="{rowspan}"')
            
        attrs_str = f' {" ".join(attrs)}' if attrs else ''
        content = self._map_content_list(element.content) if element.content else ''
        return f'<td{attrs_str}>{content}</td>'
    
    def _map_image(self, element: BoxElement) -> str:
        """
        Map image element to HTML.
        
        Args:
            element: BoxElement containing image attributes
            
        Returns:
            HTML img tag string
        """
        # Get original source URL from various possible attributes
        src = (element.attrs.get('src') or 
            element.attrs.get('boxSharedLink') or 
            element.attrs.get('url'))
            
        if not src:
            logger.warning("Image element found without source")
            return ''
        
        # Get the mapped local path for this image
        if mapped_path := self.image_paths.get(src):
            # Create relative path to images directory
            rel_path = f"images/{mapped_path.name}"
            
            # Get additional attributes
            alt = html.escape(element.attrs.get('alt', ''))
            title = html.escape(element.attrs.get('title', ''))
            
            logger.debug(f"Creating img tag with src={rel_path}")
            return f'<img src="{rel_path}" alt="{alt}" title="{title}" />'
        else:
            logger.warning(f"No local file mapping found for image: {src}")
            logger.debug(f"Available mappings: {list(self.image_paths.keys())}")
            return ''

    
    def _map_content_list(self, content: Optional[List[Any]]) -> str:
        """Map a list of content elements to HTML."""
        if not content:
            return ''
            
        return ''.join(
            self._map_element(self._create_element(item))
            for item in content
        )
    
    def _get_style_attr(self, attrs: Dict[str, Any]) -> str:
        """Convert style attributes to HTML style string."""
        styles = []
        
        if 'align' in attrs:
            styles.append(f"text-align:{attrs['align']}")
        if 'indent' in attrs:
            styles.append(f"margin-left:{attrs['indent']}em")
            
        return f' style="{";".join(styles)}"' if styles else ''
    
    _element_handlers = {
        'text': _map_text,
        'paragraph': _map_paragraph,
        'heading': _map_heading,
        'bullet_list': lambda self, e: self._map_list(e, False),
        'ordered_list': lambda self, e: self._map_list(e, True),
        'list_item': _map_list_item,
        'table': _map_table,
        'table_row': _map_table_row,
        'table_cell': _map_table_cell,
        'image': _map_image,
        'hard_break': lambda self, e: '<br>',
        'blockquote': lambda self, e: f'<blockquote>{self._map_content_list(e.content)}</blockquote>'
    }