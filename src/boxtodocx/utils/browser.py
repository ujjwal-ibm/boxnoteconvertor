"""Browser management utilities for Box authentication and downloads."""
from typing import Optional, Dict, Any
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .constants import (
    BROWSER_OPTIONS,
    SUPPORTED_BROWSERS,
    BOX_LOGIN_URL,
    BOX_AUTH_TIMEOUT,
    BOX_DOWNLOAD_TIMEOUT
)
from .logger import setup_logger

logger = setup_logger(__name__)

class BrowserManager:
    """Manages browser instances for Box authentication and downloads."""
    
    def __init__(self) -> None:
        self.driver: Optional[WebDriver] = None
        self.cookies: Optional[list] = None
        self._initialized: bool = False
    
    def initialize_browser(self, headless: bool = False) -> None:
        """
        Initialize a browser instance with appropriate options.
        
        Args:
            headless: Whether to run browser in headless mode
        
        Raises:
            RuntimeError: If no supported browser could be initialized
        """
        if self._initialized:
            return
            
        for browser_name in SUPPORTED_BROWSERS:
            try:
                headless=True
                options = self._get_browser_options(browser_name, headless)
                driver_class = self._get_driver_class(browser_name)
                self.driver = driver_class(options=options)
                logger.info(f"Successfully initialized {browser_name} browser")
                self._initialized = True
                return
            except WebDriverException as e:
                logger.debug(f"Failed to initialize {browser_name}: {str(e)}")
                continue
                
        raise RuntimeError("No supported browser could be initialized. Please install Chrome, Firefox, or Safari.")
    
    def _get_browser_options(self, browser_name: str, headless: bool) -> Any:
        """Get browser-specific options."""
        options_map = {
            "chrome": ChromeOptions,
            "firefox": FirefoxOptions,
            "safari": SafariOptions
        }
        
        options = options_map[browser_name]()
        
        if headless and browser_name != "safari":
            options.add_argument("--headless")
            
        for option in BROWSER_OPTIONS.get(browser_name, []):
            options.add_argument(option)
            
        return options
    
    def _get_driver_class(self, browser_name: str) -> Any:
        """Get the appropriate WebDriver class."""
        return {
            "chrome": webdriver.Chrome,
            "firefox": webdriver.Firefox,
            "safari": webdriver.Safari
        }[browser_name]
    
    def authenticate_box(self, credentials: Dict[str, str]) -> None:
        """
        Authenticate with Box using provided credentials.
        
        Args:
            credentials: Dict containing login credentials and selectors
            
        Raises:
            TimeoutException: If authentication times out
            RuntimeError: If browser is not initialized
        """
        if not self.driver:
            raise RuntimeError("Browser not initialized. Call initialize_browser() first.")
            
        try:
            self.driver.get(BOX_LOGIN_URL)
            
            # Enter email
            email_input = WebDriverWait(self.driver, BOX_AUTH_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "login-email"))
            )
            email_input.send_keys(credentials["user_id"])
            
            # Click submit
            self.driver.find_element(By.ID, "login-submit").click()
            
            # Handle additional authentication steps
            self._handle_auth_steps(credentials)
            
            # Store cookies after successful login
            self.cookies = self.driver.get_cookies()
            logger.info("Successfully authenticated with Box")
            
        except TimeoutException as e:
            logger.error("Authentication timed out")
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def _handle_auth_steps(self, credentials: Dict[str, str]) -> None:
        """Handle multi-step authentication process."""
        try:
            # Click specific div if required
            if credentials.get("link_id"):
                specific_div = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, credentials["link_id"]))
                )
                specific_div.click()
            
            # Enter username/password
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, credentials["user_field_id"]))
            ).send_keys(credentials["user_id"])
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, credentials["password_field_id"]))
            ).send_keys(credentials["password"])
            
            self.driver.find_element(By.ID, "login-button").click()
            
            # Handle MFA if required
            if credentials.get("mfa_link") and credentials.get("mfa_otp"):
                self._handle_mfa(credentials)
                
        except Exception as e:
            logger.error(f"Error during authentication steps: {str(e)}")
            raise
    
    def _handle_mfa(self, credentials: Dict[str, str]) -> None:
        """Handle multi-factor authentication."""
        try:
            mfa_div = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, credentials["mfa_link"]))
            )
            mfa_div.click()
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, credentials["mfa_otp_id"]))
            ).send_keys(credentials["mfa_otp"])
            
            self.driver.find_element(By.ID, credentials["mfa_btn_id"]).click()
            time.sleep(5)  # Wait for MFA processing
            
        except TimeoutException:
            logger.info("MFA step not required")
    
    def cleanup(self) -> None:
        """Clean up browser resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser session closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None
                self._initialized = False
                self.cookies = None
                
    def __enter__(self) -> 'BrowserManager':
        """Context manager entry."""
        self.initialize_browser()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.cleanup()