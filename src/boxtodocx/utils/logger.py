import logging
import sys
from typing import Optional
import colorlog

def setup_logger(verbose: bool = False) -> None:
    """Configure application logging with color support."""
    # Create color formatter
    formatter = colorlog.ColoredFormatter(
        "%(asctime)s - %(log_color)s%(levelname)s%(reset)s - %(name)s - %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    # Get the root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Set log levels
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    root_logger.addHandler(handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with the given name."""
    logger = logging.getLogger(name or __name__)
    return logger