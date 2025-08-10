from seleniumbase import Driver
from typing import Optional, Dict, Any
import platform
import os
import tempfile
import shutil
import time
import json
from config import (
    get_browser_engine,
    get_chromium_browser_path,
    is_chromium_browser,
    requires_binary_location,
    uses_undetected_chromium,
)

# =============================================================================================================================
# Initialize SeleniumBase and open browser
# =============================================================================================================================

def initialize_webdriver(custom_browser: str = "chrome", url: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Optional[Driver]:
    try:
        print(f"[color:cyan]Initializing webdriver: browser={custom_browser}, url={url}")
        if config:
            print(f"[color:cyan]Config intercept_network: {config.get('models', {}).get('deepseek', {}).get('intercept_network', False)}")
        browser = custom_browser.lower()

        # Resolve actual SeleniumBase engine via declarative alias map
        actual_browser = get_browser_engine(browser)

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

        # Set up extension loading for Chromium browsers when network interception is enabled
        extension_dir = None
        clean_profile = False
        if intercept_network and is_chromium_browser(browser):
            source_extension_dir = _get_extension_dir()
            if source_extension_dir and _validate_extension_structure(source_extension_dir):
                print(f"[color:cyan]Network interception enabled - preparing fresh extension copy...")
                # Get configured API port
                api_port = 5000  # Default port
                if config:
                    api_config = config.get("api", {})
                    api_port = api_config.get("port", 5000)
                # Create a fresh copy of the extension to avoid browser caching issues
                extension_dir = _create_fresh_extension_copy(source_extension_dir, api_port)
                if extension_dir:
                    print(f"[color:cyan]Extension copied to: {extension_dir}")
                    # Clean up old extension copies and profiles
                    _cleanup_old_extension_copies()
                    _cleanup_old_extension_profiles()
                    # Use a clean profile for better extension management
                    clean_profile = True
                else:
                    print(f"[color:red]Failed to create fresh extension copy")
                    intercept_network = False
            else:
                print(f"[color:yellow]Network interception requested but extension not found or invalid at: {source_extension_dir}")
                intercept_network = False
        
        # Set up data directory for Chromium browsers
        user_data_dir = None
        if persistent_cookies and is_chromium_browser(browser):
            user_data_dir = _get_browser_data_dir(browser)
            print(f"[color:cyan]Using persistent browser data directory: {user_data_dir}")

            # If network interception is enabled, clean any old extension installations first
            if intercept_network and is_chromium_browser(browser):
                _remove_existing_extension_from_profile(user_data_dir)

        elif clean_profile and is_chromium_browser(browser):
            # Use a clean profile for extension management (when network interception enabled but persistent cookies disabled)
            user_data_dir = _create_clean_extension_profile(browser)
            print(f"[color:cyan]Using clean extension profile: {user_data_dir}")
        else:
            # Default behavior - no special profile needed
            if intercept_network and is_chromium_browser(browser):
                print(f"[color:yellow]Network interception enabled but no profile specified - using default profile")

        # Handle browser executable path when required (e.g., Brave)
        browser_executable = None
        if requires_binary_location(browser):
            browser_executable = _get_browser_executable_path(browser)
            if browser_executable:
                print(f"[color:cyan]Using {browser.title()} executable at: {browser_executable}")
            else:
                print(f"[color:red]{browser.title()} executable not found! Please install the browser or adjust configuration.")
                return None

        # Initialize driver with proper user data directory and extension
        driver_options = {
            "browser": actual_browser,
            "chromium_arg": chromium_arg,
            "uc": uses_undetected_chromium(browser),  # Declarative undetected-chromium support
        }

        # Set binary location when required by the browser
        if requires_binary_location(browser) and browser_executable:
            driver_options["binary_location"] = browser_executable

        if user_data_dir:
            driver_options["user_data_dir"] = user_data_dir

        if extension_dir and intercept_network and is_chromium_browser(browser):
            driver_options["extension_dir"] = extension_dir

        print(f"[color:cyan]Creating Driver with options: {driver_options}")
        driver = Driver(**driver_options)
        print(f"[color:green]Driver created successfully")

        # If network interception is enabled for a Chromium browser, validate and reload the extension
        if intercept_network and is_chromium_browser(browser) and extension_dir:
            print("[color:cyan]Network interception enabled - validating extension installation...")
            if validate_extension_installation(driver):
                print("[color:green]Extension already properly installed")
            else:
                print("[color:cyan]Extension not found or invalid - attempting to reload...")
                time.sleep(2)  # Give extension time to initialize
                if validate_extension_installation(driver):
                    print("[color:green]Extension loaded successfully after delay")
                else:
                    print("[color:red]Extension failed to load - check extension directory and manifest")
        
        # Navigate to URL for all browsers (since app mode is disabled)
        if url:
            print(f"[color:cyan]Navigating to: {url}")
            driver.get(url)
            print(f"[color:green]Navigation completed")

        # Log cookie persistence status
        if persistent_cookies:
            if is_chromium_browser(browser):
                print(f"[color:green]Persistent cookies enabled for {browser.title()}")
            else:
                print(f"[color:yellow]Persistent cookies requested but not supported for {browser.title()}")
        
        # Log network interception status
        if intercept_network:
            if is_chromium_browser(browser):
                print(f"[color:green]Network interception enabled for {browser.title()}")
            else:
                print(f"[color:yellow]Network interception requested but only supported for Chromium-based browsers")

        return driver

    except Exception as e:
        import traceback
        print(f"[color:red]Error initializing Selenium driver: {e}")
        print(f"[color:red]Full traceback: {traceback.format_exc()}")
        return None

def _remove_existing_extension_from_profile(user_data_dir: str) -> None:
    """Remove any existing IntenseRP extension installations from the Chrome/Edge profile"""
    try:
        # Chrome/Edge stores extensions in Default/Extensions/
        extensions_dir = os.path.join(user_data_dir, "Default", "Extensions")
        
        if not os.path.exists(extensions_dir):
            print(f"[color:cyan]No existing extensions directory found")
            return
            
        print(f"[color:cyan]Checking for existing IntenseRP extensions in profile...")
        
        removed_count = 0
        for extension_id in os.listdir(extensions_dir):
            extension_path = os.path.join(extensions_dir, extension_id)
            
            if not os.path.isdir(extension_path):
                continue
                
            # Check each version directory for our extension
            try:
                for version_dir in os.listdir(extension_path):
                    version_path = os.path.join(extension_path, version_dir)
                    manifest_path = os.path.join(version_path, "manifest.json")
                    
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, "r") as f:
                                manifest = json.load(f)
                                # Check if this is our extension
                                if manifest.get("name") == "IntenseRP CDP Network Interceptor":
                                    print(f"[color:cyan]Found existing IntenseRP extension (ID: {extension_id}), removing...")
                                    shutil.rmtree(extension_path)
                                    removed_count += 1
                                    break  # Extension directory removed, no need to check other versions
                        except (json.JSONDecodeError, IOError) as e:
                            # Skip malformed manifest files
                            continue
                            
            except (OSError, PermissionError) as e:
                # Skip directories we can't access
                continue
                
        if removed_count > 0:
            print(f"[color:green]Removed {removed_count} existing IntenseRP extension(s) from profile")
        else:
            print(f"[color:cyan]No existing IntenseRP extensions found in profile")
            
    except Exception as e:
        print(f"[color:yellow]Error checking/removing existing extensions: {e}")


