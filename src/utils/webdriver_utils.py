from seleniumbase import Driver
from typing import Optional, Dict, Any
import os
import tempfile

# =============================================================================================================================
# Initialize SeleniumBase and open browser
# =============================================================================================================================

def initialize_webdriver(custom_browser: str = "chrome", url: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Optional[Driver]:
    try:
        browser = custom_browser.lower()
        chromium_arg = None
        
        # Check if persistent cookies are enabled
        persistent_cookies = False
        if config:
            persistent_cookies = config.get("browser_persistent_cookies", False)
        
        # Configure browser arguments
        if browser in ("chrome", "edge"):
            if url:
                chromium_arg = f"--app={url}"
        
        # Set up persistent data directory for Chromium browsers if enabled
        user_data_dir = None
        if persistent_cookies and browser in ("chrome", "edge"):
            user_data_dir = _get_browser_data_dir(browser)
            print(f"[color:cyan]Using persistent browser data directory: {user_data_dir}")

        # Initialize driver with proper user data directory
        if user_data_dir:
            # Use SeleniumBase's user_data_dir parameter instead of chromium_arg
            driver = Driver(
                browser=browser,
                chromium_arg=chromium_arg,
                uc=(browser == "chrome"),
                user_data_dir=user_data_dir
            )
        else:
            driver = Driver(
                browser=browser,
                chromium_arg=chromium_arg,
                uc=(browser == "chrome"),
            )
        
        if browser in ("firefox", "safari") and url:
            driver.get(url)

        # Log cookie persistence status
        if persistent_cookies:
            if browser in ("chrome", "edge"):
                print(f"[color:green]Persistent cookies enabled for {browser.title()}")
            else:
                print(f"[color:yellow]Persistent cookies requested but not supported for {browser.title()}")
        
        return driver

    except Exception as e:
        print(f"Error initializing Selenium driver: {e}")
        return None

def _get_browser_data_dir(browser: str) -> str:
    """Get or create a persistent data directory for the specified browser"""
    try:
        # Create a data directory in the system temp folder
        base_temp_dir = tempfile.gettempdir()
        app_data_dir = os.path.join(base_temp_dir, "IntenseRP_Browser_Data")
        browser_data_dir = os.path.join(app_data_dir, f"{browser}_profile")
        
        # Create the directory if it doesn't exist
        os.makedirs(browser_data_dir, exist_ok=True)
        
        return browser_data_dir
        
    except Exception as e:
        print(f"Error creating browser data directory: {e}")
        # Fallback to temp directory
        return os.path.join(tempfile.gettempdir(), f"intenserp_{browser}_data")

def clear_browser_data(browser: str) -> bool:
    """Clear persistent browser data for the specified browser"""
    try:
        browser_data_dir = _get_browser_data_dir(browser)
        
        if os.path.exists(browser_data_dir):
            import shutil
            shutil.rmtree(browser_data_dir)
            print(f"[color:green]Cleared browser data for {browser.title()}")
            return True
        else:
            print(f"[color:yellow]No browser data found for {browser.title()}")
            return True
            
    except Exception as e:
        print(f"[color:red]Error clearing browser data for {browser.title()}: {e}")
        return False

# =============================================================================================================================
# SeleniumBase Utils
# =============================================================================================================================

def is_browser_open(driver: Driver) -> bool:
    try:
        _ = driver.title
        return True
    except Exception:
        return False

def current_page(driver: Driver, url: str) -> bool:
    try:
        return driver.get_current_url().startswith(url)
    except Exception:
        return False