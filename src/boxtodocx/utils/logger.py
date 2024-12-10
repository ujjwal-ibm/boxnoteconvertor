"""Logging configuration"""
import logging
import sys
from typing import Optional
import colorlog

def setup_logger(
    name: str = "boxtodocx",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger instance with colored output.
    
    Args:
        name: Logger name (default: "boxtodocx")
        level: Logging level (default: logging.INFO)
        log_file: Optional file path for logging to file
        
    Returns:
        Configured logger instance
    """
    logger = colorlog.getLogger(name)
    
    if logger.handlers:  # Return existing logger if already configured
        return logger
        
    # Clear any existing handlers
    logger.handlers = []
    
    # Configure console handler with colored output
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(message)s%(reset)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white'
        }
    ))
    logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(file_handler)
    
    logger.setLevel(level)
    return logger