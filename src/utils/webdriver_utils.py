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
        
        # If network interception is enabled and we're using Chrome, reload the extension
        if intercept_network and browser == "chrome" and extension_dir:
            print("[color:cyan]Network interception enabled - reloading extension for better reliability...")
            reload_chrome_extension(driver)
        
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

def reload_chrome_extension(driver) -> bool:
    """Reload the Chrome extension by disabling and re-enabling it"""
    try:
        print("[color:cyan]Attempting to reload Chrome extension...")
        
        # Navigate to Chrome extension management page
        driver.get("chrome://extensions/")
        import time
        time.sleep(2)
        
        # Enable developer mode if not already enabled
        try:
            developer_toggle = driver.execute_script("""
                return document.querySelector('extensions-manager')
                    .shadowRoot.querySelector('extensions-toolbar')
                    .shadowRoot.querySelector('#devMode');
            """)
            
            if developer_toggle:
                is_checked = driver.execute_script("return arguments[0].checked;", developer_toggle)
                if not is_checked:
                    driver.execute_script("arguments[0].click();", developer_toggle)
                    time.sleep(1)
                    print("[color:cyan]Enabled developer mode")
        except Exception as e:
            print(f"[color:yellow]Could not toggle developer mode: {e}")
        
        # Find our extension by name and reload it
        extension_reloaded = driver.execute_script("""
            try {
                const extensionsManager = document.querySelector('extensions-manager');
                if (!extensionsManager) return false;
                
                const itemList = extensionsManager.shadowRoot.querySelector('extensions-item-list');
                if (!itemList) return false;
                
                const extensionItems = itemList.shadowRoot.querySelectorAll('extensions-item');
                
                for (let item of extensionItems) {
                    const name = item.shadowRoot.querySelector('#name');
                    if (name && name.textContent.includes('IntenseRP CDP Network Interceptor')) {
                        // Try to find and click the reload button
                        const reloadButton = item.shadowRoot.querySelector('#reload-button');
                        if (reloadButton && !reloadButton.hidden) {
                            reloadButton.click();
                            console.log('Extension reloaded successfully');
                            return true;
                        }
                        
                        // If no reload button, try toggle off/on
                        const toggle = item.shadowRoot.querySelector('#enable-toggle');
                        if (toggle) {
                            // Disable first
                            if (toggle.checked) {
                                toggle.click();
                                setTimeout(() => {
                                    // Re-enable after a short delay
                                    toggle.click();
                                    console.log('Extension toggled off/on');
                                }, 500);
                            }
                            return true;
                        }
                    }
                }
                return false;
            } catch (e) {
                console.error('Error reloading extension:', e);
                return false;
            }
        """)
        
        if extension_reloaded:
            print("[color:green]Chrome extension reloaded successfully")
            time.sleep(2)  # Give extension time to reinitialize
            return True
        else:
            print("[color:yellow]Could not find or reload the extension")
            return False
            
    except Exception as e:
        print(f"[color:red]Error reloading Chrome extension: {e}")
        return False

def remove_and_reinstall_extension(driver, extension_dir: str) -> bool:
    """Remove and reinstall the Chrome extension"""
    try:
        print("[color:cyan]Attempting to remove and reinstall Chrome extension...")
        
        # Navigate to Chrome extension management page
        driver.get("chrome://extensions/")
        import time
        time.sleep(2)
        
        # Enable developer mode
        try:
            developer_toggle = driver.execute_script("""
                return document.querySelector('extensions-manager')
                    .shadowRoot.querySelector('extensions-toolbar')
                    .shadowRoot.querySelector('#devMode');
            """)
            
            if developer_toggle:
                is_checked = driver.execute_script("return arguments[0].checked;", developer_toggle)
                if not is_checked:
                    driver.execute_script("arguments[0].click();", developer_toggle)
                    time.sleep(1)
                    print("[color:cyan]Enabled developer mode")
        except Exception as e:
            print(f"[color:yellow]Could not enable developer mode: {e}")
        
        # Remove existing extension
        extension_removed = driver.execute_script("""
            try {
                const extensionsManager = document.querySelector('extensions-manager');
                if (!extensionsManager) return false;
                
                const itemList = extensionsManager.shadowRoot.querySelector('extensions-item-list');
                if (!itemList) return false;
                
                const extensionItems = itemList.shadowRoot.querySelectorAll('extensions-item');
                
                for (let item of extensionItems) {
                    const name = item.shadowRoot.querySelector('#name');
                    if (name && name.textContent.includes('IntenseRP CDP Network Interceptor')) {
                        const removeButton = item.shadowRoot.querySelector('#remove-button');
                        if (removeButton) {
                            removeButton.click();
                            // Confirm removal in dialog
                            setTimeout(() => {
                                const dialog = document.querySelector('extensions-manager')
                                    .shadowRoot.querySelector('cr-dialog[id="dialog"]');
                                if (dialog) {
                                    const confirmButton = dialog.querySelector('.action-button');
                                    if (confirmButton) {
                                        confirmButton.click();
                                        console.log('Extension removed');
                                    }
                                }
                            }, 500);
                            return true;
                        }
                    }
                }
                return false;
            } catch (e) {
                console.error('Error removing extension:', e);
                return false;
            }
        """)
        
        if extension_removed:
            print("[color:cyan]Extension removed, waiting before reinstall...")
            time.sleep(3)
        
        # Load unpacked extension
        load_success = driver.execute_script(f"""
            try {{
                const extensionsManager = document.querySelector('extensions-manager');
                if (!extensionsManager) return false;
                
                const toolbar = extensionsManager.shadowRoot.querySelector('extensions-toolbar');
                if (!toolbar) return false;
                
                const loadButton = toolbar.shadowRoot.querySelector('#load-unpacked');
                if (loadButton) {{
                    loadButton.click();
                    console.log('Load unpacked button clicked');
                    return true;
                }}
                return false;
            }} catch (e) {{
                console.error('Error clicking load unpacked:', e);
                return false;
            }}
        """)
        
        if load_success:
            print(f"[color:cyan]Load unpacked dialog opened. Extension directory: {extension_dir}")
            time.sleep(2)
            
            # Note: We can't automatically select the folder in the file dialog due to browser security restrictions
            # The user would need to manually select the extension folder
            print("[color:yellow]Please manually select the extension folder in the file dialog that opened")
            print(f"[color:yellow]Extension folder path: {extension_dir}")
            return True
        else:
            print("[color:red]Could not open load unpacked dialog")
            return False
            
    except Exception as e:
        print(f"[color:red]Error removing and reinstalling extension: {e}")
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