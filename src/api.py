from flask import Flask, jsonify, request, Response
import utils.response_utils as response_utils
import utils.webdriver_utils as selenium
import utils.deepseek_driver as deepseek
import socket, time, threading
from typing import Generator
from waitress import serve
import re

app = Flask(__name__)
driver = None
last_driver = 0
last_response = 0
textbox = None
config = {}
logging_manager = None

@app.route("/models", methods=["GET"])
def model() -> Response:
    global driver
    if not driver:
        return jsonify({}), 503

    show_message("\n[color:purple]API CONNECTION:")
    try:
        show_message("[color:white]- [color:green]Successful connection.")
        return response_utils.get_model()
    except Exception as e:
        show_message("[color:white]- [color:red]Error connecting.")
        print(f"Error connecting to API: {e}")
        return jsonify({}), 500

@app.route("/chat/completions", methods=["POST"])
def bot_response() -> Response:
    global driver, config, last_response
    try:
        data = request.get_json()
        if not data:
            print("Error: Empty data was received.")
            return jsonify({}), 503

        character_info = response_utils.process_character(data)
        streaming = response_utils.get_streaming(data)

        deepseek_cfg = config.get("models", {}).get("deepseek", {})
        deepthink = response_utils.get_deepseek_deepthink(data) or deepseek_cfg.get("deepthink", False)
        search = response_utils.get_deepseek_search(data) or deepseek_cfg.get("search", False)
        text_file = deepseek_cfg.get("text_file", False)

        if not character_info:
            print("Error: Data could not be processed.")
            return jsonify({}), 503
        if not driver:
            print("Error: Selenium is not active.")
            return jsonify({}), 503

        last_response += 1
        current_message = last_response

        show_message(f"\n[color:purple]GENERATING RESPONSE {current_message}:")
        show_message("[color:white]- [color:green]Character data has been received.")
        
        return deepseek_response(current_message, character_info, streaming, deepthink, search, text_file)
    except Exception as e:
        print(f"Error receiving JSON from Sillytavern: {e}")
        return jsonify({}), 500

