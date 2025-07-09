from seleniumbase import Driver
from typing import Optional, Dict, Any
import os
import tempfile

# =============================================================================================================================
# Initialize SeleniumBase and open browser
# =============================================================================================================================

def initialize_webdriver(custom_browser: str = "chrome", url: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Optional[Driver]:
    try:
        print(f"[color:cyan]Initializing webdriver: browser={custom_browser}, url={url}")
        if config:
            print(f"[color:cyan]Config intercept_network: {config.get('models', {}).get('deepseek', {}).get('intercept_network', False)}")
        browser = custom_browser.lower()
        chromium_arg = None
        
        # Check if persistent cookies are enabled
        persistent_cookies = False
        if config:
            persistent_cookies = config.get("browser_persistent_cookies", False)
        
        # Check if network interception is enabled
        intercept_network = False
        if config:
            # Navigate through nested config structure
            models_config = config.get("models", {})
            deepseek_config = models_config.get("deepseek", {})
            intercept_network = deepseek_config.get("intercept_network", False)
        
        # Configure browser arguments
        # Note: App mode disabled to ensure extension compatibility
        chromium_arg = None
        
        # Set up persistent data directory for Chromium browsers if enabled
        user_data_dir = None
        if persistent_cookies and browser in ("chrome", "edge"):
            user_data_dir = _get_browser_data_dir(browser)
            print(f"[color:cyan]Using persistent browser data directory: {user_data_dir}")

        # Set up extension loading for Chrome when network interception is enabled
        extension_dir = None
        if intercept_network and browser == "chrome":
            extension_dir = _get_extension_dir()
            if extension_dir and os.path.exists(extension_dir):
                print(f"[color:cyan]Network interception enabled - loading extension from: {extension_dir}")
            else:
                print(f"[color:yellow]Network interception requested but extension not found at: {extension_dir}")
                intercept_network = False

        # Initialize driver with proper user data directory and extension
        driver_options = {
            "browser": browser,
            "chromium_arg": chromium_arg,
            "uc": (browser == "chrome"),
        }
        
        if user_data_dir:
            driver_options["user_data_dir"] = user_data_dir
            
        if extension_dir and intercept_network and browser == "chrome":
            driver_options["extension_dir"] = extension_dir

        print(f"[color:cyan]Creating Driver with options: {driver_options}")
        driver = Driver(**driver_options)
        print(f"[color:green]Driver created successfully")
        
        # Navigate to URL for all browsers (since app mode is disabled)
        if url:
            print(f"[color:cyan]Navigating to: {url}")
            driver.get(url)
            print(f"[color:green]Navigation completed")

        # Log cookie persistence status
        if persistent_cookies:
            if browser in ("chrome", "edge"):
                print(f"[color:green]Persistent cookies enabled for {browser.title()}")
            else:
                print(f"[color:yellow]Persistent cookies requested but not supported for {browser.title()}")
        
        # Log network interception status
        if intercept_network:
            if browser == "chrome":
                print(f"[color:green]Network interception enabled for {browser.title()}")
            else:
                print(f"[color:yellow]Network interception requested but only supported for Chrome")
        
        return driver

    except Exception as e:
        import traceback
        print(f"[color:red]Error initializing Selenium driver: {e}")
        print(f"[color:red]Full traceback: {traceback.format_exc()}")
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

def _get_extension_dir() -> str:
    """Get the path to the Chrome extension directory"""
    try:
        # Get the path relative to the current file location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to src directory, then to extension directory
        src_dir = os.path.dirname(current_dir)
        extension_dir = os.path.join(src_dir, "extension")
        
        return extension_dir
        
    except Exception as e:
        print(f"Error getting extension directory: {e}")
        return ""

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