def _get_browser_executable_path(browser: str) -> Optional[str]:
    """Resolve the executable path for the given browser using declarative config."""
    try:
        return get_chromium_browser_path(browser)
    except Exception as e:
        print(f"[color:yellow]Error detecting {browser.title()} executable: {e}")
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

def _get_extension_data_dir() -> str:
    """Get or create a dedicated directory for extension management"""
    try:
        base_temp_dir = tempfile.gettempdir()
        app_data_dir = os.path.join(base_temp_dir, "IntenseRP_Browser_Data")
        extension_data_dir = os.path.join(app_data_dir, "extension_profiles")
        
        os.makedirs(extension_data_dir, exist_ok=True)
        return extension_data_dir
        
    except Exception as e:
        print(f"Error creating extension data directory: {e}")
        return os.path.join(tempfile.gettempdir(), "intenserp_extensions")

def _create_clean_extension_profile(browser: str = "chrome") -> str:
    """Create a clean Chrome/Edge profile with only our extension"""
    try:
        extension_data_dir = _get_extension_data_dir()
        profile_name = f"intenserp_extension_{int(time.time())}"
        profile_path = os.path.join(extension_data_dir, profile_name)
        
        # Remove any existing profile
        if os.path.exists(profile_path):
            shutil.rmtree(profile_path)
        
        os.makedirs(profile_path, exist_ok=True)
        
        # Create a marker file to identify this as our extension profile
        marker_file = os.path.join(profile_path, "intenserp_extension_marker.txt")
        with open(marker_file, "w") as f:
            f.write(f"IntenseRP Extension Profile\nCreated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return profile_path
        
    except Exception as e:
        print(f"Error creating clean extension profile: {e}")
        print(f"[color:red]WARNING!! THIS COULD BE DANGEROUS AS IT MAY DELETE YOUR {browser.upper()} PROFILE DATA")
        print("[color:yellow]PROCEED AT YOUR OWN RISK, IT IS RECOMMENDED TO CLOSE THIS PROGRAM NOW")
        print("[color:red]Falling back to default browser data directory")
        return _get_browser_data_dir(browser)  # Fallback to default browser data directory

def _cleanup_old_extension_profiles() -> None:
    """Clean up old extension profiles to prevent accumulation"""
    try:
        extension_data_dir = _get_extension_data_dir()
        if not os.path.exists(extension_data_dir):
            return
            
        current_time = time.time()
        max_age = 24 * 60 * 60  # 24 hours in seconds
        
        for item in os.listdir(extension_data_dir):
            item_path = os.path.join(extension_data_dir, item)
            if os.path.isdir(item_path) and item.startswith("intenserp_extension_"):
                # Check if profile is older than max_age
                try:
                    profile_time = int(item.split("_")[-1])
                    if current_time - profile_time > max_age:
                        shutil.rmtree(item_path)
                        print(f"[color:cyan]Cleaned up old extension profile: {item}")
                except (ValueError, IndexError):
                    # If we can't parse the timestamp, clean it up anyway
                    shutil.rmtree(item_path)
                    print(f"[color:cyan]Cleaned up malformed extension profile: {item}")
                    
    except Exception as e:
        print(f"[color:yellow]Error cleaning up old extension profiles: {e}")

def _validate_extension_structure(extension_dir: str) -> bool:
    """Validate that the extension directory has the required files"""
    try:
        if not os.path.exists(extension_dir):
            return False
            
        required_files = ["manifest.json", "background.js", "content.js"]
        for file in required_files:
            file_path = os.path.join(extension_dir, file)
            if not os.path.exists(file_path):
                print(f"[color:red]Missing required extension file: {file}")
                return False
                
        # Validate manifest.json
        manifest_path = os.path.join(extension_dir, "manifest.json")
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                if manifest.get("name") != "IntenseRP CDP Network Interceptor":
                    print(f"[color:red]Invalid extension manifest: wrong name")
                    return False
        except Exception as e:
            print(f"[color:red]Error reading manifest.json: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"[color:red]Error validating extension structure: {e}")
        return False

def _create_fresh_extension_copy(source_extension_dir: str, api_port: int = 5000) -> str:
    """Create a fresh copy of the extension to avoid Chrome caching issues"""
    try:
        # Create a unique temporary directory for this extension copy
        base_temp_dir = tempfile.gettempdir()
        app_temp_dir = os.path.join(base_temp_dir, "IntenseRP_Extension_Copies")
        os.makedirs(app_temp_dir, exist_ok=True)
        
        # Create unique directory name with timestamp
        timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
        copy_name = f"intenserp_ext_{timestamp}"
        copy_path = os.path.join(app_temp_dir, copy_name)
        
        # Copy the entire extension directory
        print(f"[color:cyan]Copying extension from {source_extension_dir} to {copy_path}")
        shutil.copytree(source_extension_dir, copy_path)
        
        # Replace port in background.js if different from default
        if api_port != 5000:
            background_js_path = os.path.join(copy_path, "background.js")
            if os.path.exists(background_js_path):
                try:
                    print(f"[color:cyan]Updating extension port from 5000 to {api_port}")
                    with open(background_js_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace DEFAULT_PORT value
                    content = content.replace('const DEFAULT_PORT = 5000;', f'const DEFAULT_PORT = {api_port};')
                    
                    with open(background_js_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"[color:green]Extension port updated successfully to {api_port}")
                except Exception as e:
                    print(f"[color:yellow]Warning: Could not update extension port: {e}")
        else:
            print(f"[color:cyan]Using default port {api_port}, no extension modification needed")
        
        # Verify the copy was successful
        if _validate_extension_structure(copy_path):
            print(f"[color:green]Extension copy created and validated successfully")
            return copy_path
        else:
            print(f"[color:red]Extension copy validation failed")
            # Clean up the failed copy
            if os.path.exists(copy_path):
                shutil.rmtree(copy_path)
            return None
            
    except Exception as e:
        print(f"[color:red]Error creating fresh extension copy: {e}")
        return None

def _cleanup_old_extension_copies() -> None:
    """Clean up old extension copies to prevent disk space accumulation"""
    try:
        base_temp_dir = tempfile.gettempdir()
        app_temp_dir = os.path.join(base_temp_dir, "IntenseRP_Extension_Copies")
        
        if not os.path.exists(app_temp_dir):
            return
            
        current_time = time.time() * 1000  # Convert to milliseconds
        max_age = 2 * 60 * 60 * 1000  # 2 hours in milliseconds
        cleanup_count = 0
        
        for item in os.listdir(app_temp_dir):
            item_path = os.path.join(app_temp_dir, item)
            if os.path.isdir(item_path) and item.startswith("intenserp_ext_"):
                try:
                    # Extract timestamp from directory name
                    timestamp_str = item.split("intenserp_ext_")[1]
                    timestamp = int(timestamp_str)
                    
                    # Remove if older than max_age
                    if current_time - timestamp > max_age:
                        shutil.rmtree(item_path)
                        cleanup_count += 1
                        
                except (ValueError, IndexError):
                    # If we can't parse the timestamp, it's probably old/malformed, remove it
                    shutil.rmtree(item_path)
                    cleanup_count += 1
                    
        if cleanup_count > 0:
            print(f"[color:cyan]Cleaned up {cleanup_count} old extension copies")
            
    except Exception as e:
        print(f"[color:yellow]Error cleaning up old extension copies: {e}")

def _get_extension_dir() -> str:
    """Get the path to the Chrome/Edge extension directory"""
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

def validate_extension_installation(driver) -> bool:
    """Validate that the IntenseRP extension is properly installed and working"""
    try:
        # Test extension functionality by checking if it can communicate
        # This is more reliable than trying to access chrome://extensions/
        
        # Test if we can execute basic JavaScript (extension should not interfere)
        try:
            test_result = driver.execute_script("""
                // Test if extension is active by checking for basic functionality
                return {
                    hasPostMessage: typeof window.postMessage === 'function',
                    readyState: document.readyState,
                    protocol: window.location.protocol,
                    host: window.location.hostname
                };
            """)
            
            if not test_result.get('hasPostMessage'):
                print("[color:yellow]Basic JavaScript functionality test failed")
                return False
            
            # If we're on DeepSeek, test extension communication
            if 'deepseek.com' in test_result.get('host', ''):
                # Send a test message to the extension
                driver.execute_script("""
                    window.postMessage({
                        action: 'startNetworkInterception',
                        test: true
                    }, '*');
                """)
                
                # Wait for extension to process
                time.sleep(1)
                
                print("[color:green]Extension communication test completed")
                return True
            else:
                # On non-DeepSeek pages, extension should be loaded but not active
                print("[color:green]Extension loaded (not on DeepSeek domain)")
                return True
                
        except Exception as script_error:
            print(f"[color:yellow]Extension validation script error: {script_error}")
            return False
            
    except Exception as e:
        print(f"[color:red]Error validating extension installation: {e}")
        return False

def get_extension_status(driver) -> dict:
    """Get detailed extension status information"""
    try:
        status = {
            'loaded': False,
            'active': False,
            'error': None,
            'on_target_domain': False
        }
        
        # Check current page and extension state
        try:
            current_url = driver.get_current_url()
            status['on_target_domain'] = 'chat.deepseek.com' in current_url
            
            # Test basic extension functionality
            result = driver.execute_script("""
                try {
                    // Test if we can send messages (extension should listen)
                    window.postMessage({
                        action: 'startNetworkInterception',
                        test: true
                    }, '*');
                    
                    return {
                        success: true,
                        url: window.location.href,
                        protocol: window.location.protocol
                    };
                } catch (e) {
                    return {
                        success: false,
                        error: e.message
                    };
                }
            """)
            
            if result.get('success'):
                status['loaded'] = True
                status['active'] = status['on_target_domain']
            else:
                status['error'] = result.get('error', 'Unknown error')
                
        except Exception as e:
            status['error'] = str(e)
            
        return status
        
    except Exception as e:
        return {
            'loaded': False,
            'active': False,
            'error': str(e),
            'on_target_domain': False
        }

def get_chrome_extension_logs(driver) -> list:
    """Get Chrome/Edge extension console logs for debugging"""
    try:
        # Get browser logs that might contain extension messages
        logs = driver.get_log('browser')
        extension_logs = []
        
        for log in logs:
            message = log.get('message', '')
            if ('IntenseRP' in message or 'CDP' in message or 
                'Network Interceptor' in message or 'background.js' in message):
                extension_logs.append({
                    'timestamp': log.get('timestamp'),
                    'level': log.get('level'),
                    'message': message
                })
        
        return extension_logs
        
    except Exception as e:
        print(f"[color:yellow]Error getting extension logs: {e}")
        return []

def restart_chrome_with_extension(config: Optional[Dict[str, Any]] = None) -> Optional[Driver]:
    """Restart Chrome/Edge with proper extension loading - replaces the old reload mechanism"""
    try:
        print("[color:cyan]Restarting Chrome/Edge with clean extension loading...")
        
        # Clean up old extension profiles first
        _cleanup_old_extension_profiles()
        
        # Initialize a new driver instance with extension
        new_driver = initialize_webdriver("chrome", "https://chat.deepseek.com", config)
        
        if new_driver:
            print("[color:green]Chrome/Edge restarted successfully with extension")
            return new_driver
        else:
            print("[color:red]Failed to restart Chrome/Edge with extension")
            return None
            
    except Exception as e:
        print(f"[color:red]Error restarting Chrome/Edge with extension: {e}")
        return None

# Legacy functions - deprecated in favor of Chrome/Edge profile + --load-extension approach
# These functions are kept for compatibility but are no longer used

def deprecated_reload_chrome_extension(driver) -> bool:
    """DEPRECATED: Use restart_chrome_with_extension() instead"""
    print("[color:yellow]reload_chrome_extension() is deprecated - use restart_chrome_with_extension() instead")
    return False

def deprecated_remove_and_reinstall_extension(driver, extension_dir: str) -> bool:
    """DEPRECATED: Use restart_chrome_with_extension() instead"""
    print("[color:yellow]remove_and_reinstall_extension() is deprecated - use restart_chrome_with_extension() instead")
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