def deepseek_response(current_id: int, character_info: dict, streaming: bool, deepthink: bool, search: bool, text_file: bool) -> Response:
    global driver, last_response

    def client_disconnected() -> bool:
        if not streaming:
            disconnect_checker = request.environ.get('waitress.client_disconnected')
            return disconnect_checker and disconnect_checker()
        return False
    
    def interrupted() -> bool:
        return current_id != last_response or driver is None or client_disconnected()

    def safe_interrupt_response() -> Response:
        deepseek.new_chat(driver)
        return response_utils.create_response("", streaming)

    def has_incomplete_preserved_tags(text: str) -> bool:
        """Check if text contains incomplete preserved tags that should be buffered"""
        if not text:
            return False
            
        preserve_tags = deepseek.get_preserve_tags_from_config()
        if not preserve_tags:
            return False
            
        for tag in preserve_tags:
            # Check for incomplete opening tags: <tag or <tag>...content without closing
            incomplete_opening = rf'<{re.escape(tag)}(?!\w)(?:>(?:(?!</{re.escape(tag)}(?!\w)>).)*)?$'
            if re.search(incomplete_opening, text, re.DOTALL):
                return True
                
            # Check for incomplete closing tags: </tag or </ta
            incomplete_closing = rf'</{re.escape(tag)[:i]}$' 
            for i in range(1, len(tag) + 1):
                if text.endswith(f'</{tag[:i]}'):
                    return True
                    
        return False

    def extract_complete_content(text: str) -> tuple[str, str]:
        """
        Extract complete content that can be safely sent, and buffer incomplete tags.
        Returns (safe_content, buffered_content)
        """
        if not text:
            return "", ""
            
        preserve_tags = deepseek.get_preserve_tags_from_config()
        if not preserve_tags:
            return text, ""
            
        # Find the last safe position to cut the text
        # We need to ensure we don't cut in the middle of a preserved tag
        
        safe_pos = len(text)
        
        for tag in preserve_tags:
            # Look for incomplete patterns near the end
            
            # Pattern 1: Text ending with incomplete opening tag like "<test" or "<test>"
            incomplete_opening_match = re.search(rf'<{re.escape(tag)}(?!\w)(?:>(?:(?!</{re.escape(tag)}(?!\w)>).)*)?$', text, re.DOTALL)
            if incomplete_opening_match:
                safe_pos = min(safe_pos, incomplete_opening_match.start())
                
            # Pattern 2: Text ending with incomplete closing tag like "</" or "</test"
            for i in range(1, len(tag) + 2):  # +2 to include "</" case
                if i == 1 and text.endswith('</'):
                    safe_pos = min(safe_pos, len(text) - 2)
                elif i <= len(tag) and text.endswith(f'</{tag[:i]}'):
                    safe_pos = min(safe_pos, len(text) - len(f'</{tag[:i]}'))
                    
            # Pattern 3: Complete opening tag but content might be incomplete
            # Look for <tag>...content without matching </tag>
            tag_pattern = rf'<{re.escape(tag)}(?!\w)>((?:(?!</{re.escape(tag)}(?!\w)>).)*?)$'
            incomplete_content_match = re.search(tag_pattern, text, re.DOTALL)
            if incomplete_content_match:
                # Check if this might be an incomplete tag (no closing tag found)
                remaining_text = text[incomplete_content_match.start():]
                if f'</{tag}>' not in remaining_text:
                    safe_pos = min(safe_pos, incomplete_content_match.start())
        
        if safe_pos < len(text):
            return text[:safe_pos], text[safe_pos:]
        else:
            return text, ""

    try:
        if not selenium.current_page(driver, "https://chat.deepseek.com"):
            show_message("[color:white]- [color:red]You must be on the DeepSeek website.")
            return response_utils.create_response("You must be on the DeepSeek website.", streaming)

        if selenium.current_page(driver, "https://chat.deepseek.com/sign_in"):
            show_message("[color:white]- [color:red]You must be logged into DeepSeek.")
            return response_utils.create_response("You must be logged into DeepSeek.", streaming)

        if interrupted():
            return safe_interrupt_response()

        deepseek.configure_chat(driver, deepthink, search)
        show_message("[color:white]- [color:cyan]Chat reset and configured.")

        if interrupted():
            return safe_interrupt_response()

        if not deepseek.send_chat_message(driver, character_info, text_file):
            show_message("[color:white]- [color:red]Could not paste prompt.")
            return response_utils.create_response("Could not paste prompt.", streaming)

        show_message("[color:white]- [color:green]Prompt pasted and sent.")

        if interrupted():
            return safe_interrupt_response()

        if not deepseek.active_generate_response(driver):
            show_message("[color:white]- [color:red]No response generated.")
            return response_utils.create_response("No response generated.", streaming)

        if interrupted():
            return safe_interrupt_response()

        show_message("[color:white]- [color:cyan]Awaiting response.")
        initial_text = ""
        last_text = ""
        content_buffer = ""  # Buffer for incomplete tags

        if streaming:
            def streaming_response() -> Generator[str, None, None]:
                nonlocal initial_text, last_text, content_buffer
                try:
                    while deepseek.is_response_generating(driver):
                        if interrupted():
                            break

                        new_text = deepseek.get_last_message(driver)
                        if new_text and not initial_text:
                            initial_text = new_text
                        
                        if new_text and new_text != last_text and new_text.startswith(initial_text):
                            # Calculate the new content that arrived
                            full_diff = new_text[len(last_text):]
                            
                            # Add new content to buffer
                            buffered_content = content_buffer + full_diff
                            
                            # Extract what we can safely send vs what to keep buffered
                            safe_content, remaining_buffer = extract_complete_content(buffered_content)
                            
                            # Update states
                            last_text = new_text
                            content_buffer = remaining_buffer
                            
                            # Send the safe content if any
                            if safe_content:
                                yield response_utils.create_response_streaming(safe_content)
                        
                        time.sleep(0.2)

                    if interrupted():
                        return safe_interrupt_response()

                    # Final processing - get the complete response and send any remaining buffered content
                    final_text = deepseek.wait_for_response_completion(driver)
                    
                    if final_text:
                        # Calculate any final content that wasn't captured during streaming
                        if final_text != last_text:
                            final_diff = final_text[len(last_text):] if final_text.startswith(last_text) else final_text
                            final_content = content_buffer + final_diff
                        else:
                            final_content = content_buffer
                        
                        # Send any remaining content (should be complete now)
                        if final_content:
                            yield response_utils.create_response_streaming(final_content)
                    
                    # Send closing symbol if needed
                    closing = deepseek.get_closing_symbol(final_text) if final_text else ""
                    if closing:
                        yield response_utils.create_response_streaming(closing)
                    
                    show_message("[color:white]- [color:green]Completed.")
                except GeneratorExit:
                    deepseek.new_chat(driver)
                
                except Exception as e:
                    deepseek.new_chat(driver)
                    print(f"Streaming error: {e}")
                    show_message("[color:white]- [color:red]Unknown error occurred.")
                    yield response_utils.create_response_streaming("Error receiving response.")
            return Response(streaming_response(), content_type="text/event-stream")
        else:
            final_text = deepseek.wait_for_response_completion(driver)
            
            if interrupted():
                return safe_interrupt_response()
            
            response = (final_text + deepseek.get_closing_symbol(final_text)) if final_text else "Error receiving response."
            show_message("[color:white]- [color:green]Completed.")
            return response_utils.create_response_jsonify(response)
    
    except Exception as e:
        print(f"Error generating response: {e}")
        show_message("[color:white]- [color:red]Unknown error occurred.")
        return response_utils.create_response("Error receiving response.", streaming)

