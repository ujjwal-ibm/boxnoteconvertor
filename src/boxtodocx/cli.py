"""Command-line interface for Box document conversion."""
from typing import Optional
import click
from pathlib import Path

from .convertor import BoxNoteConverter
from .utils.logger import setup_logger
from .utils.constants import DEFAULT_OUTPUT_DIR

logger = setup_logger()

@click.argument(
    "input_path",
    type=click.Path(exists=True, path_type=Path)
)
@click.option(
    "--dest-dir", "-d",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    help="Destination directory for output files"
)
@click.option(
    "--export-images",
    is_flag=True,
    default=False,
    help="Export images from Box documents"
)
@click.option(
    "--box-id",
    help="Box login email"
)
@click.option(
    "--box-pwd",
    help="Box login password"
)
@click.option(
    "--link",
    help="Div ID for additional login step"
)
@click.option(
    "--id",
    help="User ID field for Box login"
)
@click.option(
    "--pwd",
    help="Password field for Box login"
)
@click.option(
    "--mfa-link",
    help="Div ID to click for MFA"
)
@click.option(
    "--mfa-otp-id",
    help="ID of input field for MFA code"
)
@click.option(
    "--mfa-btn-id",
    help="ID of button to submit MFA code"
)
@click.option(
    "--mfa-otp",
    help="MFA code (one-time password)"
)
@click.option(
    "--directory",
    is_flag=True,
    default=False,
    help="Process all Box documents in a directory"
)
@click.option(
    "--api-token",
    help="Box API token for direct download"
)
@click.option(
    "--generate-html",
    is_flag=True,
    default=False,
    help="Generate HTML and save images in separate folder"
)
@click.command(help="Convert Box documents to HTML and DOCX formats with image support.")
def main(
    input_path: Path,
    dest_dir: Path,
    export_images: bool,
    api_token: Optional[str],
    box_id: Optional[str],
    box_pwd: Optional[str],
    link: Optional[str],
    id: Optional[str],
    pwd: Optional[str],
    mfa_link: Optional[str],
    mfa_otp_id: Optional[str],
    mfa_btn_id: Optional[str],
    mfa_otp: Optional[str],
    directory: bool,
    generate_html: bool
) -> None:
    """
    Convert Box documents to HTML and DOCX formats.
    
    Args:
        input_path: Path to Box document or directory
    """
    try:
        credentials = None
        if export_images and not api_token:
            if not all([box_id, box_pwd, link, id, pwd]):
                raise click.UsageError(
                    "Either API token or all Box login parameters must be provided when exporting images"
                )
            credentials = {
                "user_id": box_id,
                "password": box_pwd,
                "link_id": link,
                "user_field_id": id,
                "password_field_id": pwd,
                "mfa_link": mfa_link,
                "mfa_otp_id": mfa_otp_id,
                "mfa_btn_id": mfa_btn_id,
                "mfa_otp": mfa_otp
            }
        
        converter = BoxNoteConverter(dest_dir)
        
        if directory:
            if not input_path.is_dir():
                raise click.BadParameter(f"Not a directory: {input_path}")
            results = converter.convert_directory(
                input_path,
                credentials=credentials,
                api_token=api_token,
                generate_html=generate_html,
                export_images=export_images
            )
            logger.info(f"Processed {len(results)} files in {input_path}")
            
        else:
            if not input_path.is_file():
                raise click.BadParameter(f"Not a file: {input_path}")
                
            if not BoxNoteConverter.validate_boxnote(input_path):
                raise click.BadParameter(f"Invalid Box document: {input_path}")
                
            html_path, docx_path, image_paths = converter.convert(
                input_path,
                credentials=credentials,
                api_token=api_token,
                generate_html=generate_html
            )
            logger.info(f"Converted {input_path} to:")
            logger.info(f"  HTML: {html_path}")
            logger.info(f"  DOCX: {docx_path}")
            if image_paths:
                logger.info(f"  Images: {len(image_paths)} files")
                
    except Exception as e:
        logger.error(str(e))
        raise click.Abort()

if __name__ == "__main__":
    main()