from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

class DOCXHandler:
    def __init__(self):
        self.document = Document()

    def convert_html_to_docx(self, html_content, output_path):
        soup = BeautifulSoup(html_content, 'html.parser')
        self._process_elements(soup.body)
        self.document.save(output_path)

    def _process_elements(self, parent):
        for element in parent.children:
            if element.name == 'p':
                self._handle_paragraph(element)
            elif element.name == 'table':
                self._handle_table(element)
            elif element.name == 'ul':
                self._handle_list(element, numbered=False)
            elif element.name == 'ol':
                self._handle_list(element, numbered=True)
            elif element.name == 'img':
                self._handle_image(element)
            elif element.name == 'h1':
                self._handle_heading(element)
            elif element.name == 'blockquote':
                self._handle_blockquote(element)

    def _handle_paragraph(self, element):
        p = self.document.add_paragraph()
        self._apply_styles(element, p)
        
        for child in element.children:
            if child.name in ['strong', 'b']:
                p.add_run(child.text).bold = True
            elif child.name in ['em', 'i']:
                p.add_run(child.text).italic = True
            elif child.name == 'a':
                p.add_run(child.text).underline = True
            else:
                p.add_run(child.text)

    def _handle_table(self, element):
        rows = element.find_all('tr')
        if not rows:
            return
            
        table = self.document.add_table(rows=len(rows), cols=len(rows[0].find_all(['td', 'th'])))
        table.style = 'Table Grid'

        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            for j, cell in enumerate(cells):
                table_cell = table.cell(i, j)
                if cell.get('colspan'):
                    table_cell.merge(table.cell(i, j + int(cell['colspan']) - 1))
                if cell.get('rowspan'):
                    table_cell.merge(table.cell(i + int(cell['rowspan']) - 1, j))
                table_cell.text = cell.text.strip()

    def _handle_list(self, element, numbered=False):
        for item in element.find_all('li', recursive=False):
            p = self.document.add_paragraph(style='List Number' if numbered else 'List Bullet')
            p.add_run(item.text)

    def _handle_image(self, element):
        src = element.get('src')
        if src and os.path.exists(src):
            self.document.add_picture(src, width=Inches(6))

    def _handle_heading(self, element):
        self.document.add_heading(element.text, level=1)

    def _handle_blockquote(self, element):
        p = self.document.add_paragraph()
        p.style = 'Quote'
        p.add_run(element.text)

    def _apply_styles(self, element, paragraph):
        if 'style' in element.attrs:
            styles = element['style'].split(';')
            for style in styles:
                if ':' not in style:
                    continue
                prop, value = style.split(':')
                prop = prop.strip()
                value = value.strip()
                
                if prop == 'text-align':
                    alignments = {
                        'left': WD_ALIGN_PARAGRAPH.LEFT,
                        'center': WD_ALIGN_PARAGRAPH.CENTER,
                        'right': WD_ALIGN_PARAGRAPH.RIGHT
                    }
                    paragraph.alignment = alignments.get(value, WD_ALIGN_PARAGRAPH.LEFT)