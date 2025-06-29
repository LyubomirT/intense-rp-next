from flask import Flask, jsonify, request, Response
import utils.response_utils as response_utils
import utils.webdriver_utils as selenium
import utils.deepseek_driver as deepseek
import socket, time, threading
from typing import Generator
from waitress import serve
from core import get_state_manager, StateEvent

app = Flask(__name__)

@app.route("/models", methods=["GET"])
def model() -> Response:
    state = get_state_manager()
    
    if not state.driver:
        return jsonify({}), 503

    state.show_message("\n[color:purple]API CONNECTION:")
    try:
        state.show_message("[color:white]- [color:green]Successful connection.")
        return response_utils.get_model()
    except Exception as e:
        state.show_message("[color:white]- [color:red]Error connecting.")
        print(f"Error connecting to API: {e}")
        return jsonify({}), 500

@app.route("/chat/completions", methods=["POST"])
def bot_response() -> Response:
    state = get_state_manager()
    
    try:
        data = request.get_json()
        if not data:
            print("Error: Empty data was received.")
            return jsonify({}), 503

        character_info = response_utils.process_character(data)
        streaming = response_utils.get_streaming(data)

        config = state.config
        deepseek_cfg = config.get("models", {}).get("deepseek", {})
        deepthink = response_utils.get_deepseek_deepthink(data) or deepseek_cfg.get("deepthink", False)
        search = response_utils.get_deepseek_search(data) or deepseek_cfg.get("search", False)
        text_file = deepseek_cfg.get("text_file", False)

        if not character_info:
            print("Error: Data could not be processed.")
            return jsonify({}), 503
        if not state.driver:
            print("Error: Selenium is not active.")
            return jsonify({}), 503

        current_message = state.increment_response_id()

        state.show_message(f"\n[color:purple]GENERATING RESPONSE {current_message}:")
        state.show_message("[color:white]- [color:green]Character data has been received.")
        
        return deepseek_response(current_message, character_info, streaming, deepthink, search, text_file)
    except Exception as e:
        print(f"Error receiving JSON from Sillytavern: {e}")
        return jsonify({}), 500