# =============================================================================================================================
# Selenium Actions
# =============================================================================================================================

def run_services() -> None:
    global driver, config, last_driver, last_response
    try:
        last_response = 0
        last_driver += 1
        close_selenium()

        driver = selenium.initialize_webdriver(config.get("browser"), "https://chat.deepseek.com/sign_in")
        
        if driver:
            threading.Thread(target=monitor_driver, daemon=True).start()

            ds_config = config.get("models", {}).get("deepseek", {})
            if ds_config.get("auto_login"):
                deepseek.login(driver, ds_config.get("email"), ds_config.get("password"))

            clear_messages()
            show_message("[color:red]API IS NOW ACTIVE!")
            show_message("[color:cyan]WELCOME TO INTENSE RP API")
            show_message("[color:yellow]URL 1: [color:white]http://127.0.0.1:5000/")

            if config.get("show_ip"):
                ip = socket.gethostbyname(socket.gethostname())
                show_message(f"[color:yellow]URL 2: [color:white]http://{ip}:5000/")

            serve(app, host="0.0.0.0", port=5000, channel_request_lookahead=1)
        else:
            clear_messages()
            show_message("[color:red]Selenium failed to start.")
    except Exception as e:
        print(f"Error starting Selenium: {e}")

def monitor_driver() -> None:
    global driver, last_driver
    current = last_driver
    print("Starting browser detection.")
    while current == last_driver:
        if driver and not selenium.is_browser_open(driver):
            clear_messages()
            show_message("[color:red]Browser connection lost!")
            driver = None
            break
        time.sleep(2)

def close_selenium() -> None:
    global driver
    try:
        if driver:
            driver.quit()
            driver = None
    except Exception:
        pass

# =============================================================================================================================
# Textbox Actions
# =============================================================================================================================

def show_message(text: str) -> None:
    global textbox, logging_manager
    try:
        textbox.colored_add(text)
        
        # Log the message if logging is enabled
        if logging_manager:
            logging_manager.log_message(text)
            
    except Exception as e:
        print(f"Error showing message: {e}")

def clear_messages() -> None:
    global textbox
    try:
        textbox.clear()
    except Exception as e:
        print(f"Error clearing messages: {e}")