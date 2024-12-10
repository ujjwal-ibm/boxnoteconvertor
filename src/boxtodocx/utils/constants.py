"""Constants and configuration values."""
from typing import Dict, List, Final
from pathlib import Path

# File paths and directories
DEFAULT_OUTPUT_DIR: Final[Path] = Path("output")
DEFAULT_IMAGE_DIR: Final[Path] = DEFAULT_OUTPUT_DIR / "images"

# Browser configuration
BROWSER_OPTIONS: Final[Dict[str, List[str]]] = {
    "chrome": [
        "--disable-notifications",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--start-maximized"
    ],
    "firefox": [
        "--width=1920",
        "--height=1080"
    ]
}

# Supported browsers in order of preference
SUPPORTED_BROWSERS: Final[List[str]] = ["chrome", "firefox", "safari"]

# HTML/DOCX conversion settings
DEFAULT_TABLE_STYLE: Final[str] = "Table Grid"
DEFAULT_IMAGE_WIDTH: Final[float] = 6.0  # inches
DEFAULT_FONT_SIZE: Final[int] = 11
DEFAULT_FONT_NAME: Final[str] = "Calibri"

# Box API endpoints and settings
BOX_LOGIN_URL: Final[str] = "https://account.box.com/login"
BOX_AUTH_TIMEOUT: Final[int] = 300  # seconds
BOX_DOWNLOAD_TIMEOUT: Final[int] = 60  # seconds

# File extensions
VALID_EXTENSIONS: Final[List[str]] = [".boxnote"]
OUTPUT_EXTENSIONS: Final[List[str]] = [".html", ".docx"]

# Logging configuration
LOG_FORMAT: Final[str] = "%(log_color)s%(asctime)s [%(levelname)s] %(message)s%(reset)s"
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"