def deepseek_response(current_id: int, character_info: dict, streaming: bool, deepthink: bool, search: bool, text_file: bool) -> Response:
    state = get_state_manager()

    def client_disconnected() -> bool:
        if not streaming:
            disconnect_checker = request.environ.get('waitress.client_disconnected')
            return disconnect_checker and disconnect_checker()
        return False
    
    def interrupted() -> bool:
        return current_id != state.last_response or state.driver is None or client_disconnected()

    def safe_interrupt_response() -> Response:
        deepseek.new_chat(state.driver)
        return response_utils.create_response("", streaming)

    try:
        if not selenium.current_page(state.driver, "https://chat.deepseek.com"):
            state.show_message("[color:white]- [color:red]You must be on the DeepSeek website.")
            return response_utils.create_response("You must be on the DeepSeek website.", streaming)

        if selenium.current_page(state.driver, "https://chat.deepseek.com/sign_in"):
            state.show_message("[color:white]- [color:red]You must be logged into DeepSeek.")
            return response_utils.create_response("You must be logged into DeepSeek.", streaming)

        if interrupted():
            return safe_interrupt_response()

        deepseek.configure_chat(state.driver, deepthink, search)
        state.show_message("[color:white]- [color:cyan]Chat reset and configured.")

        if interrupted():
            return safe_interrupt_response()

        if not deepseek.send_chat_message(state.driver, character_info, text_file):
            state.show_message("[color:white]- [color:red]Could not paste prompt.")
            return response_utils.create_response("Could not paste prompt.", streaming)

        state.show_message("[color:white]- [color:green]Prompt pasted and sent.")

        if interrupted():
            return safe_interrupt_response()

        if not deepseek.active_generate_response(state.driver):
            state.show_message("[color:white]- [color:red]No response generated.")
            return response_utils.create_response("No response generated.", streaming)

        if interrupted():
            return safe_interrupt_response()

        state.show_message("[color:white]- [color:cyan]Awaiting response.")
        initial_text = ""
        last_text = ""

        if streaming:
            def streaming_response() -> Generator[str, None, None]:
                nonlocal initial_text, last_text
                try:
                    while deepseek.is_response_generating(state.driver):
                        if interrupted():
                            break

                        new_text = deepseek.get_last_message(state.driver)
                        if new_text and not initial_text:
                            initial_text = new_text
                        
                        if new_text and new_text != last_text and new_text.startswith(initial_text):
                            diff = new_text[len(last_text):]
                            last_text = new_text
                            yield response_utils.create_response_streaming(diff)
                        
                        time.sleep(0.2)

                    if interrupted():
                        return safe_interrupt_response()

                    # Final processing - get the complete response
                    final_text = deepseek.wait_for_response_completion(state.driver)
                    
                    if final_text:
                        # Send any remaining content
                        if final_text != last_text:
                            final_diff = final_text[len(last_text):] if final_text.startswith(last_text) else final_text
                            if final_diff:
                                yield response_utils.create_response_streaming(final_diff)
                    
                    # Send closing symbol if needed
                    closing = deepseek.get_closing_symbol(final_text) if final_text else ""
                    if closing:
                        yield response_utils.create_response_streaming(closing)
                    
                    state.show_message("[color:white]- [color:green]Completed.")
                except GeneratorExit:
                    deepseek.new_chat(state.driver)
                
                except Exception as e:
                    deepseek.new_chat(state.driver)
                    print(f"Streaming error: {e}")
                    state.show_message("[color:white]- [color:red]Unknown error occurred.")
                    yield response_utils.create_response_streaming("Error receiving response.")
            return Response(streaming_response(), content_type="text/event-stream")
        else:
            final_text = deepseek.wait_for_response_completion(state.driver)
            
            if interrupted():
                return safe_interrupt_response()
            
            response = (final_text + deepseek.get_closing_symbol(final_text)) if final_text else "Error receiving response."
            state.show_message("[color:white]- [color:green]Completed.")
            return response_utils.create_response_jsonify(response)
    
    except Exception as e:
        print(f"Error generating response: {e}")
        state.show_message("[color:white]- [color:red]Unknown error occurred.")
        return response_utils.create_response("Error receiving response.", streaming)

# =============================================================================================================================
# Selenium Actions
# =============================================================================================================================

def run_services() -> None:
    state = get_state_manager()
    
    try:
        state.last_response = 0
        current_driver_id = state.increment_driver_id()
        close_selenium()

        config = state.config
        state.driver = selenium.initialize_webdriver(config.get("browser"), "https://chat.deepseek.com/sign_in")
        
        if state.driver:
            threading.Thread(target=monitor_driver, args=(current_driver_id,), daemon=True).start()

            ds_config = config.get("models", {}).get("deepseek", {})
            if ds_config.get("auto_login"):
                deepseek.login(state.driver, ds_config.get("email"), ds_config.get("password"))

            state.clear_messages()
            state.show_message("[color:red]API IS NOW ACTIVE!")
            state.show_message("[color:cyan]WELCOME TO INTENSE RP API")
            state.show_message("[color:yellow]URL 1: [color:white]http://127.0.0.1:5000/")

            if config.get("show_ip"):
                ip = socket.gethostbyname(socket.gethostname())
                state.show_message(f"[color:yellow]URL 2: [color:white]http://{ip}:5000/")

            state.is_running = True
            serve(app, host="0.0.0.0", port=5000, channel_request_lookahead=1)
        else:
            state.clear_messages()
            state.show_message("[color:red]Selenium failed to start.")
    except Exception as e:
        print(f"Error starting Selenium: {e}")
    finally:
        state.is_running = False

def monitor_driver(driver_id: int) -> None:
    state = get_state_manager()
    print("Starting browser detection.")
    
    while driver_id == state.last_driver:
        if state.driver and not selenium.is_browser_open(state.driver):
            state.clear_messages()
            state.show_message("[color:red]Browser connection lost!")
            state.driver = None
            break
        time.sleep(2)

def close_selenium() -> None:
    state = get_state_manager()
    try:
        if state.driver:
            state.driver.quit()
            state.driver = None
    except Exception:
        pass