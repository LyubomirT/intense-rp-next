from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from typing import Optional
import time
import hashlib
import re

manager = None

# Content caching system to avoid reprocessing identical HTML
_content_cache = {}
_cache_max_size = 100  # Limit cache size to prevent memory issues

def _get_content_hash(html_content: str) -> str:
    """Generate a hash for HTML content to enable caching and change detection"""
    if not html_content:
        return ""
    return hashlib.md5(html_content.encode('utf-8')).hexdigest()

def _cleanup_cache():
    """Clean up cache if it gets too large"""
    if len(_content_cache) > _cache_max_size:
        # Remove oldest entries (simple FIFO)
        keys_to_remove = list(_content_cache.keys())[:-_cache_max_size//2]
        for key in keys_to_remove:
            _content_cache.pop(key, None)

def _clear_content_cache():
    """Clear the entire content cache - used when starting new chat"""
    global _content_cache
    _content_cache.clear()

# =============================================================================================================================
# Login
# =============================================================================================================================

def login(driver: Driver, email: str, password: str) -> None:
    try:
        if not email or not password:
            return
        
        driver.type("//input[@type='text']", email, timeout=15)
        driver.type("//input[@type='password']", password, timeout=15)
        driver.click("div[role='button'].ds-sign-up-form__register-button")
    except Exception as e:
        print(f"Error logging in: {e}")

# =============================================================================================================================
# Clean Regeneration functionality
# =============================================================================================================================

def can_use_regenerate_button(driver: Driver) -> bool:
    """
    Check if the regenerate button is available and not censored.
    
    Returns:
        bool: True if regenerate button can be used, False if censored or not available
    """
    try:
        # Find the container for message controls
        container = driver.find_element("class name", "_965abe9")
        
        # Find all components with the regenerate button classes within the container
        buttons = container.find_elements("xpath", ".//div[contains(@class, '_17e543b') and contains(@class, 'db183363')]")
        
        if len(buttons) < 2:
            # Not enough buttons found, regenerate button not available
            return False
        
        # The second button (index 1) is the regenerate button
        regenerate_button = buttons[1]
        
        # Check if the button is disabled due to censorship
        aria_disabled = regenerate_button.get_attribute("aria-disabled")
        
        if aria_disabled == "true":
            print("[color:yellow]Regenerate button is disabled (likely due to censorship)")
            return False
        
        print("[color:green]Regenerate button is available and enabled")
        return True
        
    except Exception as e:
        print(f"[color:yellow]Could not detect regenerate button: {e}")
        return False

def click_regenerate_button(driver: Driver) -> bool:
    """
    Click the regenerate button to regenerate the last response.
    
    Returns:
        bool: True if button was clicked successfully, False otherwise
    """
    try:
        # Record activity since user is regenerating response
        record_activity()
        
        # Find the container for message controls
        container = driver.find_element("class name", "_965abe9")
        
        # Find all components with the regenerate button classes within the container
        buttons = container.find_elements("xpath", ".//div[contains(@class, '_17e543b') and contains(@class, 'db183363')]")
        
        if len(buttons) < 2:
            print("[color:red]Regenerate button not found - insufficient buttons in container")
            return False
        
        # The second button (index 1) is the regenerate button
        regenerate_button = buttons[1]
        
        # Double-check that it's not disabled
        aria_disabled = regenerate_button.get_attribute("aria-disabled")
        if aria_disabled == "true":
            print("[color:red]Regenerate button is disabled (censorship detected)")
            return False
        
        # Click the regenerate button
        driver.execute_script("arguments[0].click();", regenerate_button)
        
        # Wait a moment for the regeneration to start
        time.sleep(0.5)
        
        print("[color:green]Regenerate button clicked successfully")
        return True
        
    except Exception as e:
        print(f"[color:red]Error clicking regenerate button: {e}")
        return False

# =============================================================================================================================
# Reset and configure chat
# =============================================================================================================================

def _close_sidebar(driver: Driver) -> None:
    """Close the sidebar if it's currently open"""
    try:
        # Check if sidebar exists and is open
        sidebar = driver.find_element("class name", "dc04ec1d")
        
        # Check if sidebar is in closed state by looking for specific class patterns
        sidebar_classes = sidebar.get_attribute("class")
        
        # If sidebar contains the closed state class, don't try to close it
        if "a02af2e6" in sidebar_classes:
            return
        
        # Find the sidebar close button - look for the button with the sidebar panel icon
        close_button = sidebar.find_element("xpath", ".//div[@role='button' and contains(@class, '_17e543b') and contains(@class, '_7d1f5e2')]")
        driver.execute_script("arguments[0].click();", close_button)
        
        # Wait a moment for the sidebar to close
        time.sleep(0.5)
        
    except Exception as e:
        # Sidebar might already be closed or element not found
        pass

def new_chat(driver: Driver) -> None:
    """Start a new chat by clicking the appropriate new chat button based on sidebar state"""
    try:
        # Check if the button area exists (indicates sidebar is closed)
        # Use a short timeout since the button area might take a moment to appear
        try:
            button_area = driver.find_element("class name", "e5bf614e")
            # Button area exists - sidebar is closed
            # Find all buttons with the shared classes within the button area
            buttons = button_area.find_elements("xpath", ".//div[contains(@class, '_17e543b') and contains(@class, '_4f3769f')]")
            
            if len(buttons) >= 2:
                # Click the SECOND button (index 1) - this is the new chat button
                # The first button (index 0) opens the sidebar
                new_chat_btn = buttons[1]
                driver.execute_script("arguments[0].click();", new_chat_btn)
                print("New chat started using button area (sidebar closed)")
            else:
                print(f"Warning: Expected 2 buttons in button area, found {len(buttons)}")
                # Fallback - try any new chat button
                boton = driver.find_element("xpath", "//div[contains(@class, 'a084f19e')]")
                driver.execute_script("arguments[0].click();", boton)
                
        except Exception:
            # Button area not found - sidebar is open
            # Use the sidebar new chat button
            try:
                new_chat_btn = driver.find_element("xpath", "//div[contains(@class, '_5a8ac7a') and contains(@class, 'a084f19e') and .//span[text()='New chat']]")
                driver.execute_script("arguments[0].click();", new_chat_btn)
                print("New chat started using sidebar button (sidebar open)")
            except Exception:
                # Fallback for open sidebar - try the general new chat class
                new_chat_btn = driver.find_element("xpath", "//div[contains(@class, 'a084f19e')]")
                driver.execute_script("arguments[0].click();", new_chat_btn)
                print("New chat started using fallback (sidebar open)")
        
        # Wait a moment for the new chat to initialize
        time.sleep(0.5)
        
        # Clear content cache when starting new chat
        _clear_content_cache()
        
    except Exception as e:
        print(f"Error starting new chat: {e}")
        # Ultimate fallback - try the old method
        try:
            boton = driver.find_element("xpath", "//div[contains(@class, 'a084f19e')]")
            driver.execute_script("arguments[0].click();", boton)
            _clear_content_cache()
        except Exception:
            pass

def _check_and_reload_page(driver: Driver) -> None:
    try:
        element = driver.find_elements("css selector", "div.a4380d7b")
        
        if element:
            driver.refresh()
            time.sleep(1)
    except Exception:
        pass

def _set_button_state(driver: Driver, xpath: str, activate: bool) -> None:
    try:
        button = driver.find_element("xpath", xpath)
        
        # Check computed background-color style (includes CSS classes)
        computed_bg = driver.execute_script("""
            return window.getComputedStyle(arguments[0]).backgroundColor;
        """, button)
        
        # Check if background matches the active state color
        # DeepSeek uses #283142 which converts to rgb(40, 49, 66)
        is_active = (computed_bg == "rgb(40, 49, 66)" or 
                    computed_bg == "rgba(40, 49, 66, 1)")
        
        if is_active != activate:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(0.5)
    except Exception as e:
        print(f"Error setting button state: {e}")

def configure_existing_chat(driver: Driver, deepthink: bool, search: bool) -> None:
    """Configure existing chat settings without creating a new chat"""
    # Record activity since user is configuring chat
    record_activity()

    global manager
    if manager and manager.get_temp_files():
        manager.delete_file("temp", manager.get_last_temp_file())

    # Close sidebar but don't create new chat
    _close_sidebar(driver)

    # Just check and reload page if needed
    _check_and_reload_page(driver)

    # Set button states for deepthink and search
    _set_button_state(driver, "//button[@role='button' and contains(@class, 'feec6a7a') and (contains(., 'DeepThink') or contains(., '深度思考'))]", deepthink)
    _set_button_state(driver, "//button[@role='button' and contains(@class, '_70150b8') and (contains(., 'Search') or contains(., '联网搜索'))]", search)

def configure_chat(driver: Driver, deepthink: bool, search: bool) -> None:
    # Record activity since user is configuring chat
    record_activity()
    
    global manager
    if manager and manager.get_temp_files():
        manager.delete_file("temp", manager.get_last_temp_file())
    
    _close_sidebar(driver)
    new_chat(driver)
    _check_and_reload_page(driver)
    _set_button_state(driver, "//button[@role='button' and contains(@class, 'feec6a7a') and (contains(., 'DeepThink') or contains(., '深度思考'))]", deepthink)
    _set_button_state(driver, "//button[@role='button' and contains(@class, '_70150b8') and (contains(., 'Search') or contains(., '联网搜索'))]", search)

# =============================================================================================================================
# Send message or upload file to chat
# =============================================================================================================================

def _click_send_message_button(driver: Driver) -> bool:
    try:
        button_xpath = "//div[@role='button' and contains(@class, '_7436101')]"
        driver.wait_for_element_present(button_xpath, by="xpath", timeout=15)
        
        end_time = time.time() + 60
        while time.time() < end_time:
            button = driver.find_element("xpath", button_xpath)
            if button.get_attribute("aria-disabled") == "false":
                driver.execute_script("arguments[0].click();", button)
                return True
            
            time.sleep(1)
        
        return False
    except Exception as e:
        print(f"Error clicking the send message button: {e}")
        return False

def _send_chat_file(driver: Driver, text: str) -> bool:
    try:
        global manager
        temp_file = manager.create_temp_txt(text)
        file_input = driver.wait_for_element_present("input[type='file']", by="css selector", timeout=10)
        file_input.send_keys(temp_file)
        
        return _click_send_message_button(driver)
    except Exception as e:
        print(f"Error when attaching text file: {e}")
        return False

def _send_chat_text(driver: Driver, text: str) -> bool:
    try:
        def attempt_send():
            chat_input = driver.wait_for_element_present("_27c9245", by="class name", timeout=15)
            
            for _ in range(3):
                chat_input.clear()
                driver.execute_script("arguments[0].value = arguments[1];", chat_input, text)
                chat_input.send_keys(" ")
                chat_input.send_keys(Keys.BACKSPACE)
                
                if chat_input.get_attribute("value") == text:
                    return True
                
                time.sleep(1)
            
            return False
        
        for _ in range(2):
            if attempt_send():
                return _click_send_message_button(driver)
            
            driver.refresh()
            time.sleep(1)
        
        return False
    except Exception as e:
        print(f"Error when pasting prompt: {e}")
        return False


def send_chat_message(driver: Driver, text: str, text_file: bool, prefix_content: str = None) -> bool:
    # Record activity since user is sending a message
    record_activity()
    
    # Send the main message (prefix_content is now handled in message formatting, not here)
    if text_file:
        success = _send_chat_file(driver, text)
    else:
        success = _send_chat_text(driver, text)
    
    return success

# =============================================================================================================================
# HTML extraction and processing
# =============================================================================================================================

def get_last_message_raw_html(driver: Driver) -> Optional[str]:
    """Get the raw HTML of the last message without processing"""
    try:
        time.sleep(0.2)
        
        messages = driver.find_elements("xpath", "//div[contains(@class, 'ds-markdown') and not(ancestor::*[contains(@class, 'ds-think-content')])]")
        
        if messages:
            return messages[-1].get_attribute("innerHTML")
        
        return None
    
    except Exception as e:
        print(f"Error when extracting raw HTML: {e}")
        return None

def has_code_block_in_html(raw_html: str) -> bool:
    """Check if raw HTML contains any code block markers"""
    if not raw_html:
        return False
    return 'md-code-block' in raw_html

def get_last_message(driver: Driver, pipeline=None) -> Optional[str]:
    """Get the last message from the chat, optionally using pipeline for processing with caching"""
    try:
        time.sleep(0.2)
        
        messages = driver.find_elements("xpath", "//div[contains(@class, 'ds-markdown') and not(ancestor::*[contains(@class, 'ds-think-content')])]")
        
        if messages:
            last_message_html = messages[-1].get_attribute("innerHTML")
            
            # Generate hash for caching
            content_hash = _get_content_hash(last_message_html)
            
            # Check cache first
            cache_key = f"{content_hash}_{bool(pipeline)}"
            if cache_key in _content_cache:
                return _content_cache[cache_key]
            
            # Process content
            if pipeline and hasattr(pipeline, 'process_response_content'):
                processed_content = pipeline.process_response_content(last_message_html)
            else:
                # Fallback to basic processing if no pipeline
                processed_content = _basic_html_cleanup(last_message_html)
            
            # Cache the result
            _content_cache[cache_key] = processed_content
            _cleanup_cache()
            
            return processed_content
        
        return None
    
    except Exception as e:
        print(f"Error when extracting the last response: {e}")
        return None

def _basic_html_cleanup(html: str) -> str:
    """Basic HTML cleanup for fallback scenarios"""
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts and styles
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Basic cleanup
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&quot;', '"')
        
        return text.strip()
        
    except Exception:
        # Ultimate fallback - return as is
        return html

# =============================================================================================================================
# Network interception control
# =============================================================================================================================

def enable_network_interception(driver: Driver) -> bool:
    """Enable CDP network interception by communicating with the extension"""
    try:
        # Send message to content script to start CDP network interception
        driver.execute_script("""
            console.log('DeepSeek driver: Enabling CDP network interception');
            window.postMessage({
                action: 'startNetworkInterception'
            }, '*');
        """)
        
        print("[color:green]CDP network interception enabled")
        return True
        
    except Exception as e:
        print(f"Error enabling CDP network interception: {e}")
        return False

def disable_network_interception(driver: Driver) -> bool:
    """Disable CDP network interception by communicating with the extension"""
    try:
        # Send message to content script to stop CDP network interception
        driver.execute_script("""
            console.log('DeepSeek driver: Disabling CDP network interception');
            window.postMessage({
                action: 'stopNetworkInterception'
            }, '*');
        """)
        
        print("[color:cyan]CDP network interception disabled")
        return True
        
    except Exception as e:
        print(f"Error disabling CDP network interception: {e}")
        return False

# =============================================================================================================================
# Bot response generation
# =============================================================================================================================

def active_generate_response(driver: Driver) -> bool:
    try:
        button = driver.wait_for_element_present("//div[@role='button' and contains(@class, '_7436101')]", by="xpath", timeout=60)
        return button
    except Exception as e:
        print(f"Error generating response: {e}")
        return False

def wait_for_response_completion(driver: Driver, pipeline=None, max_wait_time: float = 5.0) -> str:
    """
    Wait for response to be completely finished and content to stabilize using hash-based detection.
    This fixes the race condition where content appears unstable due to processing variations.
    """
    try:
        while is_response_generating(driver):
            time.sleep(0.1)
        
        last_content_hash = None
        last_content = None
        stable_count = 0
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Get raw HTML and hash it for comparison
            try:
                messages = driver.find_elements("xpath", "//div[contains(@class, 'ds-markdown') and not(ancestor::*[contains(@class, 'ds-think-content')])]")
                if messages:
                    current_html = messages[-1].get_attribute("innerHTML")
                    current_hash = _get_content_hash(current_html)
                    
                    if current_hash == last_content_hash:
                        stable_count += 1
                        # Content hash has been stable for multiple checks
                        if stable_count >= 3:  # Balanced stability requirement
                            if last_content is None:
                                last_content = get_last_message(driver, pipeline)
                            return last_content or ""
                    else:
                        stable_count = 0
                        last_content_hash = current_hash
                        last_content = None  # Reset processed content cache
                    
            except Exception:
                pass  # Continue trying
            
            time.sleep(0.2)
        
        # Final attempt to get content
        return get_last_message(driver, pipeline) or ""
        
    except Exception as e:
        print(f"Error waiting for response completion: {e}")
        return get_last_message(driver, pipeline) or ""

def is_response_generating(driver: Driver) -> bool:
    try:
        button = driver.find_element("xpath", "//div[@role='button' and contains(@class, '_7436101')]")
        return button.get_attribute("aria-disabled") == "false"
    except Exception:
        return False

def wait_for_generation_to_start(driver: Driver, timeout: float = 10.0) -> bool:
    """Wait for response generation to actually start (stop button appears) after sending message"""
    try:
        start_time = time.time()
        
        # First wait for loading phase to complete and generation to start
        while time.time() - start_time < timeout:
            if is_response_generating(driver):
                return True  # Generation has started
            time.sleep(0.1)
        
        # Timeout - generation never started
        return False
        
    except Exception as e:
        print(f"Error waiting for generation to start: {e}")
        return False

# =============================================================================================================================
# Page refresh functionality
# =============================================================================================================================

def refresh_page(driver: Driver) -> bool:
    """
    Refresh the DeepSeek page to prevent session timeouts.
    
    This function:
    1. Refreshes the page
    2. Waits for it to load
    3. Handles any login requirements
    4. Clears content cache
    
    Returns:
        bool: True if refresh was successful, False otherwise
    """
    try:
        print("[color:cyan]Refreshing page to prevent session timeout...")
        
        # Clear content cache since we're refreshing
        _clear_content_cache()
        
        # Refresh the page
        driver.refresh()
        
        # Wait for page to load
        time.sleep(3)
        
        # Check if we need to login again
        try:
            # Look for login form
            login_form = driver.find_elements("xpath", "//input[@type='text']")
            if login_form:
                print("[color:yellow]Login form detected after refresh - attempting auto-login")
                
                # Get login credentials from state manager
                from core import get_state_manager
                state = get_state_manager()
                
                email = state.get_config_value("models.deepseek.email", "")
                password = state.get_config_value("models.deepseek.password", "")
                auto_login = state.get_config_value("models.deepseek.auto_login", False)
                
                if auto_login and email and password:
                    login(driver, email, password)
                    time.sleep(2)
                    print("[color:green]Auto-login completed after refresh")
                else:
                    print("[color:orange]Auto-login not configured - manual login may be required")
                    
        except Exception as login_error:
            print(f"Note: Could not check login status after refresh: {login_error}")
        
        # Verify page loaded successfully by looking for chat interface
        try:
            chat_input = driver.find_element("class name", "_27c9245")
            if chat_input:
                print("[color:green]Page refresh successful - chat interface ready")
                return True
        except Exception:
            pass
        
        # Alternative check - look for any DeepSeek-specific elements
        try:
            deepseek_elements = driver.find_elements("xpath", "//div[contains(@class, 'ds-')]")
            if deepseek_elements:
                print("[color:green]Page refresh successful - DeepSeek interface loaded")
                return True
        except Exception:
            pass
        
        print("[color:orange]Page refresh completed but interface status unclear")
        return True
        
    except Exception as e:
        print(f"[color:red]Error refreshing page: {e}")
        return False

def start_refresh_timer() -> None:
    """Start the refresh timer if enabled in configuration."""
    try:
        from core import get_state_manager
        from utils.refresh_timer import start_refresh_timer as start_timer
        
        state = get_state_manager()
        
        # Check if refresh timer is enabled
        if not state.get_config_value("refresh_timer.enabled", False):
            return
        
        # Check if we have a driver
        if not state.driver:
            print("[color:yellow]Cannot start refresh timer - no browser driver available")
            return
        
        def refresh_callback():
            """Callback function for refresh timer."""
            driver = state.driver
            if driver:
                refresh_page(driver)
            else:
                print("[color:red]Cannot refresh - no browser driver available")
        
        def grace_period_callback():
            """Callback for when grace period starts."""
            # Only show grace period message if grace period is enabled
            use_grace_period = state.get_config_value("refresh_timer.use_grace_period", True)
            if not use_grace_period:
                return  # Don't show grace period message if it's disabled
            
            try:
                idle_timeout = int(state.get_config_value("refresh_timer.idle_timeout", 5))
            except (ValueError, TypeError):
                idle_timeout = 5
            
            try:
                grace_period = int(state.get_config_value("refresh_timer.grace_period", 25))
            except (ValueError, TypeError):
                grace_period = 25
            
            print(f"[color:orange]No activity for {idle_timeout} minutes. Page will refresh in {grace_period} seconds unless activity is detected.")
        
        # Start the timer
        start_timer(refresh_callback, grace_period_callback)
        
    except Exception as e:
        print(f"Error starting refresh timer: {e}")

def stop_refresh_timer() -> None:
    """Stop the refresh timer."""
    try:
        from utils.refresh_timer import stop_refresh_timer as stop_timer
        stop_timer()
    except Exception as e:
        print(f"Error stopping refresh timer: {e}")

def record_activity() -> None:
    """Record activity to reset the refresh timer."""
    try:
        from utils.refresh_timer import record_activity as record
        record()
    except Exception as e:
        # Don't log errors for activity recording to avoid spam
        pass
