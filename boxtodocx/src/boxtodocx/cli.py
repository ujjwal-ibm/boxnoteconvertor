import sys
from pathlib import Path
from typing import Optional

import click

from boxnotetodocx.converter import BoxNoteConverter
from boxnotetodocx.utils.logger import setup_logger, get_logger

logger = get_logger(__name__)

@click.command()
@click.version_option()  # This will use __version__ from __init__.py
@click.argument('input_path', type=click.Path(exists=True))
@click.option('-d', '--dir', help='Work directory for temporary files')
@click.option('-t', '--token', help='Box access token')
@click.option('-o', '--output', help='Output file name (only for single file conversion)')
@click.option('-u', '--user', help='Box user id')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
def main(input_path: str, dir: Optional[str], token: Optional[str],
         output: Optional[str], user: Optional[str], verbose: bool) -> int:
    """
    Convert BoxNote files to DOCX format.
    
    INPUT_PATH can be a single .boxnote file or a directory containing multiple .boxnote files.
    """
    try:
        # Setup logging
        setup_logger(verbose)
        
        # Initialize converter
        workdir = Path(dir) if dir else Path.cwd() / '.temp'
        workdir.mkdir(parents=True, exist_ok=True)
        
        converter = BoxNoteConverter(
            workdir=workdir,
            token=token,
            user_id=user
        )
        
        input_path = Path(input_path)
        output_path = Path(output) if output else None
        
        # Process files
        if input_path.is_dir():
            logger.info(f"Processing directory: {input_path}")
            converter.convert_folder(input_path)
        else:
            if not input_path.suffix == '.boxnote':
                logger.error(f"Input file must be a .boxnote file: {input_path}")
                return 1
                
            logger.info(f"Processing file: {input_path}")
            converter.convert_single_file(input_path, output_path)
            
        return 0
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        if verbose:
            logger.exception("Detailed error information:")
        return 1

if __name__ == '__main__':
    sys.exit(main())