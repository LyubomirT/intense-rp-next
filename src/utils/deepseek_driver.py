from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from typing import Optional
import time
import hashlib

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
# Reset and configure chat
# =============================================================================================================================

def _close_sidebar(driver: Driver) -> None:
    try:
        sidebar = driver.find_element("class name", "dc04ec1d")
        
        if "a02af2e6" not in sidebar.get_attribute("class"):
            driver.click(".ds-icon-button")
            time.sleep(1)
    except Exception:
        pass

def new_chat(driver: Driver) -> None:
    try:
        boton = driver.find_element("xpath", "//div[contains(@class, '_217e214')]")
        driver.execute_script("arguments[0].click();", boton)
        # Clear content cache when starting new chat
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
        style = button.get_attribute("style")
        is_active = "rgba(77, 107, 254, 0.40)" in style
        
        if is_active != activate:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(0.5)
    except Exception as e:
        print(f"Error setting button state: {e}")

def configure_chat(driver: Driver, deepthink: bool, search: bool) -> None:
    global manager
    if manager and manager.get_temp_files():
        manager.delete_file("temp", manager.get_last_temp_file())
    
    _close_sidebar(driver)
    new_chat(driver)
    _check_and_reload_page(driver)
    _set_button_state(driver, "//div[@role='button' and contains(@class, '_3172d9f') and contains(., 'R1')]", deepthink)
    _set_button_state(driver, "//div[@role='button' and contains(@class, '_3172d9f') and not(contains(., 'R1'))]", search)

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
            chat_input = driver.wait_for_element_present("chat-input", by="id", timeout=15)
            
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
        
        messages = driver.find_elements("xpath", "//div[contains(@class, 'ds-markdown ds-markdown--block')]")
        
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
        
        messages = driver.find_elements("xpath", "//div[contains(@class, 'ds-markdown ds-markdown--block')]")
        
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
        button = driver.wait_for_element_present("//div[@role='button' and contains(@class, '_7436101')]//div[contains(@class, '_480132b')]", by="xpath", timeout=60)
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
                messages = driver.find_elements("xpath", "//div[contains(@class, 'ds-markdown ds-markdown--block')]")
                if messages:
                    current_html = messages[-1].get_attribute("innerHTML")
                    current_hash = _get_content_hash(current_html)
                    
                    if current_hash == last_content_hash:
                        stable_count += 1
                        # Content hash has been stable for multiple checks
                        if stable_count >= 2:  # Reduced from 3 since hash-based is more reliable
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