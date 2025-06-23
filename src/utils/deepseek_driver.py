from selenium.webdriver.common.keys import Keys
from seleniumbase import Driver
from bs4 import BeautifulSoup
from typing import Optional
import re, time

manager = None

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

def configure_chat(driver: Driver, r1: bool, search: bool) -> None:
    global manager
    if manager.get_temp_files():
        manager.delete_file("temp", manager.get_last_temp_file())
    
    _close_sidebar(driver)
    new_chat(driver)
    _check_and_reload_page(driver)
    _set_button_state(driver, "//div[@role='button' and contains(@class, '_3172d9f') and contains(., 'R1')]", r1)
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

def send_chat_message(driver: Driver, text: str, text_file: bool) -> bool:
    if text_file:
        return _send_chat_file(driver, text)
    else:
        return _send_chat_text(driver, text)

# =============================================================================================================================
# HTML extraction and processing
# =============================================================================================================================

def _remove_em_inside_strong(html: str) -> str:
    try:
        result = []
        inside_strong = False
        i = 0
        while i < len(html):
            if html[i:i+8] == "<strong>":
                inside_strong = True
                result.append("<strong>")
                i += 8
            elif html[i:i+9] == "</strong>":
                inside_strong = False
                result.append("</strong>")
                i += 9
            elif html[i:i+4] == "<em>" and inside_strong:
                i += 4
            elif html[i:i+5] == "</em>" and inside_strong:
                i += 5
            else:
                result.append(html[i])
                i += 1
        return "".join(result)
    except Exception as e:
        print(f"Error when editing html: {e}")
        return html

def get_closing_symbol(text: str) -> str:
    try:
        if not text:
            return ""
        
        text = text.strip()
        analysis_text = text.split("\n")[-1].strip()
        
        if re.search(r'(?:"\.?$|\*\.?$)', analysis_text):
            return ""
        
        current_symbol = None
        opposite_chars = {
            '"': ['*'],
            '*': ['"']
        }
        
        for char in analysis_text:
            if char in ['"', '*']:
                if current_symbol is None:
                    current_symbol = char
                elif char == current_symbol:
                    current_symbol = None
                elif char in opposite_chars[current_symbol]:
                    current_symbol = char
        
        return current_symbol if current_symbol else ""
    except Exception:
        return ""

def get_last_message(driver: Driver) -> Optional[str]:
    try:
        time.sleep(0.1)
        
        messages = driver.find_elements("xpath", "//div[contains(@class, 'ds-markdown ds-markdown--block')]")
        
        if messages:
            last_message_html = messages[-1].get_attribute("innerHTML")
            
            last_message_html = _remove_em_inside_strong(last_message_html)

            processed_message = re.sub(r'</p></li>', '', last_message_html)

            processed_message = re.sub(r'</h3>(?!$)', '\n\n', processed_message)
            processed_message = re.sub(r'</p>(?!$)', '\n\n', processed_message)
            processed_message = re.sub(r'</ul>(?!$)', '\n\n', processed_message)
            processed_message = re.sub(r'<li>', '\n- ', processed_message)
            processed_message = re.sub(r'<br\s*/?>', '\n', processed_message, flags=re.IGNORECASE)

            processed_message = re.sub(r'</?code>', '`', processed_message)
            processed_message = re.sub(r'</?strong>', '*', processed_message)
            processed_message = re.sub(r'</?em>', '*', processed_message)

            processed_message = re.sub(r'&amp;', '&', processed_message)
            processed_message = re.sub(r'&lt;', '<', processed_message)
            processed_message = re.sub(r'&gt;', '>', processed_message)
            processed_message = re.sub(r'&nbsp;', ' ', processed_message)
            processed_message = re.sub(r'&quot;', '"', processed_message)
            
            soup = BeautifulSoup(processed_message, 'html.parser')
            text_only = soup.get_text()
            
            clean_text = re.sub(r'\n{3,}', '\n\n', text_only)
            clean_text = re.sub(r'\*{2,}', '*', clean_text)
            clean_text = re.sub(r'"{2,}', '"', clean_text)
            clean_text = re.sub(r'`{2,}', '`', clean_text)
            
            clean_text = re.sub(r'^\*([^\s*]+)\s\*(.*)$', r'*\1 \2', clean_text, flags=re.MULTILINE)

            return clean_text.strip("\n")

        else:
            return None
    
    except Exception as e:
        print(f"Error when extracting the last response: {e}")
        return None

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

def wait_for_response_completion(driver: Driver, max_wait_time: float = 5.0) -> str:
    """
    Wait for response to be completely finished and content to stabilize.
    This fixes the race condition where button state changes before content is fully rendered.
    """
    try:
        while is_response_generating(driver):
            time.sleep(0.1)
        
        last_content = None
        stable_count = 0
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            current_content = get_last_message(driver)
            
            if current_content == last_content:
                stable_count += 1
                # Content has been stable for multiple checks
                if stable_count >= 3:
                    return current_content or ""
            else:
                stable_count = 0
                last_content = current_content
            
            time.sleep(0.2)
        
        return last_content or ""
        
    except Exception as e:
        print(f"Error waiting for response completion: {e}")
        return get_last_message(driver) or ""

def is_response_generating(driver: Driver) -> bool:
    try:
        button = driver.find_element("xpath", "//div[@role='button' and contains(@class, '_7436101')]")
        return button.get_attribute("aria-disabled") == "false"
    except Exception:
        return False