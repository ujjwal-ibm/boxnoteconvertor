import argparse
from pathlib import Path
from boxtodocx.handlers.html_handler import BoxNoteParser
from boxtodocx.handlers.docx_handler import HtmlToDocx
from boxtodocx.utils.logger import get_logger
import sys
import traceback
import uuid
from typing import Optional
from boxtodocx.utils.logger import get_logger, setup_logger

logger = get_logger(__name__)

class BoxNoteConverter:
    """Main converter class for BoxNote to docx conversion."""
    
    def __init__(self, workdir: Path, token: Optional[str] = None, user_id: Optional[str] = None):
        self.workdir = workdir
        self.token = token
        self.user_id = user_id
        self.temp_files = []

    def get_temp_html_path(self) -> Path:
        """Generate a unique temporary HTML file path."""
        temp_file = self.workdir / f'temp_{uuid.uuid4().hex}.html'
        self.temp_files.append(temp_file)
        return temp_file

    def cleanup_temp_files(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file}: {str(e)}")
        self.temp_files.clear()

    def convert_single_file(
        self,
        input_file: Path,
        output_docx: Optional[Path] = None
    ) -> None:
        """Convert a single boxnote file to docx."""
        temp_html = None
        try:
            # Create temp directory if it doesn't exist
            self.workdir.mkdir(parents=True, exist_ok=True)

            # Generate temporary HTML file path
            temp_html = self.get_temp_html_path()

            # Read and parse content
            logger.info(f"Reading input file: {input_file}")
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Clean filename and setup output path
            clean_name = input_file.stem.replace('.boxnote', '').replace('.docx', '')
            if output_docx is None:
                output_docx = input_file.parent / f'{clean_name}.docx'
            else:
                # Handle output path with potential .docx extension
                output_stem = output_docx.stem.replace('.docx', '')
                output_docx = output_docx.parent / f'{output_stem}.docx'

            # Parse BoxNote to HTML
            logger.info("Converting BoxNote to HTML")
            parser = BoxNoteParser()
            html_content = parser.parse(content, clean_name, self.workdir, self.token, self.user_id)

            # Write temporary HTML
            logger.info(f"Writing temporary HTML: {temp_html}")
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Convert HTML to docx
            logger.info(f"Converting to docx: {output_docx}")
            docx_parser = HtmlToDocx(self.workdir)
            docx_parser.table_style = 'TableGrid'

            try:
                docx_parser.parse_html_file(str(temp_html), str(output_docx.with_suffix('')))
                logger.info(f"Successfully created: {output_docx}")
            except Exception as e:
                logger.error(f"docx conversion failed: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            raise

        finally:
            # Clean up temporary files
            self.cleanup_temp_files()

    def convert_folder(self, input_path: Path) -> None:
        """Convert all boxnote files in a folder."""
        # Count files and track progress
        boxnote_files = list(input_path.glob('*.boxnote'))
        total_files = len(boxnote_files)
        successful = 0
        failed = 0

        logger.info(f"Found {total_files} BoxNote files in {input_path}")

        for boxnote_file in boxnote_files:
            try:
                logger.info(f"Processing: {boxnote_file.name}")
                output_docx = None  # Let convert_single_file handle the output path
                self.convert_single_file(boxnote_file, output_docx)
                successful += 1
                logger.info(f"Successfully converted: {boxnote_file.name}")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to convert {boxnote_file.name}: {str(e)}")
                continue

        # Print summary
        logger.info("\nConversion Summary:")
        logger.info(f"Total files: {total_files}")
        logger.info(f"Successfully converted: {successful}")
        logger.info(f"Failed: {failed}")



class DocxConverter:
    def __init__(self):
        self.temp_files = []

    def get_temp_html_path(self, workdir: Path) -> Path:
        """Generate a unique temporary HTML file path"""
        temp_file = workdir / f'temp_{uuid.uuid4().hex}.html'
        self.temp_files.append(temp_file)
        return temp_file

    def cleanup_temp_files(self):
        """Clean up all temporary files"""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file}: {str(e)}")
        self.temp_files.clear()

    def convert_single_file(
        self,
        token: str,
        workdir: Path,
        input_file: Path,
        output_docx: Optional[Path],
        user_id: str
    ) -> None:
        """Convert a single boxnote file to docx with enhanced error handling"""
        temp_html = None
        try:
            # Create temp directory if it doesn't exist
            workdir.mkdir(parents=True, exist_ok=True)

            # Generate temporary HTML file path
            temp_html = self.get_temp_html_path(workdir)

            # Read and parse content
            logger.info(f"Reading input file: {input_file}")
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Clean filename and setup output path
            clean_name = input_file.stem.replace('.boxnote', '').replace('.docx', '')
            if output_docx is None:
                output_docx = input_file.parent / f'{clean_name}.docx'
            else:
                # Handle output path with potential .docx extension
                output_stem = output_docx.stem.replace('.docx', '')
                output_docx = output_docx.parent / f'{output_stem}.docx'

            # Parse BoxNote to HTML
            from html_parser import parse
            logger.info("Converting BoxNote to HTML")
            html_content = parse(content, clean_name, workdir, token, user_id)

            # Write temporary HTML
            logger.info(f"Writing temporary HTML: {temp_html}")
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Convert HTML to docx
            logger.info(f"Converting to docx: {output_docx}")
            docx_parser = HtmlToDocx(workdir)
            docx_parser.table_style = 'TableGrid'

            try:
                docx_parser.parse_html_file(str(temp_html), str(output_docx.with_suffix('')))  # Remove .docx extension
                logger.info(f"Successfully created: {output_docx}")
            except Exception as e:
                logger.error(f"docx conversion failed: {str(e)}")
                logger.error(traceback.format_exc())
                raise

        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def convert_folder(
        self,
        token: str,
        workdir: Path,
        input_path: Path,
        user_id: str
    ) -> None:
        """Convert all boxnote files in a folder with comprehensive error handling"""
        # Count files and track progress
        boxnote_files = list(input_path.glob('*.boxnote'))
        total_files = len(boxnote_files)
        successful = 0
        failed = 0

        logger.info(f"Found {total_files} BoxNote files in {input_path}")

        for boxnote_file in boxnote_files:
            try:
                logger.info(f"Processing: {boxnote_file.name}")
                output_docx = None  # Let convert_single_file handle the output path
                self.convert_single_file(token, workdir, boxnote_file, output_docx, user_id)
                successful += 1
                logger.info(f"Successfully converted: {boxnote_file.name}")
            except Exception as e:
                failed += 1
                logger.error(f"Failed to convert {boxnote_file.name}: {str(e)}")
                continue

        # Print summary
        logger.info("\nConversion Summary:")
        logger.info(f"Total files: {total_files}")
        logger.info(f"Successfully converted: {successful}")
        logger.info(f"Failed: {failed}")

def main():
    parser = argparse.ArgumentParser(description='Convert BoxNote files to docx format')
    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-d', '--dir', help='Work directory for temporary files')
    parser.add_argument('-t', '--token', help='Box access token')
    parser.add_argument('-o', '--output', help='Output file name (only for single file conversion)')
    parser.add_argument('-u', '--user', help='Box user id')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        setup_logger(True)

    converter = DocxConverter()
    try:
        # Setup paths
        workdir = Path(args.dir) if args.dir else Path.cwd() / '.temp'
        input_path = Path(args.input)
        output_docx = Path(args.output) if args.output else None

        # Validate input path
        if not input_path.exists():
            logger.error(f"Input path does not exist: {input_path}")
            return 1

        # Process files
        if input_path.is_dir():
            converter.convert_folder(args.token, workdir, input_path, args.user)
        else:
            if not input_path.suffix == '.boxnote':
                logger.error(f"Input file must be a .boxnote file: {input_path}")
                return 1
            converter.convert_single_file(
                args.token, workdir, input_path, output_docx, args.user
            )

        return 0

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

    finally:
        # Clean up temporary files
        converter.cleanup_temp_files()

if __name__ == '__main__':
    sys.exit(main())