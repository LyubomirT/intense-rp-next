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

def get_preserve_tags_from_config() -> list:
    """Get the list of tags to preserve from the API config"""
    try:
        # Import api module to access the global config
        import api
        
        if not hasattr(api, 'config') or not api.config:
            print("No API config available")
            return []
        
        # Get tag preservation settings from the API config
        tag_preservation = api.config.get("tag_preservation", {})
        preserve_tags = tag_preservation.get("preserve_tags", [])
        
        # Ensure we have a list of valid tag names
        if isinstance(preserve_tags, list):
            valid_tags = [tag.strip().lower() for tag in preserve_tags if tag and isinstance(tag, str)]
            print(f"Config loaded preserve_tags: {valid_tags}")  # Debug logging
            return valid_tags
        
        print(f"Invalid preserve_tags format: {preserve_tags}")
        return []
    except Exception as e:
        print(f"Error getting preserve tags from API config: {e}")
        return []

def get_last_message(driver: Driver) -> Optional[str]:
    try:
        time.sleep(0.1)
        
        messages = driver.find_elements("xpath", "//div[contains(@class, 'ds-markdown ds-markdown--block')]")
        
        if messages:
            last_message_html = messages[-1].get_attribute("innerHTML")
            
            # Clean up the HTML first
            last_message_html = _remove_em_inside_strong(last_message_html)

            # Get custom tags to preserve from config
            preserve_tags = get_preserve_tags_from_config()
            
            print(f"[DEBUG] Preserving tags: {preserve_tags}")
            print(f"[DEBUG] Raw HTML snippet (first 300 chars): {last_message_html[:300]}...")
            
            # STEP 1: Extract and preserve custom tags BEFORE BeautifulSoup processing
            custom_tag_placeholders = {}
            processed_message = last_message_html
            
            if preserve_tags:
                print(f"[DEBUG] Starting tag preservation for: {preserve_tags}")
                
                # DeepSeek handles custom tags in two ways:
                # 1. In regular text: <span class="ds-markdown-html">&lt;test&gt;</span>Testing<span class="ds-markdown-html">&lt;/test&gt;</span>
                # 2. In code blocks: <test>Testing</test> (just HTML entities)
                
                for tag in preserve_tags:
                    print(f"[DEBUG] Processing tag: '{tag}'")
                    
                    # FIXED: Match HTML entities in spans (&lt; instead of <)
                    # Pattern 1: HTML entities wrapped in spans (regular text)
                    escaped_span_pattern = rf'<span class="ds-markdown-html">&lt;{re.escape(tag)}(?!\w)&gt;</span>(.*?)<span class="ds-markdown-html">&lt;/{re.escape(tag)}(?!\w)&gt;</span>'
                    
                    # Pattern 2: Plain HTML entities (code blocks) - after entity conversion
                    escaped_entity_pattern = rf'<{re.escape(tag)}(?!\w)>(.*?)</{re.escape(tag)}(?!\w)>'
                    
                    print(f"[DEBUG] Span pattern: {escaped_span_pattern}")
                    print(f"[DEBUG] Entity pattern: {escaped_entity_pattern}")
                    
                    def replace_span_func(match):
                        content = match.group(1)
                        original_tag = f"<{tag}>{content}</{tag}>"
                        placeholder = f"___PRESERVE_{tag.upper()}_{len(custom_tag_placeholders)}___"
                        custom_tag_placeholders[placeholder] = original_tag
                        print(f"[DEBUG] Found span-wrapped '{tag}' tag: content='{content}' -> {placeholder}")
                        return placeholder
                    
                    def replace_entity_func(match):
                        content = match.group(1)
                        original_tag = f"<{tag}>{content}</{tag}>"
                        placeholder = f"___PRESERVE_{tag.upper()}_{len(custom_tag_placeholders)}___"
                        custom_tag_placeholders[placeholder] = original_tag
                        print(f"[DEBUG] Found entity-escaped '{tag}' tag: content='{content}' -> {placeholder}")
                        return placeholder
                    
                    # Replace span-wrapped tags (regular text)
                    before_span_count = len(custom_tag_placeholders)
                    processed_message = re.sub(escaped_span_pattern, replace_span_func, processed_message, flags=re.DOTALL | re.IGNORECASE)
                    after_span_count = len(custom_tag_placeholders)
                    print(f"[DEBUG] Span replacement for '{tag}': {after_span_count - before_span_count} matches")
                    
                    # Don't apply entity pattern yet - wait until after HTML entity conversion
                    
                print(f"[DEBUG] Total tags extracted from spans: {len(custom_tag_placeholders)}")
                print(f"[DEBUG] Message after span processing (first 300 chars): {processed_message[:300]}...")

            # STEP 2: FIXED HTML entity conversion (was completely wrong before)
            print(f"[DEBUG] Converting HTML entities...")
            processed_message = re.sub(r'&amp;', '&', processed_message)
            processed_message = re.sub(r'&lt;', '<', processed_message)
            processed_message = re.sub(r'&gt;', '>', processed_message)
            processed_message = re.sub(r'&nbsp;', ' ', processed_message)
            processed_message = re.sub(r'&quot;', '"', processed_message)
            
            print(f"[DEBUG] Message after entity conversion (first 300 chars): {processed_message[:300]}...")
            
            # STEP 2.5: Now apply entity pattern for code blocks (after entity conversion)
            if preserve_tags:
                for tag in preserve_tags:
                    escaped_entity_pattern = rf'<{re.escape(tag)}(?!\w)>(.*?)</{re.escape(tag)}(?!\w)>'
                    
                    def replace_entity_func(match):
                        content = match.group(1)
                        original_tag = f"<{tag}>{content}</{tag}>"
                        placeholder = f"___PRESERVE_{tag.upper()}_{len(custom_tag_placeholders)}___"
                        custom_tag_placeholders[placeholder] = original_tag
                        print(f"[DEBUG] Found entity-escaped '{tag}' tag: content='{content}' -> {placeholder}")
                        return placeholder
                    
                    # Replace entity-escaped tags (code blocks)
                    before_entity_count = len(custom_tag_placeholders)
                    processed_message = re.sub(escaped_entity_pattern, replace_entity_func, processed_message, flags=re.DOTALL | re.IGNORECASE)
                    after_entity_count = len(custom_tag_placeholders)
                    print(f"[DEBUG] Entity replacement for '{tag}': {after_entity_count - before_entity_count} matches")
            
            print(f"[DEBUG] Total preserved tags: {len(custom_tag_placeholders)}")
            print(f"[DEBUG] Preserved tags map: {custom_tag_placeholders}")
            print(f"[DEBUG] Message after all tag extraction (first 300 chars): {processed_message[:300]}...")
            
            # STEP 3: Process with BeautifulSoup (custom tags are now safe as placeholders)
            soup = BeautifulSoup(processed_message, 'html.parser')
            
            # Remove unwanted tags completely
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()
            
            # STEP 3.1: Convert DeepSeek code blocks to Markdown before removing UI elements
            code_blocks = soup.find_all('div', class_='md-code-block')
            print(f"[DEBUG] Found {len(code_blocks)} code blocks to convert")
            
            for code_block in code_blocks:
                try:
                    # Extract language from the UI element
                    language_elem = code_block.find('span', class_='d813de27')
                    language = language_elem.get_text().strip() if language_elem else ''
                    
                    # Extract code content from <pre> tag
                    pre_tag = code_block.find('pre')
                    if pre_tag:
                        code_content = pre_tag.get_text().strip()
                        
                        # Create Markdown code block
                        if language and language.lower() not in ['text', '']:
                            markdown_code = f"\n```{language}\n{code_content}\n```\n"
                            print(f"[DEBUG] Converting to {language} code block, content: {code_content[:50]}...")
                        else:
                            markdown_code = f"\n```\n{code_content}\n```\n"
                            print(f"[DEBUG] Converting to plain code block, content: {code_content[:50]}...")
                        
                        # Replace the entire code block with Markdown
                        code_block.replace_with(markdown_code)
                        
                        print(f"[DEBUG] Converted code block: language='{language}', content length={len(code_content)}")
                    
                except Exception as e:
                    print(f"[DEBUG] Error converting code block: {e}")
                    # If conversion fails, just remove the code block wrapper
                    pre_tag = code_block.find('pre')
                    if pre_tag:
                        code_block.replace_with(f"\n```\n{pre_tag.get_text()}\n```\n")
            
            # Remove remaining DeepSeek UI elements (after code block conversion)
            ui_selectors = [
                '.md-code-block-banner',
                '.code-info-button-text',
                '.ds-button',
                '.d813de27',
                '.efa13877',
                '.d2a24f03',
                '[role="button"]',
                '.ds-button__icon',
                '.ds-icon'
            ]
            
            for selector in ui_selectors:
                for element in soup.select(selector):
                    element.decompose()
                    
            print(f"[DEBUG] Removed DeepSeek UI elements")
            
            # STEP 3.2: Convert other HTML elements to Markdown
            # Convert headers
            for i in range(1, 7):  # h1 to h6
                for header in soup.find_all(f'h{i}'):
                    header_text = header.get_text()
                    markdown_header = f"\n{'#' * i} {header_text}\n"
                    header.replace_with(markdown_header)
            
            # Convert links
            for link in soup.find_all('a', href=True):
                link_text = link.get_text()
                link_url = link.get('href')
                if link_text and link_url:
                    markdown_link = f"[{link_text}]({link_url})"
                    link.replace_with(markdown_link)
            
            # Convert images
            for img in soup.find_all('img', src=True):
                alt_text = img.get('alt', '')
                img_url = img.get('src')
                markdown_img = f"![{alt_text}]({img_url})"
                img.replace_with(markdown_img)
            
            # Convert blockquotes
            for quote in soup.find_all('blockquote'):
                quote_text = quote.get_text().strip()
                quote_lines = quote_text.split('\n')
                markdown_quote = '\n'.join(f"> {line}" for line in quote_lines)
                quote.replace_with(f"\n{markdown_quote}\n")
            
            # Convert horizontal rules
            for hr in soup.find_all('hr'):
                hr.replace_with("\n---\n")
            
            print(f"[DEBUG] Converted HTML elements to Markdown")
            
            # STEP 3.3: Handle remaining HTML elements
            # Handle line breaks
            for br in soup.find_all('br'):
                br.replace_with('\n')
            
            # Handle list items with proper Markdown formatting
            for ul in soup.find_all('ul'):
                list_items = ul.find_all('li')
                markdown_list = []
                for li in list_items:
                    item_text = li.get_text().strip()
                    markdown_list.append(f"- {item_text}")
                ul.replace_with('\n' + '\n'.join(markdown_list) + '\n')
            
            for ol in soup.find_all('ol'):
                list_items = ol.find_all('li')
                markdown_list = []
                for i, li in enumerate(list_items, 1):
                    item_text = li.get_text().strip()
                    markdown_list.append(f"{i}. {item_text}")
                ol.replace_with('\n' + '\n'.join(markdown_list) + '\n')
            
            # Remove any remaining li tags that weren't in ul/ol
            for li in soup.find_all('li'):
                li.replace_with(f"- {li.get_text()}")
                
            # Handle paragraphs - add spacing
            for p in soup.find_all('p'):
                p.insert_after('\n\n')
                    
            # Convert formatting tags to markdown
            # Handle inline code first (single backticks)
            inline_code_elements = soup.find_all('code')
            print(f"[DEBUG] Found {len(inline_code_elements)} inline code elements")
            
            for code in inline_code_elements:
                # Make sure this isn't part of a code block we already converted
                parent_code_block = code.find_parent('div', class_='md-code-block')
                if not parent_code_block:  # Only process if not inside a code block
                    text_content = code.get_text()
                    if text_content.strip():
                        # Check if it's likely a multi-line code (contains newlines)
                        if '\n' in text_content and len(text_content.strip().split('\n')) > 1:
                            # Multi-line code, use code block format
                            code.replace_with(f"\n```\n{text_content.strip()}\n```\n")
                            print(f"[DEBUG] Converted multi-line inline code to block: {text_content[:30]}...")
                        else:
                            # Single line, use inline format
                            code.replace_with(f"`{text_content}`")
                            print(f"[DEBUG] Converted inline code: {text_content[:30]}...")
            
            # Handle bold and italic formatting
            for strong in soup.find_all(['strong', 'b']):
                text_content = strong.get_text()
                if text_content.strip():
                    strong.replace_with(f"**{text_content}**")
            
            for em in soup.find_all(['em', 'i']):
                text_content = em.get_text()
                if text_content.strip():
                    em.replace_with(f"*{text_content}*")
            
            # Convert tables to basic Markdown (simplified)
            for table in soup.find_all('table'):
                try:
                    rows = table.find_all('tr')
                    if rows:
                        markdown_table = []
                        
                        # Header row
                        header_row = rows[0]
                        headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                        if headers:
                            markdown_table.append('| ' + ' | '.join(headers) + ' |')
                            markdown_table.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
                        
                        # Data rows
                        for row in rows[1:]:
                            cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                            if cells:
                                markdown_table.append('| ' + ' | '.join(cells) + ' |')
                        
                        table.replace_with('\n' + '\n'.join(markdown_table) + '\n')
                        
                except Exception as e:
                    print(f"[DEBUG] Error converting table: {e}")
                    # Fallback: just unwrap the table
                    table.unwrap()
            
            # Unwrap remaining formatting tags
            formatting_tags = ['span', 'div']
            for tag_name in formatting_tags:
                for tag in soup.find_all(tag_name):
                    tag.unwrap()
            
            print(f"[DEBUG] Processed remaining HTML elements")
            
            # Get the processed result from BeautifulSoup
            result = soup.get_text()
            print(f"[DEBUG] Result after BeautifulSoup processing (first 300 chars): {result[:300]}...")
            
            # STEP 4: Restore custom tags
            if custom_tag_placeholders:
                print(f"[DEBUG] Restoring {len(custom_tag_placeholders)} custom tags...")
                for placeholder, original_tag in custom_tag_placeholders.items():
                    if placeholder in result:
                        result = result.replace(placeholder, original_tag)
                        print(f"[DEBUG] Restored '{placeholder}' back to '{original_tag}'")
                    else:
                        print(f"[DEBUG] WARNING: Placeholder '{placeholder}' not found in result!")
                        
                print(f"[DEBUG] Restored all custom tags")
            else:
                print(f"[DEBUG] No custom tags to restore")
                
            print(f"[DEBUG] Final result after tag restoration (first 300 chars): {result[:300]}...")
            
            # Final cleanup - fix spacing and formatting for Markdown
            result = re.sub(r'\n{3,}', '\n\n', result)  # Limit consecutive newlines
            result = re.sub(r'\*{3,}', '**', result)    # Fix multiple asterisks (preserve ** for bold)
            # Fix multiple backticks but preserve triple backticks for code blocks
            result = re.sub(r'`{4,}', '```', result)    # Fix 4+ backticks to triple
            result = re.sub(r'(?<!`)`{2}(?!`)', '`', result)  # Fix double backticks to single (but not triple)
            result = re.sub(r'^[\s]*\n', '', result)    # Remove leading empty lines
            result = re.sub(r'\n[\s]*$', '', result)    # Remove trailing empty lines
            
            # Clean up Markdown formatting issues
            result = re.sub(r'\n\s*\n\s*```', '\n\n```', result)  # Fix code block spacing
            result = re.sub(r'```\s*\n\s*\n', '```\n', result)    # Fix code block spacing
            result = re.sub(r'\n\s*\n\s*#', '\n\n#', result)      # Fix header spacing
            result = re.sub(r'\n\s*\n\s*-', '\n\n-', result)      # Fix list spacing
            
            # Clean up any extra whitespace
            result = result.strip()
            
            print(f"[DEBUG] Final cleaned result length: {len(result)}")
            print(f"[DEBUG] Final result (first 200 chars): {result[:200]}...")

            return result

        else:
            print(f"[DEBUG] No messages found")
            return None
    
    except Exception as e:
        print(f"Error when extracting the last response: {e}")
        import traceback
        traceback.print_exc()
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