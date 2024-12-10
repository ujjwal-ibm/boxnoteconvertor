import click
import os
from pathlib import Path
from .converter import BoxNoteConverter
from .utils.logger import get_logger

logger = get_logger(__name__)

@click.command()
@click.version_option()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('-d', '--dir', help='Work directory for temporary files')
@click.option('-t', '--token', help='Box access token')
@click.option('-o', '--output', help='Output file name')
@click.option('-u', '--user', help='Box user id')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
def main(input_path, dir, token, output, user, verbose):
    try:
        converter = BoxNoteConverter()
        input_path = Path(input_path)
        
        if input_path.is_file():
            _convert_file(converter, input_path, output or dir)
        else:
            _convert_directory(converter, input_path)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise click.Abort()

def _convert_file(converter, file_path, output_dir=None):
    output_dir = output_dir or file_path.parent
    converter.convert(str(file_path), str(output_dir))

def _convert_directory(converter, dir_path):
    for file in dir_path.glob('**/*.boxnote'):
        _convert_file(converter, file)
